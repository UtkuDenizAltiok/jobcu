"""One generation survives retrieval failures; its bill and temporary record stay tracked."""

import json

import httpx
import pytest
from google import genai
from google.genai import types
from pydantic import BaseModel

from jobcu import db
from jobcu.ai import request_recovery
from jobcu.ai.base import AIConnectionError, AILimitReached, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.gemini_adapter import GeminiAdapter
from jobcu.ai.request_recovery import RecoveryContext
from jobcu.ai.usage import UsageLog
from jobcu.settings import Settings


class Answer(BaseModel):
    ok: bool


def operation(identifier="fictional-1", status="completed", *, research=False, tokens=100):
    steps = [{"type": "model_output", "content": [{"type": "text", "text": '{"ok":true}'}]}]
    if research:
        steps.insert(0, {"type": "google_search_call",
                         "arguments": {"queries": ["fictional vacancy"]}})
    return {"id": identifier, "status": status, "steps": steps if status == "completed" else [],
            "usage": {"total_input_tokens": tokens, "total_output_tokens": 30,
                      "total_thought_tokens": 50, "total_cached_tokens": 0}}


@pytest.fixture
def service():
    clients = []

    def make(handler, *, checkpoint=None, settings=None):
        calls, waits, notices = [], [], []
        adapter = GeminiAdapter("fictional-key")

        def handle(request):
            body = json.loads(request.content) if request.content else None
            calls.append((request.method, request.url.path, body))
            return handler(request, calls)

        sdk = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            client_args={"transport": httpx.MockTransport(handle)}))
        adapter._genai_client = sdk
        clients.append(sdk)
        configured = settings or Settings()
        configured.ai.provider, configured.ai.model = "gemini", "gemini-3.8-flash"
        configured.ai.recover_interrupted_requests = True
        client = AIClient(configured, adapter=adapter, usage_log=UsageLog(), search_id=1,
                          checkpoint=checkpoint, sleep=waits.append, notify=notices.append)
        return client, adapter, calls, waits, notices

    yield make
    for client in clients:
        client.close()


def ask(client, prompt="Fictional applicant"):
    return client.generate(Answer, step="scoring", system="Use only fictional evidence",
                           prompt=prompt)


@pytest.mark.parametrize("profession", ["electronics engineer", "community nurse", "teacher"])
@pytest.mark.parametrize("research", [False, True])
def test_dropped_retrieval_keeps_same_generation_and_complete_bill(service, profession, research):
    def handler(request, calls):
        if request.method == "POST":
            return httpx.Response(200, json={"id": "fictional-1", "status": "in_progress"})
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        if sum(method == "GET" for method, _, _ in calls) == 1:
            raise httpx.ReadError("Fictional dropped retrieval", request=request)
        return httpx.Response(200, json=operation(research=research))

    client, _, calls, waits, _ = service(handler)
    if research:
        reply = client.research(step="job_places", system="Read fictional ad", prompt=profession)
        assert reply.usage == Usage(100, 80, 0, 50, 1)
    else:
        assert ask(client, profession).ok
    assert [method for method, _, _ in calls] == ["POST", "GET", "GET", "DELETE"]
    body = calls[0][2]
    assert body["store"] is body["background"] is True and body["stream"] is False
    assert body["generation_config"]["thinking_level"] == "medium"
    assert all(path.endswith("/fictional-1") for _, path, _ in calls[1:])
    assert waits and not request_recovery.pending(force=True)
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM ai_usage").fetchall()
    assert len(rows) == 1 and rows[0]["unreported_requests"] == 0
    assert rows[0]["input_tokens"] == 100 and rows[0]["output_tokens"] == 80


