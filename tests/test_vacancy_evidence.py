"""Fictional exact-original facts override refreshed boards without rewriting history."""

import copy
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from test_search import PROFILE

from jobcu import db, jobstore, pipeline, pool, search, travel, vacancy_evidence
from jobcu.app import create_app
from jobcu.dedupe import JobGroup
from jobcu.filters import apply_rules
from jobcu.location import Anchor, Condition, LocationPlan, TownRef
from jobcu.settings import SearchForm, Settings
from jobcu.sources.base import FoundJob

NOW = datetime.now(UTC)
ORIGINAL = "https://careers.example.test/vacancy/REQ-10"


def saved(title="Power Electronics Engineer"):
    groups = [JobGroup([FoundJob("employer", str(i), f"https://careers.example.test/jobs/{i}",
              title, company="Fictional Employer", country="DE", location_text="Berlin",
              posted_at=NOW, date_precision="exact", description="Fictional full ad.",
              description_is_complete=True)], source_kinds={"employer": "employer"})
              for i in range(3)]
    with db.connect() as conn:
        search_id = conn.execute("INSERT INTO searches (status,form_json) "
                                 "VALUES ('finished','{}')").lastrowid
    ids, _ = jobstore.remember(groups, search_id)
    assert len(set(ids)) == 3  # same title/company are not the same native requisition
    return search_id, groups, ids


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Ward Nurse", "Physics Teacher"])
def test_exact_original_facts_override_a_new_board_date_and_preserve_other_requisitions(title):
    _, groups, ids = saved(title)
    with db.connect() as conn:
        original_rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        original_keys = conn.execute("SELECT * FROM job_keys ORDER BY key").fetchall()
    vacancy_evidence.record(ids[0], "closed", ORIGINAL, "The exact vacancy is no longer available.")
    vacancy_evidence.record(ids[1], "posted_before", ORIGINAL + "1", "Original is 80 days old.",
                            posted_before=NOW - timedelta(days=79))
    outcome = apply_rules(groups, [None] * 3, started_at=NOW, posted_within_hours=24,
                          job_types=["full_time_permanent"], exclude_remote=False, countries=["DE"])
    assert outcome.kept == [2]
    assert outcome.left_out == {"verified_closed": 1, "original_date": 1}
    with db.connect() as conn:
        assert conn.execute("SELECT * FROM jobs ORDER BY id").fetchall() == original_rows
        assert conn.execute("SELECT * FROM job_keys ORDER BY key").fetchall() == original_keys
    # A conservative upper bound overlapping the window cannot establish an old posting.
    assert vacancy_evidence.reasons(ids, NOW - timedelta(days=90)) == {ids[0]: "verified_closed"}


def test_saved_response_and_undo_preserve_marks_and_original_snapshot(monkeypatch):
    search_id, _, ids = saved()
    card = {"job_id": ids[0], "title": "Fictional role", "score": 88, "is_new": True,
            "state": {"saved": True, "applied": True, "dismissed": False},
            "main_link": {"source": "Employer's site", "url": ORIGINAL}, "also_on": []}
    snapshot = {"id": search_id, "status": "finished", "started_at": NOW.isoformat(),
                "form": {"posted_within_hours": 24}, "result": {"jobs": {
                    "cards": [card], "date_unknown": [], "hidden": [],
                    "counts": {"shown": 1}}}}
    original = json.dumps(snapshot)
    jobstore.finish_search(search_id, "finished", original)
    jobstore.set_state(ids[0], saved=True, applied=True)
    evidence_id = vacancy_evidence.record(ids[0], "closed", ORIGINAL, "No longer available.")
    assert vacancy_evidence.record(ids[0], "closed", ORIGINAL,
                                   "No longer available.") == evidence_id
    monkeypatch.setattr(search, "manager", search.SearchManager())
    client = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    view = client.get("/api/search/current").json()["search"]
    assert not view["result"]["jobs"]["cards"]
    assert view["result"]["jobs"]["counts"]["left_out"] == [
        {"reason": vacancy_evidence.CLOSED, "count": 1}]
    vacancy_evidence.filter_snapshot(view)  # repeat polling is idempotent
    assert len(view["result"]["jobs"]["counts"]["left_out"]) == 1
    assert jobstore.latest_results()[1] == original
    assert jobstore.states([ids[0]])[ids[0]].saved
    assert jobstore.states([ids[0]])[ids[0]].applied
    annotated = vacancy_evidence.annotate(copy.deepcopy(card))
    assert annotated["state"] == card["state"] and annotated["score"] == 88
    assert annotated["application_link_unavailable"] and not annotated["main_link"]["url"]
    assert client.get("/api/applications/excluded").json()["evidence"][0]["note"]
    path = f"/api/jobs/evidence/{evidence_id}"
    assert client.delete(path).status_code == 403
    assert client.delete(path, headers={"X-Jobcu": "1"}).status_code == 200
    assert client.get("/api/search/current").json()["search"]["result"]["jobs"]["cards"]
    assert client.delete(path, headers={"X-Jobcu": "1"}).status_code == 404
    assert jobstore.latest_results()[1] == original


