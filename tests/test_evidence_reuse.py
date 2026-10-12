"""Original evidence and identical route requests, using only fictional offline data."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from jobcu import jobplace, requirements, travel
from jobcu.keystore import KeyStore
from jobcu.sources.base import SourceContext, SourceReport
from jobcu.sources.budget import Limits, RequestBudget
from jobcu.sources.careers import Employer
from jobcu.sources.greenhouse import GreenhouseSource
from jobcu.sources.http import PoliteClient

NOW = datetime(2026, 10, 12, 10, tzinfo=UTC)


@pytest.mark.parametrize("profession", ["Electronics engineer", "Nurse", "Teacher"])
@pytest.mark.parametrize("count", [1, 10])
def test_greenhouse_list_supplies_original_evidence_without_a_detail_request(profession, count):
    from types import SimpleNamespace

    from jobcu.dedupe import JobGroup
    from jobcu.pipeline import load_full_ads

    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.params.get("content") == "true"
        return httpx.Response(200, json={"jobs": [{
            "id": i, "title": profession, "location": {"name": "Berlin, Germany"},
            "absolute_url": f"https://example.test/fictional/{i}",
            "first_published": NOW.isoformat(),
            "application_deadline": (NOW + timedelta(days=7)).isoformat(),
            "content": "&lt;p&gt;A completed qualification is required.&lt;/p&gt;",
        } for i in range(count)]})

    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    ctx = SourceContext(http, KeyStore(), SourceReport("greenhouse", "Fictional board"),
                        lambda: False, lambda message: None)
    source = GreenhouseSource()
    jobs = list(source.list_jobs(Employer("Fictional", "greenhouse", "fake", ()), ctx))
    run = SimpleNamespace(stop_requested=False, note=lambda _: None, update=lambda *args: None)
    load_full_ads([JobGroup([job]) for job in jobs], range(count), SimpleNamespace(
        sources={source.id: source}, reports=[ctx.report]), http, ctx.keys, run)
    assert len(requests) == 1
    assert len(jobs) == count
    assert all(job.description == "A completed qualification is required."
               and job.description_is_complete and job.posted_at == NOW for job in jobs)


@pytest.mark.parametrize("publication", [NOW.isoformat(), None])
@pytest.mark.parametrize("list_date_known", [False, True])
def test_full_greenhouse_text_does_not_skip_missing_dates_or_deadlines(
        publication, list_date_known):
    import dataclasses
    from types import SimpleNamespace

    from jobcu.dedupe import JobGroup
    from jobcu.filters import apply_rules
    from jobcu.pipeline import load_full_ads
    from jobcu.settings import JOB_TYPES
    from jobcu.sources.greenhouse import to_found_job

    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"content": "<p>Original complete ad.</p>",
                                        "first_published": publication,
                                        "application_deadline":
                                            (NOW - timedelta(hours=1)).isoformat()})

    job = to_found_job({"id": 1, "title": "Teacher", "content": "<p>Original complete ad.</p>"},
                      Employer("Fictional school", "greenhouse", "fake", ("DE",)))
    if list_date_known:
        job = dataclasses.replace(job, posted_at=NOW, date_precision="exact")
    source = GreenhouseSource()
    collected = SimpleNamespace(sources={source.id: source}, reports=[
        SourceReport(source.id, source.name)])
    run = SimpleNamespace(stop_requested=False, note=lambda _: None, update=lambda *args: None)
    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    groups = [JobGroup([job])]
    load_full_ads(groups, [0], collected, http, KeyStore(), run)
    assert groups[0].posted_at == (NOW if publication or list_date_known else None)
    assert groups[0].closes_at == NOW - timedelta(hours=1)
    assert len(requests) == 1
    filtered = apply_rules(groups, remembered_states=[None], started_at=NOW,
                           posted_within_hours=24, job_types=list(JOB_TYPES),
                           exclude_remote=False, countries=["DE"])
    assert filtered.left_out == {"closed": 1}
    # Valid prior metadata attempts can be reused, while current full text stays current.
    current = dataclasses.replace(job, description="A newly stated teaching qualification.")
    groups = [JobGroup([current])]
    load_full_ads(groups, [0], collected, http, KeyStore(), run)
    assert groups[0].best_description_copy.description == current.description
    assert groups[0].posted_at == (NOW if publication or list_date_known else None)
    assert groups[0].closes_at == NOW - timedelta(hours=1)
    assert len(requests) == 1


def test_failed_greenhouse_metadata_with_complete_text_stays_retryable():
    from types import SimpleNamespace

    from jobcu import jobstore
    from jobcu.dedupe import JobGroup
    from jobcu.pipeline import load_full_ads
    from jobcu.sources.greenhouse import to_found_job

    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(404)
        return httpx.Response(200, json={"content": "<p>Original complete ad.</p>",
                                        "first_published": NOW.isoformat()})

    job = to_found_job({"id": 1, "title": "Nurse", "content": "<p>Original complete ad.</p>"},
                      Employer("Fictional clinic", "greenhouse", "fake", ("DE",)))
    source = GreenhouseSource()
    run = SimpleNamespace(stop_requested=False, note=lambda _: None, update=lambda *args: None)
    collected = SimpleNamespace(sources={source.id: source}, reports=[
        SourceReport(source.id, source.name)])
    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    groups = [JobGroup([job])]
    load_full_ads(groups, [0], collected, http, KeyStore(), run)
    assert groups[0].posted_at is None and groups[0].best_description_copy.description_is_complete
    assert jobstore.remembered_ad(job, reader_version=source.detail_cache_version) is None
    groups = [JobGroup([job])]
    load_full_ads(groups, [0], collected, http, KeyStore(), run)
    assert groups[0].posted_at == NOW and len(calls) == 2


@pytest.mark.parametrize("heading", ["**JOB J0**", "### **JOB J0**", "**J0**"])
def test_markdown_job_heading_preserves_own_supported_requirement(heading):
    notes = f"{heading}\nA completed qualification is required.\n**JOB J1**\nOther evidence."
    own = jobplace._job_notes(notes, "J0", 2)
    checked = requirements.ground([requirements.RequirementCheck(
        requirement="Qualification", ad_words="A completed qualification is required.",
        profile_words="Completed fictional qualification", status="met",
    )], own, "Completed fictional qualification")
    assert checked[0]["status"] == "met"
    assert "Other evidence" not in own
    assert jobplace._job_notes(notes + "\n**JOB J0**\nDuplicate.", "J0", 2) == ""


def test_maps_reuses_exact_elements_in_one_session_and_keeps_failures_retryable():
    bodies = []

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if len(bodies) == 1:
            return httpx.Response(200, json=[
                {"destinationIndex": 0, "condition": "ROUTE_EXISTS", "duration": "600s"},
                {"destinationIndex": 1, "status": {"code": 14}},
            ])
        return httpx.Response(200, json=[
            {"destinationIndex": 0, "condition": "ROUTE_EXISTS", "duration": "1200s"},
        ])

    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    maps = travel.GoogleMaps("fictional", http, now=lambda: NOW)
    origin, a, b = {"address": "Fictional workplace"}, {"address": "Town A"}, {"address": "Town B"}
    assert maps._matrix(origin, [a, b], "transit", "DE") == {0: 10}
    assert maps._matrix(origin, [a, b], "transit", "DE") == {0: 10, 1: 20}
    assert len(bodies[1]["destinations"]) == 1
    assert maps._matrix(origin, [b, a], "transit", "DE") == {0: 20, 1: 10}
    assert len(bodies) == 2
    # A different mode, origin, destination or departure identity needs new evidence.
    maps._matrix(origin, [a], "drive", "DE")
    maps._matrix({"address": "Another district"}, [a], "transit", "DE")
    assert len(bodies) == 4


def test_maps_overlapping_queries_spend_only_new_elements_and_exact_dates():
    bodies = []
    now = NOW
    routes = RequestBudget("fictional_maps", "Fictional Maps", Limits(per_search=20),
                           now=lambda: now)

    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        return httpx.Response(200, json=[
            {"destinationIndex": i, "condition": "ROUTE_EXISTS", "duration": "600s"}
            for i, _ in enumerate(body["destinations"])
        ])

    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    maps = travel.GoogleMaps("fictional", http, now=lambda: now, routes=routes)
    origin = {"address": "Fictional workplace"}
    a, b, c = ({"address": name} for name in ["Town A", "Town B", "Town C"])
    assert maps._matrix(origin, [a, b], "transit", "DE") == {0: 10, 1: 10}
    assert maps._matrix(origin, [b, c, b], "transit", "DE") == {0: 10, 1: 10, 2: 10}
    assert routes.used_this_search == 3  # previously five attempted cells across two matrices
    assert [len(body["destinations"]) for body in bodies] == [2, 1]
    now += timedelta(days=7)
    maps._matrix(origin, [a], "transit", "DE")
    assert bodies[-1]["departureTime"] != bodies[0]["departureTime"]
    # A new search cannot reuse old Google durations, even with the same HTTP client.
    travel.GoogleMaps("fictional", http, now=lambda: now, routes=routes)._matrix(
        origin, [a], "transit", "DE")
    assert routes.used_this_search == 5 and len(bodies) == 4


@pytest.mark.parametrize("failure", ["quota", "budget", "malformed"])
def test_maps_known_cells_survive_later_failure_without_spending_them_again(failure):
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(200, json=[{
                "destinationIndex": 0, "condition": "ROUTE_EXISTS", "duration": "600s",
            }])
        if failure == "quota":
            return httpx.Response(403, json={"error": "fictional key refused"})
        return httpx.Response(200, json={"unexpected": "body"})

    routes = RequestBudget("fictional_maps", "Fictional Maps",
                           Limits(per_search=1 if failure == "budget" else 20), now=lambda: NOW)
    maps = travel.GoogleMaps("fictional", PoliteClient(
        min_intervals={}, transport=httpx.MockTransport(handler)), now=lambda: NOW, routes=routes)
    origin, a, b = ({"address": name} for name in ["Workplace", "Town A", "Town B"])
    assert maps._matrix(origin, [a], "transit", "DE") == {0: 10}
    assert maps._matrix(origin, [b, a], "transit", "DE") == {1: 10}
    if failure == "malformed":
        assert maps._matrix(origin, [b, a], "transit", "DE") == {1: 10}
        assert len(calls) == 3  # unresolved body is retryable
    else:
        assert maps._matrix(origin, [b, a], "transit", "DE") == {1: 10}
        assert len(calls) == (1 if failure == "budget" else 2)
    assert all(len(body["destinations"]) == 1 for body in calls)


@pytest.mark.parametrize("legacy", [False, True])
def test_factual_research_note_has_no_uncertainty_marker_but_missing_evidence_keeps_it(legacy):
    from jobcu.dedupe import JobGroup
    from jobcu.location import LocationPlan
    from jobcu.pipeline import build_card
    from jobcu.scoring import LEGACY_ONLINE_NOTE, ONLINE_NOTE
    from jobcu.sources.base import FoundJob

    group = JobGroup([FoundJob(source="fictional", source_job_id="1", title="Nurse",
                              url="https://example.test/1", country="DE")])
    plan = LocationPlan(text="", understood_as="Germany", countries=["DE"], places=[],
                        conditions=[], not_checked_yet=[], outside_supported_area=[], broad=False)
    result = {"score": 60, "parts": {}, "reasons": [], "required_languages": [],
              "notes": [LEGACY_ONLINE_NOTE if legacy else ONLINE_NOTE,
                        "Mandatory requirements were not fully checked"]}
    card = build_card(group, job_id=1, is_new=True, state=None, scored=result, plan=plan,
                      source_names={}, possible_duplicate_of=None, started_at=NOW,
                      posted_within_hours=24)
    assert card["score_checks"] == [
        {"text": ONLINE_NOTE, "status": "info"},
        {"text": "Mandatory requirements were not fully checked", "status": "unclear"},
    ]
    assert card["score"] == 60 and card["score_notes"] == result["notes"]
