"""Fictional failures must not become repeated charges or misleading complete estimates."""

import threading

import pytest
from google.genai import errors
from pydantic import BaseModel

from jobcu.ai.base import (
    AIAuthError,
    AIConnectionError,
    AILimitReached,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIUnavailable,
    AIUsageUncertain,
    ProviderAdapter,
    RawReply,
    ResearchReply,
    Usage,
)
from jobcu.ai.client import AIClient, in_parallel
from jobcu.ai.gemini_adapter import _translate
from jobcu.ai.usage import UsageLog, estimate_cost
from jobcu.countries import COUNTRIES
from jobcu.settings import ModelPrice, Settings

GOOD = '{"ok": true, "word": "fictional"}'


class ScriptedAdapter(ProviderAdapter):
    def __init__(self, *script):
        super().__init__("fictional-key")
        self.script, self.calls = list(script), []

    def complete_json(self, **request):
        self.calls.append(request)
        reply = self.script.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return RawReply(reply, Usage(10, 5))

    def list_models(self):
        return []


class Answer(BaseModel):
    ok: bool
    word: str


class Stopped(Exception):
    pass


def settings():
    value = Settings()
    value.ai.provider, value.ai.model = "gemini", "fictional-model"
    return value


def ask(client):
    return client.generate(Answer, step="scoring", system="Use stated evidence only",
                           prompt="Fictional applicant and job")


@pytest.mark.parametrize("research", [False, True])
@pytest.mark.parametrize("code,message", [
    (402, "Prepayment credits depleted"),
    (429, "Your prepayment credits are depleted"),
])
def test_depleted_credit_is_not_temporary_throttling(research, code, message):
    error = errors.ClientError(code, {"error": {
        "code": code, "status": "RESOURCE_EXHAUSTED", "message": message}})
    translated = _translate(error, web_search=research)
    assert isinstance(translated, AIQuotaExhausted)
    assert "credit" in translated.message.lower()


@pytest.mark.parametrize("research", [False, True])
@pytest.mark.parametrize("code,message", [
    (403, "Monthly spend cap exceeded"),
    (429, "Google Search service paused after reaching the monthly cap."),
])
def test_explicit_monthly_cap_is_terminal_before_search_or_rate_limit_fallback(
        research, code, message):
    error = errors.ClientError(code, {"error": {
        "code": code, "status": "PERMISSION_DENIED", "message": message}})
    translated = _translate(error, web_search=research)
    assert isinstance(translated, AIQuotaExhausted)
    assert "spending cap" in translated.message and not translated.retryable
    adapter = ScriptedAdapter(translated, GOOD)
    client = AIClient(settings(), adapter=adapter, patient=True,
                      sleep=lambda seconds: pytest.fail("A cap must not cause a retry wait"))
    for _ in range(2):
        with pytest.raises(AIQuotaExhausted):
            ask(client)
    assert len(adapter.calls) == 1


@pytest.mark.parametrize("message", ["Permission denied for this key.",
                                      "Monthly spend cap has not been reached."])
def test_ambiguous_permission_refusal_does_not_claim_a_billing_cause(message):
    error = errors.ClientError(403, {"error": {
        "code": 403, "status": "PERMISSION_DENIED", "message": message}})
    translated = _translate(error, web_search=True)
    assert isinstance(translated, AIAuthError)
    assert "permissions" in translated.message and "billing" in translated.message
    assert "does not identify" in translated.message


@pytest.mark.parametrize("failure", [AIRateLimited("busy"), AIUnavailable("offline")])
def test_stop_interrupts_retry_wait_without_sending_another_request(failure):
    stopped = False
    waits = []
    progress = []

    def checkpoint():
        if stopped:
            raise Stopped

    def sleep(seconds):
        nonlocal stopped
        waits.append(seconds)
        stopped = True

    adapter = ScriptedAdapter(failure, GOOD)
    client = AIClient(settings(), adapter=adapter, checkpoint=checkpoint, sleep=sleep,
                      on_wait=progress.append)
    with pytest.raises(Stopped):
        ask(client)
    assert len(adapter.calls) == 1
    assert waits and max(waits) <= 1
    assert progress[0] >= 1 and progress[-1] == 0