def test_lost_initial_post_is_not_recreated_without_an_operation_id(service):
    def handler(request, calls):
        raise httpx.ReadError("Fictional loss before operation ID", request=request)

    client, _, calls, _, _ = service(handler)
    for _ in range(2):
        with pytest.raises(AIConnectionError):
            ask(client)
    assert len(calls) == 1 and calls[0][0] == "POST"
    assert UsageLog().this_month()[0].usage.unreported_requests == 1
    assert not request_recovery.pending(force=True)


def test_retrieval_rate_limit_obeys_retry_after_without_repeating_generation(service):
    def handler(request, calls):
        if request.method == "POST":
            return httpx.Response(200, json={"id": "fictional-1", "status": "in_progress"})
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        if sum(method == "GET" for method, _, _ in calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "3"}, json={"error": {"code": 429,
                "status": "RESOURCE_EXHAUSTED", "message": "Retry in 3 seconds"}})
        return httpx.Response(200, json=operation())

    client, _, calls, waits, _ = service(handler)
    assert ask(client).ok
    assert sum(method == "POST" for method, _, _ in calls) == 1
    assert sum(waits) >= 4  # ordinary processing poll plus the server's retrieval wait


def test_stop_cancels_then_records_final_usage_before_deletion(service):
    from jobcu.search import SearchStopped

    created = False

    def checkpoint():
        if created:
            raise SearchStopped

    def handler(request, calls):
        nonlocal created
        if request.url.path.endswith("/cancel"):
            return httpx.Response(200, json=operation(status="cancelled"))
        if request.method == "POST":
            created = True
            return httpx.Response(200, json={"id": "fictional-1", "status": "in_progress"})
        if request.method == "DELETE":
            assert UsageLog().this_month()[0].usage == Usage(100, 80, 0, 50)
            return httpx.Response(200, json={})
        pytest.fail("Stop must cancel before another result poll")

    client, _, calls, _, _ = service(handler, checkpoint=checkpoint)
    with pytest.raises(SearchStopped):
        ask(client)
    assert [method for method, _, _ in calls] == ["POST", "POST", "DELETE"]
    assert calls[1][1].endswith("/cancel")
    assert not request_recovery.pending(force=True)
    assert UsageLog().for_search(1)["scoring"] == Usage(100, 80, 0, 50)


def test_completed_answer_is_kept_when_its_bill_reaches_the_monthly_limit(service):
    settings = Settings()
    settings.limits.monthly_token_limit = 50

    def handler(request, calls):
        if request.method == "POST":
            return httpx.Response(200, json=operation())
        return httpx.Response(200, json={})

    client, _, calls, _, _ = service(handler, settings=settings)
    assert ask(client).ok
    with pytest.raises(AILimitReached):
        ask(client, "A second paid generation must not start")
    assert [method for method, _, _ in calls] == ["POST", "DELETE"]


def test_delete_failure_keeps_usable_answer_and_retries_cleanup_on_demand(service):
    deletion_allowed = False

    def handler(request, calls):
        if request.method in {"POST", "GET"}:
            return httpx.Response(200, json=operation())
        if deletion_allowed:
            return httpx.Response(200, json={})
        return httpx.Response(503, json={"error": {"code": 503, "message": "Fictional outage"}})

    client, adapter, calls, _, notices = service(handler)
    assert ask(client).ok
    assert len(request_recovery.pending(force=True)) == 1
    assert any("could not be deleted" in note for note in notices)
    assert not request_recovery.pending()  # no repeated cleanup storm during this minute
    deletion_allowed = True
    adapter.cleanup_pending(RecoveryContext(False, "gemini", "cleanup"), force=True)
    assert not request_recovery.pending(force=True)
    assert sum(method == "POST" for method, _, _ in calls) == 1
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ai_usage").fetchone()[0] == 1


