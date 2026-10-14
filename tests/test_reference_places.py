"""Fictional city services, professions and evidence; no network/provider traffic."""

from dataclasses import replace

import pytest

from jobcu import reference_places, travel
from jobcu.ai.base import AIConnectionError, ResearchReply, Source, Usage
from jobcu.countries import COUNTRIES
from jobcu.dedupe import JobGroup
from jobcu.location import (
    Condition,
    ConditionEdit,
    SortedAnchor,
    SortedCondition,
    TownRef,
    _check_sorted_conditions,
    _corrected_near,
)
from jobcu.places import Town
from jobcu.reference_places import ReferenceAnswer, ReferenceAnswers
from jobcu.sources.base import FoundJob


def anchor(**kwargs):
    return SortedAnchor(**{"description": "Candidate cities", **kwargs})


@pytest.fixture
def cities(monkeypatch):
    towns = [Town(name, "DE", 50, lon, people, ()) for name, lon, people in (
        ("Atlas", 0, 500_000), ("Birch", 3, 400_000), ("Cedar", 6, 300_000),
        ("Smallville", 0.1, 2_000))]
    monkeypatch.setattr(travel.place_list, "towns_in", lambda c: towns if c == "DE" else [])
    monkeypatch.setattr(travel.place_list, "part_of", lambda t: None)
    monkeypatch.setattr(travel.place_list, "find", lambda name, country: next(
        (t for t in towns if t.name == name and t.country == country), None))
    monkeypatch.setattr(travel, "job_point", lambda g: travel.Point(
        g.main.latitude, g.main.longitude, g.main.country, "address", g.main.location_text))
    return towns


class Client:
    def __init__(self, rows=None, *, queries=2, sources=True, fail=False):
        self.rows = rows if rows is not None else [
            ReferenceAnswer(id="C0", meets=True, evidence="The full condition is met.",
                            source_ids=["S0"]),
            ReferenceAnswer(id="C1", meets=False, evidence="The required service is absent.",
                            source_ids=["S0"])]
        self.queries, self.sources, self.fail = queries, sources, fail
        self.calls = []

    def research(self, **request):
        self.calls.append(("research", request))
        if self.fail:
            raise AIConnectionError("Connection interrupted")
        return ResearchReply(
            "CITY C0\nThe full condition is met. Official service register, 2026.\n"
            "CITY C1\nThe required service is absent. Official service register, 2026.\n"
            "CITY C2\nUnknown: the register does not cover this city.",
            [Source("https://example.test/official-register", "Service register")]
            if self.sources else [], Usage(100, 200, web_searches=self.queries))

    def generate(self, output, **request):
        self.calls.append(("structure", request))
        assert output is ReferenceAnswers
        return ReferenceAnswers(cities=self.rows)


def interpreted(client):
    text = "Near a large city with an accessible public library"
    (condition,) = _check_sorted_conditions(client, [SortedCondition(
        text=text, understood_as=text, kind="near", max_km=20,
        anchor=anchor(description="large cities", min_people=100_000,
                            needs_the_web=True, look_up="an accessible public library"))], ["DE"])
    return condition


def job(town, profession="Nurse"):
    return JobGroup(copies=[FoundJob(
        source="fictional", source_job_id=f"{town.name}-{profession}",
        url="https://example.test/vacancy", title=profession, company="Fictional Hospital",
        country=town.country, location_text=town.name, latitude=town.latitude,
        longitude=town.longitude)])


@pytest.mark.parametrize("profession", ["Power electronics engineer", "Nurse", "Teacher"])
def test_partial_answers_preserve_supported_cities_without_accepting_omissions(cities, profession):
    client = Client()
    condition = interpreted(client)
    assert [c.meets for c in condition.anchor.reference_checks] == [True, False, None]
    assert travel.answer(condition, job(cities[0], profession)) == "yes"
    assert travel.answer(condition, job(cities[1], profession)) == "no"
    assert travel.answer(condition, job(cities[2], profession)) == "unknown"
    assert travel.answer(condition, job(cities[3], profession)) == "yes"  # small workplace
    assert len(client.calls) == 2
    request = client.calls[0][1]
    assert "Atlas" in request["prompt"] and "Smallville" not in request["prompt"]
    assert request["max_searches"] == 4
    assert condition.anchor.reference_checks[0].sources[0].url.endswith("official-register")