def test_waiting_for_a_request_slot_checks_stop():
    stopped, waiting = threading.Event(), threading.Event()

    def checkpoint():
        if stopped.is_set():
            raise Stopped
        waiting.set()

    adapter = ScriptedAdapter(GOOD)
    client = AIClient(settings(), adapter=adapter, checkpoint=checkpoint)
    client._requests_running = client.parallel_requests
    failures = []

    def run():
        try:
            ask(client)
        except Stopped:
            failures.append("stopped")

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    assert waiting.wait(2)
    stopped.set()
    worker.join(2)
    assert not worker.is_alive() and failures == ["stopped"]
    assert not adapter.calls


def test_definite_account_refusal_blocks_later_dispatch_even_when_a_step_catches_it():
    adapter = ScriptedAdapter(AIQuotaExhausted("Credits depleted"), GOOD)
    notices = []
    client = AIClient(settings(), adapter=adapter, notify=notices.append)
    for _ in range(2):
        with pytest.raises(AIQuotaExhausted):
            ask(client)
    assert len(adapter.calls) == 1
    assert notices == ["Credits depleted"]


def test_reopened_client_keeps_the_same_searchs_reported_web_allowance():
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            pytest.fail("A completed search's exhausted allowance must not reset")

    configured = settings()
    configured.limits.web_search_cap = 3
    ledger = UsageLog()
    ledger.record(search_id=71, step="employers", provider="gemini", model="fictional-model",
                  usage=Usage(web_searches=17))  # separate discovery allowance
    ledger.record(search_id=71, step="places", provider="gemini", model="fictional-model",
                  usage=Usage(web_searches=2))
    ledger.record(search_id=71, step="location", provider="openai", model="fictional-other",
                  usage=Usage(web_searches=1))
    resumed = AIClient(configured, adapter=Web(), usage_log=ledger, search_id=71)
    with pytest.raises(AILimitReached, match="allowance"):
        resumed.research(step="location", system="Fictional fact", prompt="Saved condition")
    fresh = AIClient(configured, adapter=Web(), usage_log=ledger, search_id=72)
    assert fresh.web_searches_left() == 3
    ledger.record(search_id=73, step="employers", provider="gemini", model="fictional-model",
                  usage=Usage(web_searches=17))
    discovery_only = AIClient(configured, adapter=Web(), usage_log=ledger, search_id=73)
    assert discovery_only.web_searches_left() == 3


def test_identical_exhausted_research_does_not_restart_but_independent_checks_can_run():
    class Disconnected(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], raw.usage)

    adapter = Disconnected(*[AIConnectionError("Interrupted") for _ in range(5)], GOOD, GOOD)
    notes, waits = [], []
    log = UsageLog()
    client = AIClient(settings(), adapter=adapter, usage_log=log, notify=notes.append,
                      sleep=waits.append)
    with pytest.raises(AIConnectionError):
        client.research(step="location", system="City service", prompt="Fictional cities")
    for step in ("employers", "job_places"):
        with pytest.raises(AIConnectionError, match="identical online check"):
            client.research(step=step, system="City service", prompt="Fictional cities")
    assert len(adapter.calls) == 5 and len(waits) == 4
    assert log.this_month()[0].usage.unreported_requests == 5
    assert sum("exhausted" in note for note in notes) == 1
    assert client._web_searches_reserved == 0
    assert client.research(step="employers", system="City service", prompt="Another city").text
    # Generation remains available: an online-research failure is not a scoring failure.
    assert ask(client).ok
    assert len(adapter.calls) == 7
    fresh = AIClient(settings(), adapter=Disconnected(GOOD))
    assert fresh.web_research_unavailable_reason() is None


def test_completed_usage_is_kept_before_stop_and_no_later_batch_runs():
    stopped = False
    log = UsageLog()

    class Completed(ScriptedAdapter):
        def complete_json(self, **request):
            nonlocal stopped
            reply = super().complete_json(**request)
            stopped = True
            return reply

    def checkpoint():
        if stopped:
            raise Stopped

    adapter = Completed(GOOD, GOOD)
    client = AIClient(settings(), adapter=adapter, checkpoint=checkpoint, usage_log=log)
    client.parallel_requests = 1
    with pytest.raises(Stopped):
        in_parallel(client, lambda item: ask(client), list(COUNTRIES))
    assert len(adapter.calls) == 1
    assert log.this_month()[0].usage.input_tokens == 10


