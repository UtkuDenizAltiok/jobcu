"""Lost paid answers cannot silently turn into repeated paid attempts."""

import httpx
import pytest

from jobcu.ai.base import AIConnectionError, ProviderAdapter, RawReply, ResearchReply, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.usage import UsageLog
from jobcu.settings import Settings


class Adapter(ProviderAdapter):
    can_search_the_web = True

    def __init__(self, failure):
        super().__init__("fictional-key")
        self.failure, self.calls = failure, []

    def complete_json(self, **request):
        self.calls.append("structured")
        return RawReply('{"ok":true}', Usage(10, 3))

    def research(self, **request):
        self.calls.append("research")
        if len(self.calls) == 1:
            raise self.failure
        return ResearchReply("Complete fictional notes", [], Usage(10, 3, web_searches=1))

    def list_models(self):
        return []


def configured():
    value = Settings()
    value.ai.provider, value.ai.model = "gemini", "fictional-model"
    value.limits.monthly_cost_limit = value.limits.monthly_token_limit = None
    return value


def test_uncertain_execution_stops_repeat_and_later_dispatches_on_that_path():
    failure = AIConnectionError("The answer was lost")
    failure.request_sent = True
    adapter = Adapter(failure)
    ledger, waits, notices = UsageLog(), [], []
    client = AIClient(configured(), adapter=adapter, usage_log=ledger,
                      sleep=waits.append, notify=notices.append)
    for question in ("First fictional city", "Another fictional city"):
        with pytest.raises(AIConnectionError):
            client.research(step="location", system="City facts", prompt=question)
    assert adapter.calls == ["research"] and waits == []
    assert ledger.this_month()[0].usage.unreported_requests == 1
    assert client._web_searches_reserved == 0
    # A separate structured path is still usable; explicit later recovery gets a fresh client.
    from pydantic import BaseModel

    class Answer(BaseModel):
        ok: bool

    assert client.generate(Answer, step="scoring", system="Fictional", prompt="Fictional").ok
    resumed = AIClient(configured(), adapter=adapter, usage_log=ledger)
    assert resumed.research(step="location", system="City facts", prompt="First fictional city")
    assert any("may already have charged" in note for note in notices)
    assert not any("exhausted" in note for note in notices)  # no automatic retry was attempted


def test_proven_connection_setup_failure_can_retry_without_inventing_a_charge():
    failure = AIConnectionError("Fictional DNS failure")
    failure.request_sent = False
    adapter = Adapter(failure)
    ledger, waits = UsageLog(), []
    client = AIClient(configured(), adapter=adapter, usage_log=ledger, sleep=waits.append)
    assert client.research(step="location", system="City facts", prompt="Fictional city")
    assert adapter.calls == ["research", "research"] and len(waits) == 1
    assert ledger.this_month()[0].usage.unreported_requests == 0


@pytest.mark.parametrize("provider", ["gemini", "openai", "anthropic"])
@pytest.mark.parametrize("kind,sent", [(httpx.ConnectError, False), (httpx.ConnectTimeout, False),
                                      (httpx.ReadTimeout, True), (httpx.RemoteProtocolError, True)])
def test_adapters_preserve_whether_a_failed_request_could_have_reached_the_provider(
        provider, kind, sent):
    request = httpx.Request("POST", "https://example.test/generate")
    cause = kind("Fictional interruption", request=request)
    if provider == "gemini":
        from jobcu.ai.gemini_adapter import _translate
        failure = cause
    elif provider == "openai":
        import openai

        from jobcu.ai.openai_adapter import translate_openai_error as _translate
        failure = openai.APIConnectionError(request=request)
    else:
        import anthropic

        from jobcu.ai.anthropic_adapter import _translate
        failure = anthropic.APIConnectionError(request=request)
    if failure is not cause:
        failure.__cause__ = cause
    translated = _translate(failure)
    assert isinstance(translated, AIConnectionError) and translated.request_sent is sent


@pytest.mark.parametrize("kind,sent", [(httpx.ConnectError, False), (httpx.ReadError, True)])
def test_socket_cause_does_not_erase_httpx_dispatch_classification(kind, sent):
    from jobcu.ai.base import connection_problem

    cause = kind("Fictional transport failure")
    cause.__cause__ = OSError("Fictional socket failure")
    wrapper = RuntimeError("Fictional SDK wrapper")
    wrapper.__cause__ = cause
    assert connection_problem(wrapper).request_sent is sent