@pytest.mark.parametrize("code", list(COUNTRIES))
def test_candidate_population_thresholds_use_each_countrys_local_arithmetic(monkeypatch, code):
    people = COUNTRIES[code].people
    threshold = round(people * 0.01)
    towns = [Town("Large", code, 50, 0, threshold, ()),
             Town("Small", code, 50, 1, threshold - 1, ())]
    monkeypatch.setattr(travel.place_list, "towns_in", lambda c: towns)
    monkeypatch.setattr(travel.place_list, "part_of", lambda t: None)
    chosen = reference_places.candidates(anchor(min_share_of_country=0.01), [code])
    assert [t.name for t in chosen] == ["Large"]


def test_named_and_size_rules_intersect_and_unknown_names_keep_open_ended_research(cities):
    assert reference_places.candidates(anchor(
        named=[TownRef(name="Smallville", country="DE")], min_people=100_000), ["DE"]) == []
    assert reference_places.candidates(anchor(
        named=[TownRef(name="Unlisted", country="DE")]), ["DE"]) is None
    assert reference_places.candidates(anchor(needs_the_web=True), ["DE"]) is None


def test_no_candidate_needs_no_paid_research_and_large_lists_are_not_truncated(cities, monkeypatch):
    client = Client()
    condition = reference_places.check(client, "A required city service", [])
    assert condition.status == "applied" and condition.reference_checks == [] and not client.calls
    monkeypatch.setattr(travel.place_list, "towns_in", lambda c: [
        replace(cities[0], name=f"City{i}") for i in range(401)])
    assert reference_places.candidates(anchor(min_people=100_000), ["DE"]) is None


@pytest.mark.parametrize("change", ["missing_source", "foreign_excerpt", "duplicate", "unknown_id"])
def test_unsupported_or_ambiguous_city_answers_stay_unknown(cities, change):
    row = ReferenceAnswer(id="C0", meets=True, evidence="The full condition is met.",
                          source_ids=["S0"])
    rows = [row]
    if change == "missing_source":
        row.source_ids = ["invented"]
    elif change == "foreign_excerpt":
        row.evidence = "The required service is absent."  # belongs to C1
    elif change == "duplicate":
        rows.append(row.model_copy(update={"meets": False}))
    else:
        row.id = "C99"
    result = reference_places.check(Client(rows), "City service", cities[:3])
    assert all(c.meets is None for c in result.reference_checks)
    assert result.status == "not_checked"


@pytest.mark.parametrize(("queries", "sources"), [(0, True), (2, False)])
def test_memory_answers_or_missing_citations_skip_structure(cities, queries, sources):
    client = Client(queries=queries, sources=sources)
    result = reference_places.check(client, "City service", cities[:3])
    assert result.status == "not_checked"
    assert [kind for kind, _ in client.calls] == ["research"]


def test_failed_research_remains_unknown_and_a_later_check_is_fresh(cities):
    assert reference_places.check(Client(fail=True), "City service", cities[:3]).status == (
        "not_checked")
    client = Client()
    reference_places.check(client, "City service", cities[:3])
    reference_places.check(client, "City service", cities[:3])
    assert [kind for kind, _ in client.calls].count("research") == 2


def test_unknown_alternative_prevents_false_exclusion_but_not_a_supported_pass(cities):
    condition = interpreted(Client())
    condition.max_minutes, condition.max_km = 50, None
    group = job(cities[2])
    condition.travel[travel.job_key(group)] = {"minutes": {"Atlas": 90}, "by": "Google Maps"}
    assert travel.answer(condition, group) == "unknown"
    condition.travel[travel.job_key(group)]["minutes"]["Atlas"] = 40
    assert travel.answer(condition, group) == "yes"
    condition.travel[travel.job_key(group)]["minutes"] = {"Birch": 0}  # stale/ineligible
    assert travel.answer(condition, group) == "unknown"