def test_failed_attempt_usage_is_recorded_once_and_checks_monthly_limit_before_retry():
    failure = AIUnavailable("Stream interrupted")
    failure.usage = Usage(10, 30, reasoning_tokens=20, unreported_requests=1)
    adapter = ScriptedAdapter(failure, GOOD)
    limits = settings()
    limits.limits.monthly_token_limit = 35
    log = UsageLog()
    client = AIClient(limits, adapter=adapter, usage_log=log, sleep=lambda seconds: None)
    with pytest.raises(AILimitReached):
        ask(client)
    assert len(adapter.calls) == 1
    recorded = log.this_month()[0]
    assert recorded.usage == failure.usage
    prices = [ModelPrice(provider="gemini", model="fictional-model",
                         input_per_million=1, output_per_million=2)]
    cost, complete = estimate_cost([recorded], prices)
    assert cost == pytest.approx(70 / 1e6)
    assert not complete


def test_truncated_attempt_usage_survives_repair_without_double_counting():
    failure = AIOutputTruncated("Too long")
    failure.usage = Usage(20, 40, reasoning_tokens=30)
    adapter = ScriptedAdapter(failure, GOOD)
    log = UsageLog()
    client = AIClient(settings(), adapter=adapter, usage_log=log)
    assert ask(client).ok
    assert log.this_month()[0].usage == Usage(30, 45, reasoning_tokens=30)


def test_impatient_connection_probe_does_not_repeat_an_outage_request():
    adapter = ScriptedAdapter(AIUnavailable("offline"), GOOD)
    client = AIClient(settings(), adapter=adapter, patient=False,
                      sleep=lambda seconds: pytest.fail("Unexpected retry wait"))
    with pytest.raises(AIUnavailable):
        ask(client)
    assert len(adapter.calls) == 1


@pytest.mark.parametrize("profession", ["hardware engineer", "nurse", "teacher"])
@pytest.mark.parametrize("error_type", [AIUnavailable, AIRateLimited])
def test_observed_research_with_missing_failure_receipt_stops_automatic_paid_work(
        profession, error_type):
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], raw.usage)

    failure = error_type("Fictional service failure after research")
    failure.usage = Usage(10, 30, reasoning_tokens=20, web_searches=2, unreported_requests=1)
    adapter = Web(failure, GOOD)
    ledger, notices, waits = UsageLog(), [], []
    client = AIClient(settings(), adapter=adapter, usage_log=ledger, notify=notices.append,
                      sleep=waits.append)
    with pytest.raises(AIUsageUncertain) as first:
        client.research(step="location", system="Use sourced fictional evidence",
                        prompt=f"A fictional city for a {profession}")
    assert not first.value.retryable
    assert "usage" in first.value.message and "stopped" in first.value.message
    for prompt in (profession, "Another independent city"):
        with pytest.raises(type(first.value)):
            client.research(step="job_places", system="Fictional evidence", prompt=prompt)
    assert len(adapter.calls) == 1 and not waits
    assert ledger.this_month()[0].usage == failure.usage
    assert client.web_searches_used == 2 and client._web_searches_reserved == 0
    assert sum("stopped automatic" in note for note in notices) == 1
    # A paused research route must not pause ordinary structured matching.
    assert ask(client).ok and len(adapter.calls) == 2