def test_abandoned_request_is_reconciled_and_cleaned_before_new_work(service):
    old = RecoveryContext(True, "gemini", "job_places", search_id=99)
    request_recovery.track(old, "fictional-old", "gemini-3.8-flash")
    request_recovery.release("gemini", "fictional-old", deleted=False)
    UsageLog().record(step="job_places", provider="gemini", model="gemini-3.8-flash",
                      usage=Usage(web_searches=1, unreported_requests=1), search_id=99,
                      recovery_id="fictional-old")

    def handler(request, calls):
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        if request.method == "GET":
            return httpx.Response(200, json=operation("fictional-old", research=True))
        return httpx.Response(200, json=operation())

    client, _, calls, _, _ = service(handler)
    assert ask(client).ok
    assert [method for method, _, _ in calls] == ["GET", "DELETE", "POST", "DELETE"]
    assert UsageLog().for_search(99)["job_places"] == Usage(100, 80, 0, 50, 1)
    assert not request_recovery.pending(force=True)


def test_observed_inflight_bill_at_monthly_limit_cancels_without_new_work(service):
    settings = Settings()
    settings.limits.monthly_token_limit = 50

    def handler(request, calls):
        if request.url.path.endswith("/cancel"):
            return httpx.Response(200, json=operation(status="cancelled", tokens=120))
        if request.method == "POST":
            return httpx.Response(200, json={"id": "fictional-1", "status": "in_progress"})
        if request.method == "GET":
            return httpx.Response(200, json=operation(status="in_progress"))
        return httpx.Response(200, json={})

    client, _, calls, _, _ = service(handler, settings=settings)
    with pytest.raises(AILimitReached):
        ask(client)
    assert [method for method, _, _ in calls] == ["POST", "GET", "POST", "DELETE"]
    assert calls[2][1].endswith("/cancel")
    assert UsageLog().for_search(1)["scoring"] == Usage(120, 80, 0, 50)


def test_completion_racing_with_stop_recovers_the_same_final_bill(service):
    from jobcu.search import SearchStopped

    created = False
    def checkpoint():
        if created:
            raise SearchStopped

    def handler(request, calls):
        nonlocal created
        if request.url.path.endswith("/cancel"):
            return httpx.Response(409, json={"error": {"code": "conflict",
                                                       "message": "Already completed"}})
        if request.method == "POST":
            created = True
            return httpx.Response(200, json={"id": "fictional-1", "status": "in_progress"})
        if request.method == "GET":
            return httpx.Response(200, json=operation())
        return httpx.Response(200, json={})

    client, _, calls, _, _ = service(handler, checkpoint=checkpoint)
    with pytest.raises(SearchStopped):
        ask(client)
    assert [method for method, _, _ in calls] == ["POST", "POST", "GET", "DELETE"]
    assert UsageLog().for_search(1)["scoring"] == Usage(100, 80, 0, 50)


def test_concurrent_recovery_never_cancels_another_active_request(service):
    import itertools
    import threading
    from concurrent.futures import ThreadPoolExecutor

    identifiers = itertools.count()
    entered = threading.Barrier(4)
    def handler(request, calls):
        if request.url.path.endswith("/cancel"):
            pytest.fail("One thread must not treat another active request as abandoned")
        if request.method == "POST":
            identifier = f"fictional-{next(identifiers)}"
            entered.wait(timeout=5)
            return httpx.Response(200, json={"id": identifier, "status": "in_progress"})
        if request.method == "GET":
            return httpx.Response(200, json=operation(request.url.path.rsplit("/", 1)[1]))
        return httpx.Response(200, json={})

    client, _, calls, _, _ = service(handler)
    with ThreadPoolExecutor(max_workers=4) as workers:
        assert all(value.ok for value in workers.map(lambda i: ask(client, f"Fictional {i}"),
                                                     range(4)))
    assert sum(method == "POST" for method, _, _ in calls) == 4
    assert sum(method == "DELETE" for method, _, _ in calls) == 4
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ai_usage").fetchone()[0] == 4
    assert not request_recovery.pending(force=True)


