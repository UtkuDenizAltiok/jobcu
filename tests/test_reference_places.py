"""Fictional city services, professions and evidence; no network/provider traffic."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from jobcu import reference_places, travel
from jobcu.ai.base import AIConnectionError, AIRefused, Citation, ResearchReply, Source, Usage
from jobcu.countries import COUNTRIES
from jobcu.dedupe import JobGroup
from jobcu.location import (
    Condition,
    ConditionEdit,
    ReferenceCheck,
    SortedAnchor,
    SortedCondition,
    TownRef,
    _check_sorted_conditions,
    _corrected_near,
    apply_edits,
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


@pytest.mark.parametrize("mapped", [True, False])
def test_provider_links_disambiguate_same_title_sources_and_cannot_cross_cities(cities, mapped):
    class Annotated(Client):
        def research(self, **request):
            reply = super().research(**request)
            reply.sources = [Source("https://example.test/opaque-a", "example.test"),
                             Source("https://example.test/opaque-b", "example.test")]
            reply.citations = ([
                Citation("The full condition is met.", reply.sources[0].url),
                Citation("The required service is absent.", reply.sources[1].url)]
                if mapped else [])
            return reply

    client = Annotated(rows=[
        ReferenceAnswer(id="C0", meets=True, evidence="The full condition is met.",
                        source_ids=["S1"]),  # another city's source cannot validate it
        ReferenceAnswer(id="C1", meets=False, evidence="The required service is absent.",
                        source_ids=["S1"])])
    found = reference_places.check(client, "Fictional city service", cities[:2])
    assert [c.meets for c in found.reference_checks] == [None, False if mapped else None]
    if mapped:
        prompt = client.calls[1][1]["prompt"]
        assert "Provider-linked source IDs per CITY" in prompt
        assert '"C0": ["S0"]' in prompt
    else:
        assert len(client.calls) == 1  # no extraction can recover absent passage links


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


@pytest.mark.parametrize("profession", ["Power electronics engineer", "Nurse", "Teacher"])
@pytest.mark.parametrize("fail_middle", [False, True])
def test_bounded_groups_preserve_all_candidates_and_each_groups_own_evidence(
        cities, profession, fail_middle):
    towns = [replace(cities[0], name=f"Fictional City {i}") for i in range(19)]

    class Groups(Client):
        def __init__(self):
            super().__init__()
            self.group, self.progress = 0, []
            self.on_progress = self.progress.append

        def research(self, **request):
            self.group += 1
            if fail_middle and self.group == 2:
                self.calls.append(("research", request))
                raise AIRefused("This group could not be checked")
            reply = super().research(**request)
            reply.sources[0].url += f"/{self.group}"
            return reply

    client = Groups()
    result = reference_places.check(client, f"City service for a fictional {profession}", towns)
    assert [c.name for c in result.reference_checks] == [town.name for town in towns]
    requests = [request for kind, request in client.calls if kind == "research"]
    assert len(requests) == 3
    assert all(len(request["prompt"].split("Reference cities:\n")[1].splitlines()) <= 8
               for request in requests)
    for start, group in ((0, 1), (8, 2), (16, 3)):
        checks = result.reference_checks[start:start + 8]
        if fail_middle and group == 2:
            assert all(c.meets is None for c in checks)
        else:
            assert checks[0].meets is True and checks[1].meets is False
            assert all(c.meets is None for c in checks[2:])
            assert checks[0].sources[0].url.endswith(f"/{group}")
    assert len(client.progress) == 3


def test_connection_exhaustion_keeps_checked_groups_and_does_not_multiply_paid_attempts(cities):
    towns = [replace(cities[0], name=f"Fictional City {i}") for i in range(19)]

    class InterruptedGroup(Client):
        def research(self, **request):
            if self.calls:
                self.calls.append(("research", request))
                raise AIConnectionError("Connection retry allowance exhausted")
            return super().research(**request)

    client = InterruptedGroup()
    result = reference_places.check(client, "A required public library service", towns)
    assert len(result.reference_checks) == len(towns)
    assert result.reference_checks[0].meets is True
    assert result.reference_checks[1].meets is False
    assert all(c.meets is None for c in result.reference_checks[8:])
    assert [kind for kind, _ in client.calls].count("research") == 2
    assert "Remaining reference-city groups were not sent" in result.note


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


@pytest.mark.parametrize("profession", ["Power electronics engineer", "Nurse", "Teacher"])
def test_retry_keeps_recent_supported_facts_and_only_researches_unknown_cities(cities, profession):
    condition = interpreted(Client())
    condition.travel = {"fictional:job": {"minutes": {"Atlas": 12}}}
    client = Client(rows=[ReferenceAnswer(id="C0", meets=True,
                                          evidence="The full condition is met.",
                                          source_ids=["S0"])])
    updated = reference_places.retry_missing(client, condition, ["DE"])
    assert [c.meets for c in updated.anchor.reference_checks] == [True, False, True]
    assert updated.anchor.reference_checks[:2] == condition.anchor.reference_checks[:2]
    request = client.calls[0][1]["prompt"].split("Reference cities:\n")[1]
    assert "Cedar" in request and "Atlas" not in request and "Birch" not in request
    assert updated.travel == {}  # new eligible destinations invalidate an old aggregate result
    assert travel.answer(updated, job(cities[2], profession)) == "yes"
    assert condition.anchor.reference_checks[2].meets is None  # input snapshot untouched


def test_failed_retry_preserves_recent_evidence_and_unchanged_travel(cities):
    condition = interpreted(Client())
    condition.travel = {"fictional:job": {"minutes": {"Atlas": 12}}}
    updated = reference_places.retry_missing(Client(fail=True), condition, ["DE"])
    assert updated.anchor.reference_checks[:2] == condition.anchor.reference_checks[:2]
    assert updated.travel == condition.travel
    assert updated.anchor.reference_checks[2].meets is None
    assert "Connection interrupted" in updated.note
    assert updated.sources == condition.sources


def test_check_again_uses_the_saved_interpretation_and_keeps_size_and_time_edits(cities):
    from jobcu.location import LocationPlan

    condition = interpreted(Client())
    plan = LocationPlan(text=condition.text, understood_as=condition.text, countries=["DE"],
                        broad=True, places=[], conditions=[condition], not_checked_yet=[],
                        conditions_about_the_job=[], outside_supported_area=[])
    client = Client()
    updated = apply_edits(client, plan, [ConditionEdit(
        original=0, text=condition.text, check_again=True, max_km=25)]).conditions[0]
    assert updated.max_km == 25
    assert updated.anchor.reference_checks[0] == condition.anchor.reference_checks[0]
    assert [kind for kind, _ in client.calls] == ["research", "structure"]


@pytest.mark.parametrize("stamp", [None, "2020-01-01T00:00:00+00:00", "invalid",
                                   "2026-10-01T00:00:00", "2999-01-01T00:00:00+00:00"])
def test_retry_does_not_reuse_legacy_expired_or_future_dated_proof(cities, stamp):
    condition = interpreted(Client())
    _forget_reused_facts()  # only the condition's own stamps are under test here
    for city in condition.anchor.reference_checks:
        city.checked_at = stamp
    client = Client()
    reference_places.retry_missing(client, condition, ["DE"])
    request = client.calls[0][1]["prompt"].split("Reference cities:\n")[1]
    assert all(town.name in request for town in cities[:3])


def test_widening_size_does_not_invent_facts_and_limit_only_edits_keep_checks(cities):
    condition = interpreted(Client())
    corrected = _corrected_near(condition, ConditionEdit(
        original=0, text=condition.text, min_people=1_000), ["DE"])
    assert "Smallville" in {t.name for t in travel.unchecked_reference_towns(
        corrected.anchor, "DE")}
    assert corrected.anchor.reference_checks == condition.anchor.reference_checks
    assert Condition.model_validate_json(corrected.model_dump_json()).model_dump() == (
        corrected.model_dump())


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


def test_complete_research_is_available_in_flight_without_hidden_persistent_storage(cities):
    class BrokenStructure(Client):
        def generate(self, *args, **kwargs):
            raise AIConnectionError("Connection interrupted while organizing the notes")

    condition = interpreted(BrokenStructure())
    assert condition.reference_status == "not_checked"
    assert "CITY C0\nThe full condition is met." in condition.anchor.reference_notes
    assert condition.sources[0].url.endswith("official-register")
    restored = Condition.model_validate_json(condition.model_dump_json())
    assert "reference_notes" not in condition.model_dump_json()
    assert restored.anchor.reference_notes == ""
    assert restored.anchor.reference_checks == condition.anchor.reference_checks
    assert restored.sources == condition.sources


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


@pytest.mark.parametrize('profession', ['Hardware engineer', 'Nurse', 'Teacher'])
def test_missing_model_source_ids_use_provider_links_covering_the_decisive_excerpt(
        cities, profession):
    class Linked(Client):
        def research(self, **request):
            reply = super().research(**request)
            reply.citations = [Citation(
                'CITY C0\nThe full condition is met.', reply.sources[0].url)]
            return reply

    client = Linked(rows=[ReferenceAnswer(id='C0', meets=True,
        evidence='The full condition is met.', source_ids=[])])
    found = reference_places.check(client, f'City service for a {profession}', cities[:2])
    assert [c.meets for c in found.reference_checks] == [True, None]
    assert found.reference_checks[0].sources[0].url.endswith('official-register')
    assert len(client.calls) == 2  # research + structure; no repair/repeated research


@pytest.mark.parametrize('passage', [
    'The full condition',  # only part of the decisive excerpt
    'CITY C1\nThe required service is absent.',  # another city
    'CITY C0\nThe full condition is met.\nCITY C1\nThe required service is absent.',
    '',
])
def test_recovered_ids_require_full_decisive_excerpt_in_one_city_block(cities, passage):
    class Linked(Client):
        def research(self, **request):
            reply = super().research(**request)
            reply.citations = [Citation(passage, reply.sources[0].url)] if passage else []
            return reply

    found = reference_places.check(Linked(rows=[ReferenceAnswer(id='C0', meets=True,
        evidence='The full condition is met.', source_ids=[])]), 'City service', cities[:2])
    assert all(c.meets is None for c in found.reference_checks)


class CachedClient(Client):
    def __init__(self, cache=None, search_id=42):
        from jobcu.settings import Settings

        super().__init__()
        self.reference_research_cache = {} if cache is None else cache
        self.search_id = search_id
        self.settings = Settings()
        self.settings.ai.provider = 'gemini'
        self.settings.ai.model = 'fictional-model'
        self.provider_id = 'gemini'

    def model_for(self, reasoning):
        return self.settings.ai.model


def test_conversion_failure_keeps_complete_web_answer_for_same_search_recovery(cities):
    class Interrupted(CachedClient):
        def generate(self, output, **request):
            if not any(kind == 'structure' for kind, _ in self.calls):
                self.calls.append(('structure', request))
                raise AIConnectionError('Fictional conversion interruption')
            return super().generate(output, **request)

    client = Interrupted()
    first = reference_places.check(client, 'City service', cities[:2])
    second = reference_places.check(client, 'City service', cities[:2])
    assert all(c.meets is None for c in first.reference_checks)
    assert [c.meets for c in second.reference_checks] == [True, False]
    assert [kind for kind, _ in client.calls].count('research') == 1
    assert [kind for kind, _ in client.calls].count('structure') == 2
    assert 'reference_research_cache' not in second.model_dump_json()


@pytest.mark.parametrize('change', [
    'search', 'model', 'effort', 'host', 'fact', 'cities', 'expiry'])
def test_transient_web_reuse_is_bound_to_search_route_fact_scope_and_age(cities, change):
    class Unconverted(CachedClient):
        def generate(self, output, **request):
            raise AIConnectionError('Fictional conversion failure')

    client = Unconverted()
    reference_places.check(client, 'City service', cities[:2])
    assert client.reference_research_cache
    next_client = CachedClient(client.reference_research_cache)
    fact, scope = 'City service', cities[:2]
    if change == 'search':
        next_client.search_id += 1
    elif change == 'model':
        next_client.settings.ai.model = 'different-fictional-model'
    elif change == 'effort':
        next_client.settings.ai.reasoning_effort = 'high'
    elif change == 'host':
        next_client.settings.ai.base_url = 'https://different.example.test'
    elif change == 'fact':
        fact += ' changed'
    elif change == 'cities':
        scope = cities[:1]
    else:
        for key, (stamp, reply) in list(client.reference_research_cache.items()):
            client.reference_research_cache[key] = (stamp - 3700, reply)
    reference_places.check(next_client, fact, scope)
    assert [kind for kind, _ in next_client.calls].count('research') == 1


def test_incomplete_usage_does_not_seed_reference_recovery(cities):
    class Incomplete(CachedClient):
        def research(self, **request):
            reply = super().research(**request)
            reply.usage.unreported_requests = 1
            return reply

    client = Incomplete()
    reference_places.check(client, 'City service', cities[:2])
    _forget_reused_facts()  # isolate same-search recovery from cross-search reuse
    reference_places.check(client, 'City service', cities[:2])
    assert not client.reference_research_cache
    assert [kind for kind, _ in client.calls].count('research') == 2


def test_compact_source_hints_preserve_every_note_and_validate_the_same_mapping(cities):
    from jobcu.ai.base import Source

    notes = 'CITY C0\nThe full condition is met.\nCITY C1\nThe service is absent.'
    sources = {'S0': Source('https://example.test/opaque-' + 'x' * 5000, 'Official A'),
               'S1': Source('https://example.test/opaque-' + 'y' * 5000, 'Official B')}
    links = {'S0': ['The full condition is met.'], 'S1': ['The service is absent.']}
    prompt = reference_places._structure_prompt('City service', ['C0 | Atlas', 'C1 | Birch'],
                                               notes, sources, links)
    assert notes in prompt
    assert '"C0": ["S0"]' in prompt and '"C1": ["S1"]' in prompt
    assert all(url.url not in prompt for url in sources.values())
    assert 'Official A' in prompt and 'Official B' in prompt
    assert len(prompt) < 1000


def test_search_snapshot_never_serializes_transient_grounded_answers():
    from jobcu.search import SearchRun
    from jobcu.settings import SearchForm

    run = SearchRun(1, SearchForm(), '2026-10-16T10:00:00+00:00',
                    reference_research_cache={'private-answer': object()})
    assert 'private-answer' not in str(run.snapshot())
    assert 'reference_research_cache' not in run.snapshot()


@pytest.mark.parametrize('unknown', [True, False])
def test_completed_conversion_retires_web_answer_even_when_city_facts_remain_unknown(
        cities, unknown):
    client = CachedClient()
    if unknown:
        client.rows = []
    reference_places.check(client, 'City service', cities[:2])
    assert not client.reference_research_cache
    later = reference_places.check(client, 'City service', cities[:2])
    # Verified city facts are reused by the next check. Unknown ones rest for a week rather
    # than buying the same failed research in every search; an explicit retry looks again.
    assert [kind for kind, _ in client.calls].count('research') == 1
    if unknown:
        assert all(c.meets is None and c.evidence.startswith('Looked up on ')
                   for c in later.reference_checks)
        assert 'not bought again' in later.note
        reference_places.check(client, 'City service', cities[:2], retry_unknown=True)
        assert [kind for kind, _ in client.calls].count('research') == 2


def test_a_provider_link_on_only_a_city_heading_cannot_support_its_claim(cities):
    class HeadingOnly(Client):
        def research(self, **request):
            reply = super().research(**request)
            reply.citations = [Citation('CITY C0', reply.sources[0].url)]
            return reply

    client = HeadingOnly()
    found = reference_places.check(client, 'City service', cities[:2])
    assert all(c.meets is None for c in found.reference_checks)
    assert len(client.calls) == 1


def test_reviewed_request_matching_needs_one_unedited_reference_fact():
    from jobcu.location import Anchor, Condition, LocationPlan

    def near(fact):
        return Condition(text="Within 30 minutes of a fictional kind of city", understood_as="",
                         status="estimate", kind="near", max_minutes=30,
                         anchor=Anchor(look_up=fact))

    plan = LocationPlan(text="A fictional request", understood_as="", countries=["DE"],
                        places=[], conditions=[near("A staffed weekend service"),
                                               near("a staffed  weekend service")],
                        not_checked_yet=[], outside_supported_area=[], broad=False)
    assert reference_places.single_fact_request(plan) == "A fictional request"
    second = plan.model_copy(update={"conditions": [*plan.conditions, near("A river port")]})
    assert reference_places.single_fact_request(second) is None
    assert reference_places.single_fact_request(plan.model_copy(update={"edited": True})) is None
    off = second.model_copy(deep=True)
    off.conditions[-1].switched_off = True
    assert reference_places.single_fact_request(off) == "A fictional request"


def _forget_reused_facts():
    from jobcu import db
    with db.connect() as conn:
        conn.execute("DELETE FROM preparation_cache WHERE kind IN (?, ?)",
                     (reference_places.RESEARCH_REUSE_KIND, reference_places.VERIFIED_KIND))


def _forget_route_reuse():
    from jobcu import db
    with db.connect() as conn:
        conn.execute("DELETE FROM preparation_cache WHERE kind = ?",
                     (reference_places.RESEARCH_REUSE_KIND,))


def test_verified_city_facts_last_90_days_whichever_ai_or_wording_found_them(cities):
    from jobcu import db

    request = "Fictional request: near a city with a staffed public service"
    first = CachedClient(search_id=1)
    found = reference_places.check(first, 'City service', cities[:2], request=request)
    assert [c.meets for c in found.reference_checks] == [True, False]
    # Another search, another model, another wording of the same request: no look-up.
    other = CachedClient(search_id=2)
    other.settings.ai.model = 'another-fictional-model'
    again = reference_places.check(other, 'A reworded city service', cities[:2],
                                   request=request)
    assert other.calls == []
    assert [(c.meets, c.evidence, c.sources, c.checked_at) for c in again.reference_checks] == [
        (c.meets, c.evidence, c.sources, c.checked_at) for c in found.reference_checks]
    assert again.sources and again.status == 'applied'
    # Another request (or an edited fact, which has none) is another question.
    reference_places.check(other, 'Another city service', cities[:2])
    assert [k for k, _ in other.calls].count('research') == 1
    # After 90 days the fact is checked again; an unknown answer keeps the older verified one.
    old = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    with db.connect() as conn:
        for row in conn.execute("SELECT key, answer_json FROM preparation_cache WHERE kind = ?",
                                (reference_places.VERIFIED_KIND,)).fetchall():
            fact = ReferenceCheck.model_validate_json(row["answer_json"])
            conn.execute("UPDATE preparation_cache SET answer_json = ? WHERE kind = ? AND key = ?",
                         (fact.model_copy(update={"checked_at": old}).model_dump_json(),
                          reference_places.VERIFIED_KIND, row["key"]))
    _forget_route_reuse()
    unsure = CachedClient(search_id=3)
    unsure.rows = []  # the new look-up establishes nothing
    kept = reference_places.check(unsure, 'City service', cities[:2], request=request)
    assert [k for k, _ in unsure.calls].count('research') == 1
    assert [(c.meets, c.checked_at) for c in kept.reference_checks] == [(True, old), (False, old)]


def test_a_reviewed_city_decision_stands_before_any_remembered_or_researched_answer(cities):
    from jobcu.reference_sources import request_key
    from jobcu.settings import CityDecision, EvidenceLink, PlaceEvidenceSet

    request = "Fictional request: near a city with a staffed public service"
    first = CachedClient(search_id=1)
    found = reference_places.check(first, 'City service', cities[:2], request=request)
    assert [c.meets for c in found.reference_checks] == [True, False]  # remembered 90 days

    # A reviewed answer computed from official figures: Birch meets after all, and Atlas fails.
    reviewed = CachedClient(search_id=2)
    reviewed.settings.place_evidence = [PlaceEvidenceSet(
        fact_key="0" * 64, request_key=request_key(request), sources=[], city_decisions=[
            CityDecision(country="DE", name=name, meets=meets,
                         reason=f"{name}: official register, 3 of 4 districts.",
                         sources=[EvidenceLink(url="https://register.example.test/data.csv",
                                               title="Fictional official register")],
                         reviewed="2026-10-30: computed from the official register")
            for name, meets in (("Atlas", False), ("Birch", True))])]
    again = reference_places.check(reviewed, 'A reworded city service', cities[:3],
                                   request=request)
    atlas, birch, cedar = again.reference_checks
    assert (atlas.meets, birch.meets) == (False, True)
    assert birch.evidence.startswith("Reviewed decision: Birch: official register")
    assert [s.url for s in birch.sources] == ["https://register.example.test/data.csv"]
    # Only the city without a decision was looked up; the decided ones never are.
    research = [r for kind, r in reviewed.calls if kind == 'research']
    assert len(research) == 1 and 'Cedar' in research[0]['prompt']
    assert 'Atlas' not in research[0]['prompt'] and 'Birch' not in research[0]['prompt']
    assert cedar.meets is True  # the fake researcher's answer for its first city
    # Even after the remembered answers would be rechecked, the decisions still stand.
    _forget_reused_facts()
    later = CachedClient(search_id=3)
    later.settings.place_evidence = reviewed.settings.place_evidence
    final = reference_places.check(later, 'City service', cities[:2], request=request)
    assert [c.meets for c in final.reference_checks] == [False, True] and not later.calls