@pytest.mark.parametrize("profession", ["hardware engineer", "nurse", "teacher"])
def test_when_paid_limits_only_tell_one_research_failure_never_stops_the_other_checks(
        profession):
    # 2026-11-06: one look-up failed after its searches, and every later online check of the
    # search (places, requirements, employer postings) was left unchecked, although the
    # person's paid limits only tell.
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], raw.usage)

    failure = AIUnavailable("Fictional service failure after research")
    failure.usage = Usage(10, 30, reasoning_tokens=20, web_searches=2, unreported_requests=1)
    adapter = Web(failure, GOOD, GOOD)
    configured = settings()
    configured.limits.paid_limits = "tell"
    ledger, notices, waits = UsageLog(), [], []
    client = AIClient(configured, adapter=adapter, usage_log=ledger, notify=notices.append,
                      sleep=waits.append)
    # The failed look-up is tried again like any outage, after a wait.
    assert client.research(step="employers", system="Use sourced fictional evidence",
                           prompt=f"Fictional employers for a {profession}").text
    assert len(adapter.calls) == 2 and len(waits) == 1
    # Later, independent look-ups still run.
    assert client.research(step="job_places", system="Fictional evidence",
                           prompt="Another fictional job").text
    assert len(adapter.calls) == 3
    # The failed attempt's searches count against the allowance; its missing bill is told.
    assert client.web_searches_used >= 2 and client._web_searches_reserved == 0
    month = ledger.this_month()[0].usage  # the failed attempt plus the two answers
    assert month.web_searches == 2 and month.unreported_requests == 1
    assert month.input_tokens == 10 + 2 * 10
    assert sum("did not report complete usage" in note for note in notices) == 1
    assert not any("stopped automatic research" in note for note in notices)


@pytest.mark.parametrize("provider,counted", [("gemini", 0), ("anthropic", 12)])
def test_a_failed_look_up_takes_nothing_from_the_search_where_the_provider_bills_nothing(
        provider, counted):
    # November 2026: a search lost about a quarter of its share of the free web searches to
    # look-ups Google had failed after 8 to 19 searches each; Google's billing report showed
    # none of them. Where nothing is measured, the searches seen still count.
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], Usage(10, 5, web_searches=2))

    failure = AIUnavailable("Fictional failure: the provider ended the request without usage")
    failure.usage = Usage(web_searches=12, unreported_requests=1)
    adapter = Web(failure, GOOD)
    configured = settings()
    configured.ai.provider = provider
    configured.limits.paid_limits = "tell"
    ledger = UsageLog()
    client = AIClient(configured, adapter=adapter, usage_log=ledger, sleep=lambda seconds: None,
                      free_web_search_share=20)
    assert client.research(step="job_places", system="Fictional evidence",
                           prompt="A fictional job").text
    assert client.web_searches_used == counted + 2 and client._web_searches_reserved == 0
    assert client.web_searches_left() == 20 - counted - 2
    # The ledger keeps what was seen either way; only the count against the month differs.
    assert ledger.this_month()[0].usage.web_searches == 14
    assert ledger.web_searches_this_month(provider) == counted + 2


@pytest.mark.parametrize("provider,pauses", [("gemini", False), ("anthropic", True)])
def test_with_limits_that_stop_a_look_up_the_provider_failed_for_free_is_only_an_outage(
        provider, pauses):
    # November 2026: Google failed 2 of 21 look-up requests of one search after their searches
    # and billed nothing for them. With limits that stop, one such failure still left every
    # later place, requirement and posting of the search unchecked. Where nothing is measured,
    # the failure's bill is unknown and the pause stays.
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], Usage(10, 5, web_searches=2))

    failure = AIUnavailable("Fictional failure: the provider ended the request without usage")
    failure.usage = Usage(web_searches=12, unreported_requests=1)
    adapter = Web(failure, GOOD, GOOD)
    configured = settings()
    configured.ai.provider = provider
    assert configured.limits.paid_limits == "stop"
    ledger, notices, waits = UsageLog(), [], []
    client = AIClient(configured, adapter=adapter, usage_log=ledger, notify=notices.append,
                      sleep=waits.append)

    def look_up(prompt):
        return client.research(step="job_places", system="Fictional evidence", prompt=prompt)

    if pauses:
        with pytest.raises(AIUsageUncertain):
            look_up("A fictional job")
        with pytest.raises(AIUsageUncertain):
            look_up("Another fictional job")
        assert len(adapter.calls) == 1 and not waits
        assert sum("stopped automatic research" in note for note in notices) == 1
    else:
        # Tried again after a wait, like any outage, and later look-ups still run.
        assert look_up("A fictional job").text and look_up("Another fictional job").text
        assert len(adapter.calls) == 3 and len(waits) == 1
        assert not any("stopped automatic research" in note for note in notices)
        assert client.web_searches_used == 4
    # What was seen stays on record either way.
    assert ledger.this_month()[0].usage.web_searches == 12 + 2 * (not pauses) * 2
    assert client._web_searches_reserved == 0


