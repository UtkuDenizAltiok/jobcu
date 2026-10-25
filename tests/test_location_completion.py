"""Fictional complete location flows; no provider, owner data or network calls."""

import pytest

from jobcu import travel
from jobcu.dedupe import JobGroup
from jobcu.location import Anchor, Condition
from jobcu.places import Town
from jobcu.settings import Settings
from jobcu.sources.base import FoundJob


def setup_routes(monkeypatch, *, answer=35, incomplete=False):
    towns = [Town(f"City {i}", "DE", 50, 8 + i / 10, 500_000) for i in range(1, 6)]
    monkeypatch.setattr(travel, "anchor_towns", lambda *args: towns)
    point = travel.Point(50, 8, "DE", "address", "Independent Village")
    monkeypatch.setattr(travel, "job_point", lambda group: point)
    condition = Condition(text="Within 50 minutes of a large city", understood_as="…",
                          kind="near", status="estimate", max_minutes=50,
                          travel_mode="transit", anchor=Anchor(min_people=100_000))
    groups = [JobGroup([FoundJob("fictional", str(i), f"https://example.test/{i}", title,
                                country="DE", location_text="Independent Village")])
              for i, title in enumerate(["Power Electronics Engineer", "Nurse", "Teacher"])]
    meter = travel.TravelMeter(None, None, None, Settings())
    calls = []

    def minutes(places, *args, **kwargs):
        calls.append([[t.name for t in ts] for _, ts, _ in places])
        return {p.key: travel.TravelReading(
            {t.name: answer if t.name == "City 3" else 70 for t in ts
             if not incomplete}, {t.name for t in ts} if incomplete else set(),
            dict.fromkeys((t.name for t in ts if not incomplete), travel.MAPS), travel.MAPS)
                for p, ts, _ in places}

    monkeypatch.setattr(meter, "_minutes", minutes)
    return condition, groups, meter, calls, towns


def test_third_city_is_checked_after_two_nearer_cities_fail(monkeypatch):
    condition, groups, meter, calls, _ = setup_routes(monkeypatch)
    meter.measure([condition], groups, [0, 1, 2])
    assert all(travel.answer(condition, g) == "yes" for g in groups)
    assert calls == [[["City 1", "City 2"]], [["City 3", "City 4"]]]
    assert all(condition.travel[travel.job_key(g)]["minutes"]["City 3"] == 35 for g in groups)


def test_complete_negative_measures_every_reachable_city_once(monkeypatch):
    condition, groups, meter, calls, towns = setup_routes(monkeypatch, answer=75)
    meter.measure([condition], groups, [0])
    assert travel.answer(condition, groups[0]) == "no"
    assert sum(len(ts) for request in calls for ts in request) == len(towns)
    meter.measure([condition], groups, [0])
    assert len(calls) == 3  # unchanged complete evidence is free


def test_partial_saved_negative_continues_with_unmeasured_cities_only(monkeypatch):
    condition, groups, meter, calls, _ = setup_routes(monkeypatch)
    point = travel.job_point(groups[0])
    condition.travel[travel.job_key(groups[0])] = {
        "minutes": {"City 1": 70, "City 2": 80}, "point": point.key, "by": travel.MAPS,
        "timing_profile": travel.TRAVEL_TIMING, "routing_version": travel.MAPS_ROUTING_VERSION}
    meter.measure([condition], groups, [0])
    assert travel.answer(condition, groups[0]) == "yes"
    assert calls == [[["City 3", "City 4"]]]
    assert condition.travel[travel.job_key(groups[0])]["minutes"]["City 1"] == 70


def test_failed_round_stops_without_sending_other_alternatives(monkeypatch):
    condition, groups, meter, calls, _ = setup_routes(monkeypatch, incomplete=True)
    meter.measure([condition], groups, [0, 1])
    assert calls == [[["City 1", "City 2"]]]
    assert all(travel.answer(condition, g) == "unknown" for g in groups[:2])


