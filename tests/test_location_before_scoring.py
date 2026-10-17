"""Only qualifying workplaces enter scoring; all evidence here is fictional and offline."""

from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from test_search import PROFILE

from jobcu import db, pipeline, pool, search, travel
from jobcu.dedupe import JobGroup
from jobcu.location import Anchor, Condition, LocationPlan, TownRef
from jobcu.places import Town
from jobcu.settings import SearchForm, Settings
from jobcu.sources.base import FoundJob


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Nurse", "Primary Teacher"])
@pytest.mark.parametrize("rule", ["0.3%", "1%", "top five"])
def test_custom_city_rules_gate_scoring_without_dropping_unresolved_jobs(monkeypatch, title, rule):
    now = datetime.now(UTC)
    city = Town("Fictional Major City", "DE", 50, 9, 2_000_000)
    anchor = (Anchor(description=rule, named=[TownRef(name=city.name, country="DE")])
              if rule == "top five" else Anchor(description=rule,
                    min_share_of_country=.003 if rule == "0.3%" else .01))
    condition = Condition(text=f"Within 50 minutes of {rule} cities", understood_as=rule,
                          status="applied", kind="near", max_minutes=50, anchor=anchor)
    plan = LocationPlan(text=rule, understood_as=rule, countries=["DE"], places=[],
                        conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    groups = [JobGroup([FoundJob("fictional", str(i), f"https://jobs.example.test/{i}", title,
              company=f"Example {i}", location_text="Independent Village", country="DE",
              latitude=50, longitude=8.9, posted_at=now, date_precision="exact",
              description="Full fictional vacancy evidence.", description_is_complete=True)])
              for i in range(3)]
    jobs = [pool.PoolJob(g, unrelated=False) for g in groups]
    with db.connect() as conn:
        run_id = conn.execute("INSERT INTO searches (status, form_json) "
                              "VALUES ('running', '{}')").lastrowid
    saved_pool = pool.Pool(run_id, jobs, PROFILE, different_jobs=3)
    run = search.SearchRun(run_id, SearchForm(), now.isoformat())
    scored = []

    class Meter:
        def __init__(self, *args, **kwargs):
            pass

        def measure(self, conditions, measured_groups, indexes):
            assert conditions[0].anchor == anchor  # consume this user's interpreted rule
            for i in indexes:
                condition.travel[travel.job_key(measured_groups[i])] = {
                    "minutes": {city.name: 30 if i == 0 else 75} if i != 2 else {},
                    "by": travel.MAPS, "unchecked": i == 2}

    def score(client, profile, location, scoring_groups, indexes, **kwargs):
        scored.extend(indexes)
        return {i: {"score": 75, "parts": {}, "required_languages": [], "reasons": []}
                for i in indexes}

    monkeypatch.setattr(travel, "TravelMeter", Meter)
    monkeypatch.setattr(travel, "anchor_towns", lambda a, country: [city])
    monkeypatch.setattr(search.scoring, "score_groups", score)
    client = SimpleNamespace(web_research_unavailable_reason=lambda: "Offline test")
    search._decide(run, client, {}, None, Settings(), plan, saved_pool,
                   pipeline.Collected([], [], {}), [], lambda: None)
    assert scored == [0]  # neither the proven failure nor the unknown used scoring
    result = run.result["jobs"]
    assert len(result["cards"]) == len(result["location_unchecked"]) == 1
    pending = result["location_unchecked"][0]
    assert pending["score"] is None and pending["parts"] is None
    assert any(check["status"] == "unclear" for check in pending["location_checks"])
    assert result["counts"]["location_unchecked"] == 1
    assert len(result["ruled_out_by_conditions"]) == 1
    assert len(pool.load(run_id).jobs) == 3  # retry/edit can still recover every candidate

    # Resolving evidence on the same retained pool scores only the formerly pending job.
    saved_pool.jobs[2].group.copies[0].longitude = 8.91
    old_measure = Meter.measure

    def resolved(self, conditions, measured_groups, indexes):
        old_measure(self, conditions, measured_groups, indexes)
        condition.travel[travel.job_key(groups[2])] = {
            "minutes": {city.name: 25}, "by": travel.MAPS}

    monkeypatch.setattr(Meter, "measure", resolved)
    search._decide(run, client, {}, None, Settings(), plan, saved_pool,
                   pipeline.Collected([], [], {}), [], lambda: None)
    assert scored == [0, 2]
    assert not run.result["jobs"]["location_unchecked"]
    assert len(run.result["jobs"]["cards"]) == 2


def test_unread_or_disabled_conditions_do_not_silently_bypass_or_keep_the_gate():
    job = JobGroup([FoundJob("fictional", "1", "https://jobs.example.test/1", "Nurse")])
    condition = Condition(text="A custom condition", understood_as="A custom condition",
                          status="not_checked", kind="could_not_check")
    plan = LocationPlan(text="Custom location", understood_as="…", countries=["DE"], places=[],
                        conditions=[condition],
                        not_checked_yet=[], outside_supported_area=[], broad=False)
    assert pipeline.unchecked_location_conditions(job, plan)
    condition.switched_off = True
    assert not pipeline.unchecked_location_conditions(job, plan)
    plan.not_checked_yet = ["An uninterpreted location condition"]
    assert pipeline.unchecked_location_conditions(job, plan)


def test_saved_score_with_unknown_location_is_only_reclassified_in_the_response():
    saved = {"result": {"location": {"conditions": [
        {"kind": "near", "status": "applied", "switched_off": False}]}, "jobs": {
        "cards": [{"job_id": 1, "score": 88, "parts": {"role_and_skills": 36},
                   "location_checks": [{"status": "unclear"}]}], "date_unknown": [],
        "counts": {"shown": 1}}}}
    shown = deepcopy(saved)
    pipeline.location_gate_view(shown)
    pipeline.location_gate_view(shown)  # polling must be idempotent
    assert not shown["result"]["jobs"]["cards"]
    pending = shown["result"]["jobs"]["location_unchecked"]
    assert len(pending) == 1 and pending[0]["score"] is None
    assert saved["result"]["jobs"]["cards"][0]["score"] == 88


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Ward Nurse", "Primary Teacher"])
def test_conflicting_workplaces_use_no_scoring_research_or_routes(monkeypatch, title):
    now = datetime.now(UTC)
    condition = Condition(text="Near Berlin", understood_as="Within 50 minutes of Berlin",
                          status="applied", kind="near", max_minutes=50,
                          anchor=Anchor(description="Berlin",
                                        named=[TownRef(name="Berlin", country="DE")]))
    plan = LocationPlan(text="Near Berlin", understood_as="Near Berlin", countries=["DE"],
                        places=[], conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    group = JobGroup([FoundJob("fictional", "1", "https://jobs.example.test/1", title,
                     company="Fictional Employer", location_text="Berlin", country="DE",
                     latitude=52.52, longitude=13.405, description="Workplace: Munich",
                     posted_at=now, date_precision="exact", description_is_complete=True)],
                     place_from_text=["Munich"])
    with db.connect() as conn:
        run_id = conn.execute("INSERT INTO searches (status, form_json) "
                              "VALUES ('running', '{}')").lastrowid
    saved_pool = pool.Pool(run_id, [pool.PoolJob(group, unrelated=False)], PROFILE)
    run = search.SearchRun(run_id, SearchForm(), now.isoformat())

    def forbidden(*args, **kwargs):
        pytest.fail("Conflicting workplace used a scoring, research or route request")

    monkeypatch.setattr(search.scoring, "score_groups", forbidden)
    monkeypatch.setattr(search.jobplace, "find_online", forbidden)
    monkeypatch.setattr(travel.TravelMeter, "_minutes", forbidden)
    client = SimpleNamespace(web_research_unavailable_reason=lambda: None)
    search._decide(run, client, {}, None, Settings(), plan, saved_pool,
                   pipeline.Collected([], [], {}), [], lambda: None)
    pending = run.result["jobs"]["location_unchecked"]
    assert len(pending) == 1 and pending[0]["score"] is None
    assert any("different workplaces" in c["label"] for c in pending[0]["location_checks"])
    assert not run.result["jobs"]["cards"]
    assert condition.travel == {} and travel.job_point(group) is None


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Ward Nurse", "Physics Teacher"])
def test_saved_requirement_retry_runs_only_after_current_location_admission(monkeypatch, title):
    from test_recheck import PERSON, check, saved

    now = datetime.now(UTC)
    city = Town("Fictional Major City", "DE", 50, 9, 2_000_000)
    condition = Condition(text="Near a major city", understood_as="Within 50 minutes",
                          status="applied", kind="near", max_minutes=50,
                          anchor=Anchor(description="a large city", min_share_of_country=.003))
    plan = LocationPlan(text="Near a city", understood_as="Near a city", countries=["DE"],
                        places=[], conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    jobs = [saved([check("unclear")]) for _ in range(3)]
    for i, job in enumerate(jobs):
        copy = job.group.copies[0]
        copy.source_job_id = str(i)
        copy.title, copy.location_text = title, "Fictional Village"
        copy.latitude, copy.longitude = 50, 8.9
        copy.posted_at, copy.date_precision = now, "exact"
    with db.connect() as conn:
        run_id = conn.execute("INSERT INTO searches (status, form_json) "
                              "VALUES ('running', '{}')").lastrowid
    kept = pool.Pool(run_id, jobs, PERSON.model_dump())
    run = search.SearchRun(run_id, SearchForm(), now.isoformat())
    run.steps.append(search.Step("requirements", "Rechecking requirements"))
    compared = []

    class Meter:
        def __init__(self, *args, **kwargs):
            pass

        def measure(self, conditions, groups, indexes):
            for i in indexes:
                condition.travel[travel.job_key(groups[i])] = {
                    "minutes": {city.name: 30 if i == 0 else 75} if i != 2 else {},
                    "by": travel.MAPS, "unchecked": i == 2}

    def compare(client, job, profile):
        assert travel.answer(condition, job.group) == "yes"
        compared.append(job.group.main.source_job_id)
        return True

    monkeypatch.setattr(travel, "TravelMeter", Meter)
    monkeypatch.setattr(travel, "anchor_towns", lambda *args: [city])
    monkeypatch.setattr(search, "_checkpoint", lambda *args: None)
    monkeypatch.setattr("jobcu.recheck.compare", compare)
    monkeypatch.setattr(search.scoring, "score_groups", lambda *args, **kw: pytest.fail(
        "The existing assessment must be reused"))
    client = SimpleNamespace(parallel_requests=1,
                             web_research_unavailable_reason=lambda: "Offline test")
    search._decide(run, client, {}, None, Settings(), plan, kept,
                   pipeline.Collected([], [], {}), [], lambda: None, retry_requirements=True)
    assert compared == ["0"]  # not the failed or unchecked location, even on explicit retry
    assert len(run.result["jobs"]["location_unchecked"]) == 1