@pytest.mark.parametrize("usage", [Usage(unreported_requests=1),
                                   Usage(10, 30, web_searches=2)])
def test_early_failure_or_complete_research_receipt_keeps_bounded_transient_recovery(usage):
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], raw.usage)

    failure = AIUnavailable("Fictional temporary service error")
    failure.usage = usage
    adapter, waits, ledger = Web(failure, GOOD), [], UsageLog()
    client = AIClient(settings(), adapter=adapter, usage_log=ledger, sleep=waits.append)
    assert client.research(step="location", system="Fictional evidence", prompt="Town").text
    assert len(adapter.calls) == 2 and len(waits) == 1
    assert ledger.this_month()[0].usage == usage + Usage(10, 5)


def test_retry_progress_identifies_attempts_and_the_existing_bound():
    progress = []
    adapter = ScriptedAdapter(AIConnectionError("Interrupted"),
                              AIConnectionError("Interrupted again"), GOOD)
    client = AIClient(settings(), adapter=adapter, sleep=lambda seconds: None,
                      on_progress=progress.append)
    assert ask(client).ok
    assert len(adapter.calls) == 3
    assert any("retry 1 of 4" in message for message in progress)
    assert any("retry 2 of 4" in message for message in progress)
    assert progress[-1] == "Retrying an AI request (2 of 4)"


def test_search_stop_reaches_the_ai_wait_during_document_understanding(monkeypatch):
    from jobcu import db, search
    from jobcu.settings import SearchForm

    adapter = ScriptedAdapter(AIUnavailable("Fictional outage"), GOOD)
    manager = search.SearchManager()
    stopped = threading.Event()
    monkeypatch.setattr(search, "load_settings", settings)
    monkeypatch.setattr(search.documents, "read_text",
                        lambda kind: "Fictional nurse with stated registration and experience.")

    def sleep(seconds):
        assert seconds <= 1
        assert manager.stop(manager.current.id)
        stopped.set()

    def make(*args, **kwargs):
        return AIClient(*args, **kwargs, adapter=adapter, sleep=sleep)

    monkeypatch.setattr(search, "AIClient", make)
    run = manager.start(SearchForm(location_text="Germany"))
    assert stopped.wait(2)
    # The manager's state is published after SQLite commits the stopped attempt.
    deadline = threading.Event()
    for _ in range(100):
        if run.status != "running":
            break
        deadline.wait(0.01)
    assert run.status == "stopped" and len(adapter.calls) == 1
    assert run.error is None
    with db.connect() as conn:
        assert conn.execute("SELECT status FROM searches WHERE id=?", (run.id,)).fetchone()[0] == (
            "stopped")
    assert UsageLog().for_search(run.id)["profile"].unreported_requests == 1


def test_every_research_request_carries_its_web_search_budget_and_overspending_is_logged(caplog):
    # Search 19 (2026-11-06): Gemini's search tool has no cap, and Gemini ran 4 to 10 searches a
    # job where 2 were allowed. The budget is now said in every research request.
    class Web(ScriptedAdapter):
        can_search_the_web = True

        def research(self, **request):
            raw = self.complete_json(**request)
            return ResearchReply(raw.text, [], Usage(10, 5, web_searches=7))

    adapter = Web(GOOD)
    client = AIClient(settings(), adapter=adapter, usage_log=UsageLog())
    with caplog.at_level("INFO", logger="jobcu.ai.client"):
        client.research(step="job_places", system="Find fictional workplaces",
                        prompt="Five fictional jobs", max_searches=4)
    sent = adapter.calls[0]
    assert sent["max_searches"] == 4
    assert sent["system"].startswith("Find fictional workplaces")
    assert "at most 4 search queries in total" in sent["system"]
    assert "used=7 allowed=4 search_steps=0" in caplog.text  # this provider reports no steps