def test_passing_first_round_needs_no_further_routes(monkeypatch):
    condition, groups, meter, calls, _ = setup_routes(monkeypatch)
    old = meter._minutes

    def minutes(*args, **kwargs):
        readings = old(*args, **kwargs)
        for reading in readings.values():
            reading.minutes["City 1"] = 10
        return readings

    monkeypatch.setattr(meter, "_minutes", minutes)
    meter.measure([condition], groups, [0])
    assert travel.answer(condition, groups[0]) == "yes" and len(calls) == 1


@pytest.mark.parametrize("country", ["DE", "IE", "GB", "NL"])
def test_population_threshold_never_rounds_down_a_fractional_person(monkeypatch, country):
    from jobcu.countries import COUNTRIES

    people = 100_000
    share = (people + .25) / COUNTRIES[country].people
    town = Town("Below threshold", country, 50, 8, people)
    monkeypatch.setattr(travel.place_list, "towns_in", lambda _: [town])
    monkeypatch.setattr(travel.place_list, "part_of", lambda _: None)
    assert travel.anchor_towns(Anchor(min_share_of_country=share), country) == []
    from jobcu.location import smallest_town

    assert smallest_town(Condition(text="Size", understood_as="…", kind="town_size",
                                   status="applied", min_share_of_country=share), country) == (
                                       people + 1)


@pytest.mark.parametrize("country", ["DE", "IE", "GB", "NL"])
def test_exact_percentage_boundary_is_not_lost_to_binary_rounding(monkeypatch, country):
    from jobcu.countries import COUNTRIES
    from jobcu.location import smallest_town

    people = COUNTRIES[country].people * 7 // 100
    town = Town("Exactly qualifying city", country, 50, 8, people)
    monkeypatch.setattr(travel.place_list, "towns_in", lambda _: [town])
    monkeypatch.setattr(travel.place_list, "part_of", lambda _: None)
    assert travel.anchor_towns(Anchor(min_share_of_country=.07), country) == [town]
    assert smallest_town(Condition(text="Size", understood_as="…", kind="town_size",
                                   status="applied", min_share_of_country=.07), country) == people


def deferred_plan(monkeypatch, *, copies=1):
    from jobcu import location, reference_places

    towns = [Town("Nearby City", "DE", 50, 8.1, 500_000),
             Town("Unrelated Distant City", "DE", 50, 20, 500_000),
             Town("Small Village", "DE", 50, 8, 3_000)]
    monkeypatch.setattr(travel.place_list, "towns_in", lambda c: towns if c == "DE" else [])
    monkeypatch.setattr(travel.place_list, "part_of", lambda _: None)
    clauses = [location.SortedCondition(
        text=f"Within {30 + i} km of a large city with weekend services", understood_as="…",
        kind="near", max_km=30 + i, anchor=location.SortedAnchor(description="Large cities",
            min_people=100_000, needs_the_web=True, look_up="Weekend services"))
               for i in range(copies)]
    conditions = location._check_sorted_conditions(None, clauses, ["DE"],
                                                   defer_reference_checks=True)
    plan = location.LocationPlan(text="Fictional rule", understood_as="…", countries=["DE"],
                                 places=[], conditions=conditions, not_checked_yet=[],
                                 outside_supported_area=[], broad=False)
    groups = [JobGroup([FoundJob("fictional", "1", "https://example.test/1", "Nurse",
        country="DE", location_text="Small Village", latitude=50, longitude=8)])]
    calls = []

    def check(client, text, towns, **kwargs):
        calls.append([t.name for t in towns])
        retries.append(kwargs.get("retry_unknown"))
        found = reference_places.deferred(text, towns)
        found.status = "applied"
        for city in found.reference_checks:
            city.meets = True
            city.evidence = "Fictional verified city service"
        return found

    retries = []
    monkeypatch.setattr(reference_places, "check", check)
    check.retries = retries
    return plan, groups, calls