@pytest.mark.parametrize("invalid", ["wrong_id", "missing_status"])
def test_unconfirmed_old_work_blocks_new_generation_and_keeps_cleanup_id(service, invalid):
    old = RecoveryContext(True, "gemini", "job_places", search_id=99)
    request_recovery.track(old, "fictional-old", "gemini-3.8-flash")
    request_recovery.release("gemini", "fictional-old", deleted=False)

    def handler(request, calls):
        assert request.method == "GET" or request.url.path.endswith("/cancel")
        response = operation("wrong-id" if invalid == "wrong_id" else "fictional-old")
        if invalid == "missing_status":
            response.pop("status")
        return httpx.Response(200, json=response)

    from jobcu.ai.base import AIUsageUncertain
    client, _, calls, _, _ = service(handler)
    with pytest.raises(AIUsageUncertain):
        ask(client)
    assert len(request_recovery.pending(force=True)) == 1  # no leaked active claim
    assert not any(method == "DELETE" for method, _, _ in calls)
    assert not any(method == "POST" and not path.endswith("/cancel")
                   for method, path, _ in calls)


def test_cumulative_receipts_are_one_charge_and_keep_original_month():
    log = UsageLog()
    args = dict(step="job_places", provider="gemini", model="fictional-model", search_id=99,
                recovery_id="fictional-old", created_at="2026-09-30T23:59:59Z")
    log.record(**args, usage=Usage(10, 20, 0, 5, 1, 1))
    log.record(**args, usage=Usage(100, 80, 0, 50, 3, 0))
    log.record(**args, usage=Usage(5, 10, 0, 5, 0, 1))
    assert log.for_search(99)["job_places"] == Usage(100, 80, 0, 50, 3, 0)
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM ai_usage").fetchall()
    assert len(rows) == 1 and rows[0]["created_at"] == args["created_at"]


def test_one_uncancellable_orphan_does_not_leave_other_abandoned_work_running(service):
    from jobcu.ai.base import AIUsageUncertain

    old = RecoveryContext(True, "gemini", "job_places", search_id=99)
    for identifier in ("fictional-stuck", "fictional-done"):
        request_recovery.track(old, identifier, "gemini-3.8-flash")
        request_recovery.release("gemini", identifier, deleted=False)

    def handler(request, calls):
        if "fictional-stuck" in request.url.path:
            return httpx.Response(503, json={"error": {"code": 503, "message": "Outage"}})
        assert "fictional-done" in request.url.path
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        return httpx.Response(200, json=operation("fictional-done", research=True))

    client, _, calls, _, _ = service(handler)
    with pytest.raises(AIUsageUncertain):
        ask(client)
    row, = request_recovery.pending(force=True)
    assert row["interaction_id"] == "fictional-stuck"
    assert any(method == "DELETE" and path.endswith("/fictional-done")
               for method, path, _ in calls)
    assert not any(method == "POST" and not path.endswith("/cancel")
                   for method, path, _ in calls)


def test_same_request_recovery_bills_only_the_selected_extra_allowance(service, temporary_data_dir):
    from test_extra_budgets import configure
    settings, log, allowance = configure(temporary_data_dir)
    settings.prices[0].model = 'gemini-3.8-flash'
    ordinary = log.ordinary_this_month()
    def handler(request, calls):
        if request.method == 'DELETE':
            return httpx.Response(200, json={})
        if request.method == 'POST':
            return httpx.Response(200, json={'id': 'fictional-extra', 'status': 'in_progress'})
        return httpx.Response(200, json=operation('fictional-extra'))
    client, _, _, _, _ = service(handler, settings=settings)
    client.budget_id = allowance.id
    assert ask(client).ok
    assert log.ordinary_this_month() == ordinary
    assert len(log.for_budget(allowance.id, after_id=2)) == 1
    with db.connect() as conn:
        assert conn.execute('SELECT budget_id FROM ai_usage WHERE recovery_id=?',
                             ('fictional-extra',)).fetchone()[0] == allowance.id