def test_confirmed_copy_aliases_share_facts_without_matching_another_requisition():
    _, _, ids = saved()
    vacancy_evidence.record(ids[1], "closed", ORIGINAL, "Explicit closure.")
    with db.connect() as conn:
        conn.execute("INSERT INTO job_aliases VALUES (?, ?)", (ids[1], ids[0]))
    assert vacancy_evidence.reasons(ids, NOW) == {
        ids[0]: "verified_closed", ids[1]: "verified_closed"}


def test_verified_old_or_closed_saved_jobs_use_no_routes_scoring_or_online_calls(monkeypatch):
    search_id, groups, ids = saved()
    vacancy_evidence.record(ids[0], "closed", ORIGINAL, "Explicit closure.")
    vacancy_evidence.record(ids[1], "posted_before", ORIGINAL + "1", "At least 80 days old.",
                            posted_before=NOW - timedelta(days=79))
    kept = pool.Pool(search_id, [pool.PoolJob(g, unrelated=False) for g in groups[:2]], PROFILE)
    condition = Condition(text="Near Berlin", understood_as="Near Berlin", status="applied",
                          kind="near", max_minutes=50, anchor=Anchor(description="Berlin",
                          named=[TownRef(name="Berlin", country="DE")]))
    plan = LocationPlan(text="Near Berlin", understood_as="Near Berlin", countries=["DE"],
                        places=[], conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    run = search.SearchRun(search_id, SearchForm(), NOW.isoformat())

    def forbidden(*args, **kwargs):
        pytest.fail("Known old/closed vacancy reached paid work")

    monkeypatch.setattr(travel.TravelMeter, "measure", forbidden)
    monkeypatch.setattr(search.scoring, "score_groups", forbidden)
    monkeypatch.setattr(search.jobplace, "find_online", forbidden)
    client = SimpleNamespace(web_research_unavailable_reason=lambda: "Offline")
    search._decide(run, client, {}, None, Settings(), plan, kept,
                   pipeline.Collected([], [], {}), [], lambda: None)
    assert run.result["jobs"]["counts"]["shown"] == 0
    assert len(run.result["jobs"]["counts"]["left_out"]) == 2


@pytest.mark.parametrize(("kind", "url", "note", "bound"), [
    ("closed", "javascript:void(0)", "Closed", None),
    ("closed", ORIGINAL, "", None),
    ("guessed", ORIGINAL, "Possibly old", None),
    ("posted_before", ORIGINAL, "Missing date", None),
    ("posted_before", ORIGINAL, "Naive date", datetime(2026, 1, 1)),
])
def test_unverified_or_invalid_record_inputs_cannot_exclude_a_job(kind, url, note, bound):
    _, _, ids = saved()
    with pytest.raises(ValueError):
        vacancy_evidence.record(ids[0], kind, url, note, posted_before=bound)
    assert vacancy_evidence.records() == []