def test_city_facts_wait_for_collected_jobs_and_share_reachable_scope(monkeypatch):
    from jobcu import location, reference_places

    plan, groups, calls = deferred_plan(monkeypatch, copies=2)
    assert not calls and not location.condition_warnings(plan)
    assert all(c.anchor.reference_deferred for c in plan.conditions)
    reference_places.resolve_for_jobs(None, plan, groups)
    assert calls == [["Nearby City"]]  # neither villages nor unrelated cities need research
    assert all(travel.answer(c, groups[0]) == "yes" for c in plan.conditions)
    assert all(not c.anchor.reference_deferred for c in plan.conditions)
    reference_places.resolve_for_jobs(None, plan, groups)
    assert len(calls) == 1  # no automatic repetition after the scheduled phase


def test_only_an_asked_for_retry_looks_up_recently_unknown_cities_again(monkeypatch):
    from jobcu import reference_places

    for retry in (False, True):
        plan, groups, _ = deferred_plan(monkeypatch)
        reference_places.resolve_for_jobs(None, plan, groups, retry_unknown=retry)
        assert reference_places.check.retries == [retry]


def test_empty_job_pool_buys_no_city_research(monkeypatch):
    from jobcu import reference_places

    plan, _, calls = deferred_plan(monkeypatch)
    reference_places.resolve_for_jobs(None, plan, [])
    assert not calls


def test_saved_recovery_retains_completed_facts_after_an_interruption(monkeypatch):
    from jobcu import reference_places
    from jobcu.location import ConditionEdit, Source, apply_edits

    plan, groups, calls = deferred_plan(monkeypatch)
    condition = plan.conditions[0]
    condition.anchor.reference_deferred = False
    city = condition.anchor.reference_checks[0]
    city.meets, city.evidence = True, "City service checked during this saved search."
    city.sources = [Source(url="https://example.test/city-services")]
    city.checked_at = "2026-01-01T00:00:00+00:00"
    edit = ConditionEdit(original=0, text=condition.text, check_again=True)
    corrected = apply_edits(None, plan, [edit], defer_reference_checks=True)
    assert not calls and corrected.conditions[0].anchor.reference_deferred
    reference_places.resolve_for_jobs(None, corrected, groups)
    assert not calls and travel.answer(corrected.conditions[0], groups[0]) == "yes"
    assert corrected.conditions[0].anchor.reference_checks[0].checked_at == city.checked_at


def test_unknown_workplace_does_not_broaden_to_every_city(monkeypatch):
    from jobcu import pipeline, reference_places

    plan, groups, calls = deferred_plan(monkeypatch)
    groups[0].main.latitude = groups[0].main.longitude = None
    groups[0].main.location_text = "Unknown workplace"
    reference_places.resolve_for_jobs(None, plan, groups)
    assert not calls and pipeline.unchecked_location_conditions(groups[0], plan)


def test_same_workplace_can_reuse_a_previous_jobs_passing_journey(monkeypatch):
    condition, groups, meter, calls, _ = setup_routes(monkeypatch)
    meter.measure([condition], groups, [0])
    assert len(calls) == 2
    meter.measure([condition], groups, [0, 1])
    assert len(calls) == 2
    assert travel.answer(condition, groups[1]) == "yes"


