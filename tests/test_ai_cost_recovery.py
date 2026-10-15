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
