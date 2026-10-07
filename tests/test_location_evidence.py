"""A checked journey cannot prove a separate fact about its reference city."""

import pytest
from test_location_conditions import ScriptedClient
from test_travel import NOW, FakeMaps, group, meter

from jobcu import travel
from jobcu.filters import condition_fit
from jobcu.location import (
    CheckedCondition,
    ConditionEdit,
    LocationPlan,
    SortedAnchor,
    SortedCondition,
    TownRef,
    apply_edits,
    check_conditions,
)
from jobcu.pipeline import build_card


def reference_condition(confidence):
    text = "Within 25 minutes of a city with 100,000 people and a public library"
    sorted_kind = SortedCondition(
        text=text, understood_as=text, kind="near", max_minutes=25, travel_mode="transit",
        anchor=SortedAnchor(description="large cities with a public library", min_people=100_000,
                            needs_the_web=True, look_up="cities with a public library"))
    answer = CheckedCondition(
        understood_as="Cities with a public library",
        kind="could_not_check" if confidence == "missing" else "towns_that_fit",
        towns=[] if confidence == "missing" else [TownRef(name="Munich", country="DE")],
        confidence="checked" if confidence == "checked" else "estimate",
        note="Library access could not be researched." if confidence == "missing" else
             "Library access was checked." if confidence == "checked" else
             "Library access was estimated.")
    return check_conditions(ScriptedClient(answer, sorted_kinds={text: sorted_kind}),
                            [text], ["DE"])[0]


def card_check(condition, job):
    plan = LocationPlan(text="", understood_as="", countries=["DE"], places=[],
                        conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    card = build_card(job, job_id=1, is_new=True, state=None, scored=None, plan=plan,
                      source_names={"s": "Fictional board"}, possible_duplicate_of=None,
                      started_at=NOW, posted_within_hours=24)
    return card["location_checks"][-1]


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse"])
@pytest.mark.parametrize(("confidence", "status"), [
    ("missing", "unclear"), ("estimate", "estimate"), ("checked", "verified"),
])
def test_route_measurement_does_not_upgrade_reference_city_evidence(confidence, status, title):
    condition = reference_condition(confidence)
    job = group("Fürstenfeldbruck")
    job.main.title = title
    meter(FakeMaps({"Munich": 17})).measure([condition], [job], [0])
    assert condition_fit(condition, job) == "yes"  # retain the usable partial rule
    check = card_check(condition, job)
    assert check["status"] == status
    assert check["source"] == "Google Maps" and "17 min" in check["detail"]
    if confidence != "checked":
        assert condition.status == "estimate"
        assert "Library" in check["note"]


def test_in_reference_city_and_limit_edit_do_not_prove_missing_library_fact():
    condition = reference_condition("missing")
    job = group("Munich")
    meter(key=False).measure([condition], [job], [0])
    assert card_check(condition, job)["status"] == "unclear"
    plan = LocationPlan(text="", understood_as="", countries=["DE"], places=[],
                        conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)
    restored = LocationPlan.model_validate_json(plan.model_dump_json())
    edited = apply_edits(ScriptedClient(None), restored,
                         [ConditionEdit(text=condition.text, original=0, max_minutes=30)])
    meter(key=False).measure(edited.conditions, [job], [0])
    assert card_check(edited.conditions[0], job)["status"] == "unclear"


def test_legacy_research_note_survives_route_measurement_without_invented_confidence():
    condition = reference_condition("missing")
    old = condition.model_dump()
    del old["anchor"]["research_status"]
    restored = type(condition).model_validate(old)
    job = group("Munich")
    meter(key=False).measure([restored], [job], [0])
    check = card_check(restored, job)
    assert check["status"] == "estimate"
    assert "could not be researched" in check["note"]


def test_per_job_route_confidence_does_not_downgrade_another_checked_route():
    condition = reference_condition("checked")
    checked, estimated = group("Fürstenfeldbruck", "checked"), group("Dachau", "estimate")
    condition.travel = {
        travel.job_key(checked): {"minutes": {"Munich": 17}, "by": "Google Maps"},
        travel.job_key(estimated): {"minutes": {"Munich": 20}, "by": "AI estimate"},
    }
    travel.TravelMeter._settle_status(condition)
    assert condition.status == "estimate"
    assert card_check(condition, checked)["status"] == "verified"
    assert card_check(condition, estimated)["status"] == "estimate"


def test_failed_usable_rule_still_rules_out_a_job_with_an_unchecked_city_fact():
    condition = reference_condition("missing")
    job = group("Fürstenfeldbruck")
    meter(FakeMaps({"Munich": 40})).measure([condition], [job], [0])
    assert condition_fit(condition, job) == "no"
    assert card_check(condition, job)["status"] == "fails"
