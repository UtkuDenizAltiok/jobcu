"""Fictional routes, quotas and clocks; never calls Google or uses owner inputs."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import httpx
import pytest
from test_source_cooldowns import Clock
from test_travel import group

from jobcu import db, places, search, travel
from jobcu.keystore import KeyStore
from jobcu.location import Anchor, Condition, TownRef
from jobcu.settings import SearchForm, Settings
from jobcu.sources.budget import BudgetExhausted, Limits, RequestBudget
from jobcu.sources.http import PoliteClient, RequestStopped

NOW = datetime(2026, 10, 8, 12, tzinfo=UTC)


def near():
    return Condition(text="Within 35 minutes of Munich", understood_as="Near Munich",
                     status="estimate", kind="near", max_minutes=35, travel_mode="transit",
                     anchor=Anchor(named=[TownRef(name="Munich", country="DE")]))


def quota(unit, *, message="Quota exceeded.", value="10"):
    return httpx.Response(429, json={"error": {
        "code": 429, "status": "RESOURCE_EXHAUSTED", "message": message,
        "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                     "reason": "QUOTA_EXCEEDED", "domain": "googleapis.com",
                     "metadata": {"quota_limit_unit": unit, "quota_limit_value": value,
                                  "consumer": "projects/fictional-project"}}],
    }})


def setup(handler, limit=100, *, clock=None, notes=None, stop=None):
    clock = clock or Clock()
    http = PoliteClient(min_intervals={"routes.googleapis.com": 0, "other.example.test": 0},
                        transport=httpx.MockTransport(handler), sleep=clock.sleep,
                        clock=clock.read, wall_clock=lambda: NOW.timestamp(), should_stop=stop,
                        on_wait=lambda h, s: (notes.append(s) if notes is not None else None))
    settings = Settings()
    settings.limits.maps_monthly_routes = limit
    keys = KeyStore()
    keys.set(travel.KEY_NAME, "fictional-maps-key")
    meter = travel.TravelMeter(None, keys, http, settings, now=lambda: NOW)
    point = travel.job_point(group("Freising"))
    towns = [places.find("Munich", "DE")]
    return meter, http, clock, [(point, towns, ["s:1"])]


def success(request):
    body = json.loads(request.content)
    return httpx.Response(200, json=[
        {"destinationIndex": i, "condition": "ROUTE_EXISTS", "duration": "1140s"}
        for i in range(len(body["destinations"]))])


@pytest.mark.parametrize("unit", ["1/d/{project}", "1/mo/{project}"])
def test_persistent_structured_quota_has_one_attempt_and_no_wait(unit):
    calls, notes = [], []
    def handler(request):
        calls.append(request.url.host)
        return quota(unit)
    meter, http, clock, requested = setup(handler, notes=notes)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert calls == ["routes.googleapis.com"]
        assert notes == [] and clock.sleeps == []
        assert meter._routes.used_this_search == 2
    finally:
        http.close()


def test_zero_quota_does_not_retry_even_when_its_unit_is_per_minute():
    calls = []
    def handler(request):
        calls.append(request)
        return quota("1/min/{project}", value="0")
    meter, http, clock, requested = setup(handler)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert len(calls) == 1 and not clock.sleeps
    finally:
        http.close()


@pytest.mark.parametrize("status", [429, 503])
def test_temporary_failure_recovers_full_measurement_and_counts_every_attempt(status):
    times, notes = [], []
    def handler(request):
        times.append(clock.read())
        if len(times) == 1:
            return httpx.Response(status, headers={"Retry-After": "7"}, json={
                "error": {"message": "Temporary limit"}})
        return success(request)
    clock = Clock()
    meter, http, clock, requested = setup(handler, limit=4, clock=clock, notes=notes)
    try:
        found = meter._with_maps(requested, "transit")
        assert found[requested[0][0].key].minutes == {"Munich": 19}
        assert times == [100, 107] and notes == [7]
        assert meter._routes.used_this_search == 4
        with db.connect() as conn:
            assert conn.execute("SELECT SUM(count) FROM source_requests "
                                "WHERE source = 'google_maps_routes'").fetchone()[0] == 4
        assert meter._with_maps(requested, "transit") == found
        assert times == [100, 107] and meter._routes.used_this_search == 4
    finally:
        http.close()


def test_unfunded_retry_neither_sends_nor_waits_and_keeps_remaining_evidence_uncertain():
    calls, notes = [], []
    def handler(request):
        calls.append(request)
        return httpx.Response(503, headers={"Retry-After": "600"})
    meter, http, clock, requested = setup(handler, limit=2, notes=notes)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert len(calls) == 1 and meter._routes.used_this_search == 2
        assert not clock.sleeps and not notes
    finally:
        http.close()


def test_confirmed_persistent_quota_is_not_repeated_in_later_measurement_rounds():
    calls = []
    def handler(request):
        calls.append(request.url.host)
        if request.url.host == "other.example.test":
            return httpx.Response(200, text="Full fictional nursing requirements")
        return quota("1/d/{project}")
    meter, http, clock, requested = setup(handler)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert meter._with_maps(requested, "transit") == {}
        assert calls == ["routes.googleapis.com"] and not clock.sleeps
        assert http.get("https://other.example.test/nursing").status_code == 200
        assert calls[-1] == "other.example.test"
    finally:
        http.close()


def test_terminal_throttling_does_not_announce_a_retry_that_will_not_happen():
    calls, notes = [], []
    def handler(request):
        calls.append(clock.read())
        return httpx.Response(429, json={"error": {"message": "Unspecified request limit"}})
    clock = Clock()
    meter, http, clock, requested = setup(handler, clock=clock, notes=notes)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert calls == [100, 105, 115, 135]
        assert notes == [5, 10, 20]
        assert meter._routes.used_this_search == 8
    finally:
        http.close()


def test_cancellation_during_wait_does_not_charge_or_send_the_next_attempt():
    stopped = [False]
    clock = Clock()
    original = clock.sleep
    def sleep(seconds):
        original(seconds)
        stopped[0] = True
    clock.sleep = sleep
    meter, http, clock, requested = setup(
        lambda r: httpx.Response(503, headers={"Retry-After": "600"}),
        clock=clock, stop=lambda: stopped[0])
    try:
        with pytest.raises(RequestStopped):
            meter._with_maps(requested, "transit")
        assert meter._routes.used_this_search == 2
        assert http.request_count["routes.googleapis.com"] == 1
    finally:
        http.close()


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse", "Chef"])
def test_quota_fallback_retains_fictional_jobs_and_labels_estimates(title):
    meter, http, clock, _ = setup(lambda r: quota("1/d/{project}"))
    notes = []
    meter._note = notes.append
    def estimate(requested, mode, centre=False):
        return {p.key: {t.name: 25 for t in towns} for p, towns, _ in requested}
    meter._estimate = estimate
    condition, job = near(), group("Freising")
    job.copies[0].title = title
    try:
        meter.measure([condition], [job], [0])
        assert condition.travel[travel.job_key(job)]["by"] == travel.ESTIMATE
        assert condition.travel[travel.job_key(job)]["minutes"]
        assert condition.status == "estimate"
        assert any("daily" in n and "AI estimates" in n for n in notes)
        assert len(job.copies) == 1 and job.main.title == title
    finally:
        http.close()


def test_budget_preflight_never_spends_and_committed_spend_still_rechecks():
    budget = RequestBudget("fictional", "Fictional", Limits(per_month=2), now=lambda: NOW)
    budget.check(2)
    assert budget.used_this_search == 0
    other = RequestBudget("fictional", "Fictional", Limits(per_month=2), now=lambda: NOW)
    other.spend(2)
    with pytest.raises(BudgetExhausted):
        budget.spend(2)
    assert budget.used_this_search == 0


def test_saved_route_measurement_survives_a_later_quota_and_exhausted_allowance():
    calls = []
    def handler(request):
        calls.append(request)
        return success(request) if len(calls) == 1 else quota("1/d/{project}")
    meter, http, clock, requested = setup(handler, limit=4)
    other = [(travel.job_point(group("Augsburg")), requested[0][1], ["s:2"])]
    try:
        measured = meter._with_maps(requested, "transit")
        assert measured and meter._with_maps(other, "transit") == {}
        assert meter._with_maps(requested, "transit") == measured
        assert len(calls) == 2 and meter._routes.used_this_search == 4
    finally:
        http.close()


def test_initial_allowance_exhaustion_does_not_send_or_charge():
    calls = []
    meter, http, clock, requested = setup(lambda r: calls.append(r), limit=1)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert not calls and meter._routes.used_this_search == 0
    finally:
        http.close()


@pytest.mark.parametrize(("payload", "expected"), [
    ({"error": {"message": "Daily quota exhausted"}}, "day"),
    ([{"error": {"message": "Elements per day exhausted"}}], "day"),
    ({"error": {"message": "Limit per minute exceeded"}}, "minute"),
    ({"error": {"message": "requests_per_day exceeded"}}, "day"),
    ({"error": {"message": "requests-per-minute exceeded"}}, "minute"),
    ({"error": {"message": "x" * 400 + " monthly quota"}}, "month"),
    ({"error": {"details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                              "metadata": {"quota_limit": "MatrixPerDayPerProject"}}]}}, "day"),
    ({"error": {"details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure",
                              "violations": [{"description": "Elements per day exhausted"}]}]}},
     "day"),
    (None, "unknown"), ([], "unknown"), ({"error": "broken"}, "unknown"),
    ({"error": {"details": ["broken"]}}, "unknown"),
])
def test_quota_scope_formats_and_missing_evidence(payload, expected):
    assert travel._quota_scope(httpx.Response(429, json=payload)) == expected


def test_quota_diagnostics_never_log_fictional_consumer_identifiers(caplog):
    meter, http, clock, requested = setup(lambda r: quota("1/d/{project}"))
    try:
        meter._with_maps(requested, "transit")
        assert "quota scope: day" in caplog.text
        assert "fictional-project" not in caplog.text and "consumer" not in caplog.text
    finally:
        http.close()


def test_simultaneous_budget_instances_cannot_pass_the_shared_monthly_cap():
    with db.connect():
        pass
    def spend(_):
        budget = RequestBudget("shared-fictional", "Fictional", Limits(per_month=4),
                               now=lambda: NOW)
        try:
            budget.spend()
            return True
        except BudgetExhausted:
            return False
    with ThreadPoolExecutor(max_workers=8) as workers:
        assert sum(workers.map(spend, range(8))) == 4
    with db.connect() as conn:
        assert conn.execute("SELECT SUM(count) FROM source_requests "
                            "WHERE source = 'shared-fictional'").fetchone()[0] == 4


def test_wait_progress_changes_without_repeated_warnings_or_restarting_the_step_timer(monkeypatch):
    seconds = [100.0]
    monkeypatch.setattr(search.time, "monotonic", lambda: seconds[0])
    run = search.SearchRun(id=1, form=SearchForm(), started_at=NOW.isoformat())
    run.update("filtering", "running")
    search._source_wait_note(run, "routes.googleapis.com", 5)
    seconds[0] = 105
    search._source_wait_note(run, "routes.googleapis.com", 10)
    seconds[0] = 111
    assert len(run.notes) == 1 and "route limit" in run.notes[0]
    assert "10 seconds" in run.step("filtering").detail
    filtering = next(step for step in run.snapshot()["steps"] if step["id"] == "filtering")
    assert filtering["elapsed_seconds"] == 11
    run.update("filtering", "done")
    run.update("places", "running")
    search._source_wait_note(run, "routes.googleapis.com", 20)
    assert len(run.notes) == 1 and "20 seconds" in run.step("places").detail


def test_skipping_a_retry_still_honors_retry_after_for_other_readers():
    times = []
    clock = Clock()
    def handler(request):
        times.append(clock.read())
        return (httpx.Response(429, headers={"Retry-After": "600"}) if len(times) == 1
                else httpx.Response(200, text="Full fictional ad"))
    _, http, _, _ = setup(handler, clock=clock)
    try:
        assert http.get("https://routes.googleapis.com/first",
                        retry_response=lambda r: False).status_code == 429
        assert times == [100] and not clock.sleeps
        assert http.get("https://routes.googleapis.com/second").status_code == 200
        assert times == [100, 700]
    finally:
        http.close()


def test_network_retry_attempts_are_counted_too(monkeypatch):
    from jobcu.sources import http as source_http

    monkeypatch.setattr(source_http.random, "uniform", lambda a, b: 0)
    calls = []
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ReadTimeout("Fictional network timeout")
        return success(request)
    meter, http, _, requested = setup(handler, limit=4)
    try:
        assert meter._with_maps(requested, "transit")
        assert len(calls) == 2 and meter._routes.used_this_search == 4
    finally:
        http.close()


@pytest.mark.parametrize("status", [401, 403])
def test_key_refusal_is_not_repeated_or_charged_again_in_this_meter(status):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "Fictional key refusal"}})
    meter, http, _, requested = setup(handler)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert meter._with_maps(requested, "transit") == {}
        assert len(calls) == 1 and meter._routes.used_this_search == 2
    finally:
        http.close()


def test_recognized_access_refusal_keeps_maps_fallback_without_a_bypass():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, text="<html>Captcha verification required</html>")
    meter, http, _, requested = setup(handler)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert meter._with_maps(requested, "transit") == {}
        assert len(calls) == 1 and meter._routes.used_this_search == 2
    finally:
        http.close()


def test_unfunded_network_retry_does_not_wait_or_send():
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("Fictional timeout")
    meter, http, clock, requested = setup(handler, limit=2)
    try:
        assert meter._with_maps(requested, "transit") == {}
        assert len(calls) == 1 and not clock.sleeps
        assert meter._routes.used_this_search == 2
    finally:
        http.close()
