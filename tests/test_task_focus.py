"""Fictional task-fit ceilings and recoverable location uncertainty, without paid calls."""

from types import SimpleNamespace

import pytest
from test_scoring import PLAN, PROFILE, score_json

from jobcu import pipeline, scoring, travel
from jobcu.dedupe import JobGroup
from jobcu.location import Anchor, Condition
from jobcu.places import Town
from jobcu.sources.base import FoundJob

FIELDS = [
    ("Electronics", "Power Design Engineer"), ("Nursing", "Ward Nurse"),
    ("Teaching", "Primary Teacher"), ("Hospitality", "Pastry Chef"),
]


def strong_other_parts(role):
    return scoring.JobScore.model_validate(score_json(
        "J0", role=role, seniority=20, location_and_preferences=10))


@pytest.mark.parametrize("field,target", FIELDS)
@pytest.mark.parametrize("role", [28, 31, 35])
def test_neighbouring_or_gapped_main_work_cannot_become_an_excellent_match(
        field, target, role):
    person = PROFILE.model_copy(update={"field": field, "target_roles": [target]})
    result = scoring.finish(strong_other_parts(role), person)
    assert result["score"] == 80
    assert sum(result["parts"].values()) > 80
    assert result["limits"][0]["why"] == \
        "Some gaps in the main work or a neighbouring specialisation"


@pytest.mark.parametrize("field,target", FIELDS)
@pytest.mark.parametrize("role", [36, 40])
def test_direct_core_work_stays_ahead_without_a_new_ceiling(field, target, role):
    person = PROFILE.model_copy(update={"field": field, "target_roles": [target]})
    direct = scoring.finish(strong_other_parts(role), person)
    adjacent = scoring.finish(strong_other_parts(35), person)
    assert direct["score"] == role + 60 and direct["limits"] == []
    cards = [{"title": "Adjacent", "score": adjacent["score"], "posted_at": None},
             {"title": "Direct", "score": direct["score"], "posted_at": None}]
    assert pipeline.sort_cards(cards)[0]["title"] == "Direct"


def group():
    return JobGroup(copies=[FoundJob(
        source="fictional", source_job_id="1", url="https://vacancy.example.test/1",
        title="Specialist", country="DE", location_text="Berlin",
    )])


def plan(status="not_checked"):
    condition = Condition(
        text="Within 50 minutes of a city with a public library",
        understood_as="Within 50 minutes of a city with a public library",
        status="estimate", kind="near", max_minutes=50, travel_mode="transit",
        anchor=Anchor(named=[], research_status=status),
        note="Library opening evidence unavailable.",
    )
    condition.travel[travel.job_key(group())] = {
        "minutes": {"Reference City": 40}, "by": "Google Maps", "unchecked": [],
    }
    return PLAN.model_copy(update={"conditions": [condition]})


@pytest.mark.parametrize("field,target", FIELDS)
@pytest.mark.parametrize("status", ["not_checked", "estimate"])
def test_successful_trip_does_not_make_unverified_city_fact_fully_fit(field, target, status):
    person = PROFILE.model_copy(update={"field": field, "target_roles": [target]})
    result = scoring.finish(strong_other_parts(40), person)
    checked = scoring.with_location_confidence(result, person, plan(status), group())
    assert checked["parts"]["location_and_preferences"] == 8
    assert checked["score"] == 98
    assert checked["evidence"]["location_preferences_proposed"] == 10
    assert checked["notes"] == ["Some requested location conditions could not be confirmed"]
    assert result["score"] == 100  # original evidence is not mutated


@pytest.mark.parametrize("resolution", ["resolved", "disabled"])
def test_later_resolution_restores_points_without_paid_rescoring_or_stale_note(resolution):
    result = scoring.finish(strong_other_parts(40), PROFILE)
    wanted = plan()
    checked = scoring.with_location_confidence(result, PROFILE, wanted, group())
    if resolution == "resolved":
        wanted.conditions[0].anchor.research_status = "applied"
    else:
        wanted.conditions[0].switched_off = True
    restored = scoring.with_location_confidence(checked, PROFILE, wanted, group())
    assert restored["score"] == 100 and restored["parts"]["location_and_preferences"] == 10
    assert "Some requested location conditions could not be confirmed" not in restored["notes"]