@pytest.mark.parametrize("reverse", [False, True])
def test_shared_workplace_preserves_maps_over_an_old_ai_estimate(monkeypatch, reverse):
    condition, groups, meter, calls, _ = setup_routes(monkeypatch)
    point = travel.job_point(groups[0])
    common = {"point": point.key, "timing_profile": travel.TRAVEL_TIMING,
              "routing_version": travel.MAPS_ROUTING_VERSION}
    condition.travel[travel.job_key(groups[0])] = {
        **common, "minutes": {"City 1": 70, "City 2": 70}, "by": travel.MAPS}
    condition.travel[travel.job_key(groups[1])] = {
        **common, "minutes": {"City 1": 15, "City 2": 10}, "by": travel.ESTIMATE}
    meter.measure([condition], groups, [1, 0] if reverse else [0, 1])
    for group in groups[:2]:
        entry = condition.travel[travel.job_key(group)]
        assert entry["minutes"]["City 1"] == 70
        assert entry["by_town"]["City 1"] == travel.MAPS
    assert calls == [[["City 3", "City 4"]]]


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Nurse", "Teacher"])
def test_search_checks_full_ad_workplace_then_city_facts_before_scoring(monkeypatch, title):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from test_search import PROFILE

    from jobcu import db, pipeline, pool, reference_places, search
    from jobcu.settings import SearchForm

    plan, groups, calls = deferred_plan(monkeypatch)
    now = datetime.now(UTC)
    groups[0].main.title = title
    groups[0].main.posted_at = now
    groups[0].main.description = "Complete fictional vacancy."
    groups[0].main.description_is_complete = True
    groups[0].main.date_precision = "exact"
    with db.connect() as conn:
        run_id = conn.execute("INSERT INTO searches (status, form_json) "
                              "VALUES ('running', '{}')").lastrowid
    saved_pool = pool.Pool(run_id, [pool.PoolJob(groups[0], unrelated=False)], PROFILE,
                           different_jobs=1)
    run = search.SearchRun(run_id, SearchForm(), now.isoformat())
    phases = []

    def full_ads(*args):
        phases.append("full_ad")
        groups[0].main.longitude = 20  # the original ad corrects the summary's workplace

    original = reference_places.check

    def facts(*args, **kwargs):
        phases.append("city_facts")
        assert phases == ["full_ad", "city_facts"]
        return original(*args, **kwargs)

    def score(client, profile, location, jobs, indexes, **kwargs):
        phases.append("score")
        assert travel.answer(location.conditions[0], jobs[0]) == "yes"
        return {i: {"score": 75, "parts": {}, "required_languages": [], "reasons": []}
                for i in indexes}

    monkeypatch.setattr(pipeline, "load_full_ads", full_ads)
    monkeypatch.setattr(reference_places, "check", facts)
    monkeypatch.setattr(search.scoring, "score_groups", score)
    client = SimpleNamespace(web_research_unavailable_reason=lambda: "Offline test")
    search._decide(run, client, {}, None, Settings(), plan, saved_pool,
                   pipeline.Collected([], [], {}), [], lambda: None)
    assert phases == ["full_ad", "city_facts", "score"]
    assert calls == [["Unrelated Distant City"]]
    assert len(run.result["jobs"]["cards"]) == 1


def test_a_batch_exceeding_remaining_routes_does_not_block_a_smaller_batch():
    from jobcu.sources.budget import BudgetExhausted

    cities = [Town(f"City {i}", "DE", 50, 8 + i / 10, 500_000) for i in range(3)]
    places = [(travel.Point(50, 7, "DE", "address"), cities[:2], ["job-a"]),
              (travel.Point(50, 9, "DE", "address"), cities[2:], ["job-b"])]
    notes, sent = [], []

    class Maps:
        def minutes(self, point, towns, mode, centre):
            elements = len(travel.route_targets(point, towns, centre))
            if elements > 2 - sum(sent):
                raise BudgetExhausted("Remaining allowance cannot cover this batch.")
            sent.append(elements)
            return travel.TravelReading({t.name: 25 for t in towns})

    meter = travel.TravelMeter(None, None, None, Settings(), note=notes.append)
    meter._maps = Maps()
    found = meter._minutes(places, "transit", max_minutes=50)
    assert found[places[1][0].key].minutes == {"City 2": 25}
    assert found[places[0][0].key].unchecked == {"City 0", "City 1"}
    assert sent == [2] and len(notes) == 1