def test_widening_size_does_not_invent_facts_and_limit_only_edits_keep_checks(cities):
    condition = interpreted(Client())
    corrected = _corrected_near(condition, ConditionEdit(
        original=0, text=condition.text, min_people=1_000), ["DE"])
    assert "Smallville" in {t.name for t in travel.unchecked_reference_towns(
        corrected.anchor, "DE")}
    assert corrected.anchor.reference_checks == condition.anchor.reference_checks
    assert Condition.model_validate_json(corrected.model_dump_json()) == corrected


def test_standalone_condition_does_not_reuse_partial_reference_scope(cities, monkeypatch):
    from jobcu import location

    calls = []

    def broad(client, text, names, countries):
        calls.append(text)
        return Condition(text=text, understood_as=text, kind="could_not_check",
                         status="not_checked")

    monkeypatch.setattr(location, "_research_condition", broad)
    text = "an accessible public library"
    conditions = [SortedCondition(text=text, understood_as=text, kind="needs_the_web"),
                  SortedCondition(
        text="Near a library city", understood_as="Near a library city", kind="near", max_km=20,
        anchor=anchor(min_people=100_000, needs_the_web=True, look_up=text))]
    _check_sorted_conditions(Client(), conditions, ["DE"])
    assert calls == [text]


def test_same_fact_and_different_size_rules_share_one_complete_candidate_request(cities):
    fact = "an accessible public library"
    conditions = [SortedCondition(
        text=f"Within {size} km of a library city", understood_as="Near a library city",
        kind="near", max_km=size, anchor=anchor(min_people=minimum,
                                              needs_the_web=True, look_up=fact))
        for size, minimum in [(20, 450_000), (40, 100_000)]]
    client = Client()
    checked = _check_sorted_conditions(client, conditions, ["DE"])
    assert len(client.calls) == 2
    assert "Cedar" in client.calls[0][1]["prompt"]
    assert checked[0].anchor.reference_checks == checked[1].anchor.reference_checks
    assert [t.name for t in travel.anchor_towns(checked[0].anchor, "DE")] == ["Atlas"]


def test_complete_research_survives_later_structure_failure(cities):
    class BrokenStructure(Client):
        def generate(self, *args, **kwargs):
            raise AIConnectionError("Connection interrupted while organizing the notes")

    condition = interpreted(BrokenStructure())
    assert condition.reference_status == "not_checked"
    assert "CITY C0\nThe full condition is met." in condition.anchor.reference_notes
    assert condition.sources[0].url.endswith("official-register")
    assert Condition.model_validate_json(condition.model_dump_json()) == condition


def test_only_verified_reference_destinations_can_trigger_routes(cities):
    from jobcu.keystore import KeyStore
    from jobcu.settings import Settings

    class NoPaidCalls:
        def generate(self, *args, **kwargs):
            pytest.fail("Unknown or ineligible reference cities must not trigger route estimates")

    condition = interpreted(Client())
    condition.max_minutes, condition.max_km = 5, None
    groups = [job(town) for town in cities[:3]]
    travel.TravelMeter(NoPaidCalls(), KeyStore(), None, Settings()).measure(
        [condition], groups, [0, 1, 2])
    assert [travel.answer(condition, group) for group in groups] == ["yes", "no", "unknown"]


def test_same_named_cities_keep_separate_facts_and_coordinates(cities):
    cities[1] = replace(cities[1], name=cities[0].name)
    client = Client()
    condition = interpreted(client)
    assert [t.longitude for t in travel.anchor_towns(condition.anchor, "DE")] == [0]
    assert travel.answer(condition, job(cities[0])) == "yes"
    assert travel.answer(condition, job(cities[1])) == "no"
    assert "coordinates 50, 3" in client.calls[0][1]["prompt"]


@pytest.mark.parametrize("evidence", ["Value < 20%", "Value 20%", "Value > 20%"])
def test_excerpt_validation_preserves_numerical_comparison_operators(cities, evidence):
    class Numbers(Client):
        def research(self, **request):
            return ResearchReply("CITY C0\nValue > 20%", [Source("https://example.test/table")],
                                 Usage(web_searches=1))

    result = reference_places.check(Numbers([ReferenceAnswer(
        id="C0", meets=False, evidence=evidence, source_ids=["S0"])]),
        "A numerical service threshold", cities[:1])
    assert result.reference_checks[0].meets is (False if evidence == "Value > 20%" else None)
