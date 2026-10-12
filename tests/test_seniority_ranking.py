"""Fictional evidence isolates total-score behavior from live model judgement."""

import pytest

from jobcu.profile import Profile
from jobcu.scoring import JobScore, finish


def profile(field):
    return Profile.model_validate({
        "summary": f"Graduate in {field}.", "current_or_last_role": None, "field": field,
        "skills": [], "technical_areas": [], "years_full_time_experience": 0,
        "years_student_or_part_time_experience": 1, "experience_note": "Student placement.",
        "seniority": "junior", "education": [], "languages": [],
        "target_roles": [field], "target_fields": [], "preferences": [],
        "work_mode_preference": "not_stated", "dealbreakers": [],
        "work_authorisation": None, "ignored_as_application_specific": [],
    })


def score(person, *, level, role=40, **evidence):
    answer = JobScore.model_validate({
        "job_id": "J0", "ad_language": "English", "languages_asked": [],
        "years_required": None, "doctorate": "not_required",
        "citizenship_or_clearance": "no_such_requirement",
        "citizenship_or_clearance_words": "", "requirement_checks": [],
        "role_and_skills": role, "seniority": level, "hard_requirements": 15,
        "location_and_preferences": 10, "reasons": ["Relevant skills"],
        "job_type": "full_time_permanent", "work_mode": "on_site", "fully_remote": False,
        **evidence,
    })
    return finish(answer, person, ad_text="Fictional full original ad.", complete=True)


@pytest.mark.parametrize("field", ["Electronics", "Nursing", "Teaching"])
def test_clearly_wrong_level_cannot_outrank_suitable_adjacent_entry_role(field):
    person = profile(field)
    # A strong skill overlap cannot compensate for a clearly unsuitable responsibility level.
    senior = score(person, level=11)
    suitable = score(person, level=18, role=28)
    assert senior["parts"]["role_and_skills"] > suitable["parts"]["role_and_skills"]
    assert senior["score"] < suitable["score"]
    assert senior["limits"] and "level" in senior["limits"][0]["why"]


@pytest.mark.parametrize("field", ["Electronics", "Nursing", "Teaching"])
@pytest.mark.parametrize(("level", "maximum"), [(0, 50), (5, 50), (6, 65), (11, 65)])
def test_clear_level_mismatch_limits_high_skill_total(field, level, maximum):
    result = score(profile(field), level=level)
    assert sum(result["parts"].values()) > maximum
    assert result["score"] == maximum


@pytest.mark.parametrize("level", [12, 17, 18, 20])
def test_small_gap_and_matching_level_keep_the_existing_total(level):
    result = score(profile("Teaching"), level=level)
    assert result["score"] == sum(result["parts"].values())
    assert result["limits"] == []


def test_matching_senior_person_is_not_penalised_by_title_or_experience():
    person = profile("Nursing").model_copy(update={
        "summary": "Experienced nursing team leader.", "seniority": "senior",
        "years_full_time_experience": 12,
    })
    result = score(person, level=20, years_required=10)
    assert result["score"] == 100
    assert result["limits"] == []


def test_stronger_eligibility_limit_survives_the_new_level_limit():
    result = score(profile("Electronics"), level=4,
                   citizenship_or_clearance="required_definitely_out_of_reach",
                   citizenship_or_clearance_words="Citizens of Fictionland only")
    assert result["score"] == 30
    assert {limit["at"] for limit in result["limits"]} == {30, 50}


def test_stronger_role_limit_survives_the_new_level_limit():
    result = score(profile("Teaching"), level=4, role=5)
    assert result["score"] == 30
    assert {limit["at"] for limit in result["limits"]} == {30, 50}