def test_incomplete_route_and_ai_estimate_are_unknown_but_one_valid_route_is_enough():
    result = scoring.finish(strong_other_parts(40), PROFILE)
    wanted = plan("applied")
    entry = wanted.conditions[0].travel[travel.job_key(group())]
    entry.update({"minutes": {}, "unchecked": ["Reference City"]})
    assert scoring.with_location_confidence(result, PROFILE, wanted, group())["score"] == 98
    entry.update({"minutes": {"Reference City": 40}, "by": travel.ESTIMATE})
    assert scoring.with_location_confidence(result, PROFILE, wanted, group())["score"] == 98
    entry["by"] = "Google Maps"
    assert scoring.with_location_confidence(result, PROFILE, wanted, group())["score"] == 100


def test_confidence_refresh_preserves_excerpt_warnings_without_inventing_online_evidence():
    result = scoring.finish(strong_other_parts(40), PROFILE)
    result.update({"read_online": True, "notes": ["Only part of this lengthy ad was read"]})
    checked = scoring.with_location_confidence(result, PROFILE, plan(), group())
    assert "Only part of this lengthy ad was read" in checked["notes"]
    assert scoring.ONLINE_NOTE not in checked["notes"]  # an attempted lookup is not a finding
    assert scoring.with_location_confidence({"score": 70}, PROFILE, plan(), group()) == \
        {"score": 70}  # incomplete legacy result stays usable


def test_unchecked_reference_fact_is_sent_to_scorer_despite_usable_outer_rule():
    wanted = plan()
    prompt = scoring._background(PROFILE, wanted)
    assert "unchecked_location_conditions" in prompt
    assert wanted.conditions[0].understood_as in prompt


def test_uncertainty_reduction_does_not_drop_useful_evidence_work_at_the_research_gate():
    from jobcu import jobplace

    raw = scoring.JobScore.model_validate(score_json(
        "J0", role=18, seniority=0, hard_requirements=7, location_and_preferences=10))
    before = scoring.finish(raw, PROFILE)
    checked = scoring.with_location_confidence(before, PROFILE, plan(), group())
    assert before["score"] == 50 and checked["score"] == 48
    assert scoring.evidence_priority(checked) == 50
    assert jobplace.needs_requirements(group(), before)
    assert jobplace.needs_requirements(group(), checked)
    low = scoring.with_location_confidence(
        scoring.finish(strong_other_parts(7), PROFILE), PROFILE, plan(), group())
    assert scoring.evidence_priority(low) == 30  # other fit limits are never bypassed


def test_equal_fit_breakdowns_and_incomplete_legacy_cards_keep_newest_tie_break():
    fit = scoring.finish(strong_other_parts(31), PROFILE)
    for parts in [{}, {"role_and_skills": 31}, fit["parts"]]:
        older = {"score": 80, "parts": parts, "posted_at": "2026-01-01T00:00:00Z"}
        newer = {"score": 80, "parts": parts, "posted_at": "2026-01-02T00:00:00Z"}
        assert pipeline.sort_cards([older, newer]) == [newer, older]


def test_small_workplace_can_fit_through_a_qualifying_reference_city(monkeypatch):
    small = Town("Milltown", "DE", 10.1, 10, 1000)
    reference = Town("Reference City", "DE", 10, 10, 5000)
    monkeypatch.setitem(travel.COUNTRIES, "DE", SimpleNamespace(people=1_000_000))
    monkeypatch.setattr(travel.place_list, "towns_in", lambda _: [small, reference])
    monkeypatch.setattr(travel.place_list, "part_of", lambda _: None)
    wanted = plan("applied")
    wanted.conditions[0].anchor.min_share_of_country = 0.003
    assert travel.anchor_towns(wanted.conditions[0].anchor, "DE") == [reference]
    assert travel.answer(wanted.conditions[0], group()) == "yes"
    result = scoring.finish(strong_other_parts(40), PROFILE)
    assert scoring.with_location_confidence(result, PROFILE, wanted, group())["score"] == 100
