"""Partial destination evidence must be visible without rejecting usable jobs."""

from test_search import ready, wait_until_done  # noqa: F401

from jobcu import search
from jobcu.location import Anchor, Condition, LocationPlan, TownRef, condition_warnings
from jobcu.settings import SearchForm


def partial_plan():
    condition = Condition(
        text="Within 100 km of a town with an open public library",
        understood_as="Within 100 km of a town with an open public library",
        status="estimate", kind="near", max_km=100,
        anchor=Anchor(named=[TownRef(name="Berlin", country="DE")],
                      research_status="not_checked"),
        note="Library opening hours could not be checked because research failed.",
    )
    return LocationPlan(text=condition.text, understood_as=condition.text, countries=["DE"],
                        places=[], conditions=[condition], not_checked_yet=[],
                        outside_supported_area=[], broad=False)


def test_completed_search_explains_failed_reference_fact_without_losing_jobs(
        ready, monkeypatch):  # noqa: F811
    plan = partial_plan()
    monkeypatch.setattr(search, "interpret_location_reusing", lambda *_, **kw: (plan, False))
    manager = search.SearchManager()
    manager.start(SearchForm())
    result = wait_until_done(manager)
    assert result["status"] == "finished"
    assert not result["result"]["jobs"]["cards"]
    pending = result["result"]["jobs"]["location_unchecked"]
    assert pending
    assert any("Library opening hours could not be checked" in note for note in result["notes"])
    detail = next(step["detail"] for step in result["steps"] if step["id"] == "location")
    assert "details are unchecked" in detail
    assert "condition checked" not in detail
    for card in pending:
        assert card["score"] is None and card["parts"] is None
        assert any(check["status"] == "unclear" for check in card["location_checks"])


def test_measured_journey_cannot_hide_missing_destination_facts():
    plan = partial_plan()
    plan.conditions[0].status = "applied"  # even a legacy overly confident outer status
    plan.conditions[0].travel["fictional-point"] = {
        "minutes": {"Berlin": 20}, "by": "Google Maps",
    }
    assert condition_warnings(plan)
    assert plan.conditions[0].travel["fictional-point"]["minutes"]["Berlin"] == 20


def test_pending_journey_is_not_reported_as_failed_reference_research():
    plan = partial_plan()
    plan.conditions[0].anchor.research_status = "applied"
    plan.conditions[0].note = ""
    assert plan.conditions[0].status == "estimate"
    assert condition_warnings(plan) == []


def test_disabled_conditions_and_job_preferences_need_no_place_warning():
    plan = partial_plan()
    plan.conditions[0].switched_off = True
    plan.conditions.append(Condition(
        text="Prefer daytime work", understood_as="Prefer daytime work",
        status="not_checked", kind="about_job",
    ))
    assert condition_warnings(plan) == []


def test_resolved_condition_warning_is_retired_without_losing_source_notes():
    plan = partial_plan()
    before = condition_warnings(plan)
    run = search.SearchRun(id=1, form=SearchForm(), started_at="2026-10-12T10:00:00+00:00")
    source_note = "A fictional job source temporarily failed."
    for note in [source_note, *before]:
        run.note(note)
    plan.conditions[0].anchor.research_status = "applied"
    plan.conditions[0].status = "applied"
    plan.conditions[0].note = ""
    run.replace_notes(before, condition_warnings(plan))
    assert run.notes == [source_note]
