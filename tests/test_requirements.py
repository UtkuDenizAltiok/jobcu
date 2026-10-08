"""Fictional eligibility comparisons: supported blockers, unknowns and later evidence."""

import json
import re
from types import SimpleNamespace

import pytest

from jobcu import jobplace, requirements, scoring
from jobcu.ai.base import ProviderAdapter, RawReply, Usage
from jobcu.ai.client import AIClient
from jobcu.countries import COUNTRIES
from jobcu.dedupe import JobGroup
from jobcu.location import LocationPlan
from jobcu.profile import Profile
from jobcu.settings import Settings
from jobcu.sources.base import FoundJob

PROFILE = Profile.model_validate({
    "summary": "A qualified nurse seeking regular ward work. Registration is pending.",
    "current_or_last_role": "Nurse", "field": "Nursing", "skills": ["Ward care"],
    "technical_areas": [], "years_full_time_experience": 2,
    "years_student_or_part_time_experience": 0, "experience_note": "Two years of ward work.",
    "seniority": "junior", "education": [], "languages": [],
    "target_roles": ["Registered Nurse"], "target_fields": ["Healthcare"],
    "preferences": ["Regular ward work"], "work_mode_preference": "not_stated",
    "dealbreakers": [], "work_authorisation": None, "ignored_as_application_specific": [],
})
AD = "Applicants must hold active professional registration. Ward-care duties."
FACT = "Registration is pending."


def check(status="not_met", ad_words="must hold active professional registration",
          profile_words=FACT, name="Active professional registration"):
    return requirements.RequirementCheck(requirement=name, ad_words=ad_words,
                                         profile_words=profile_words, status=status)


def answer(checks=None, hard=13):
    return scoring.JobScore(
        job_id="J0", ad_language="English", languages_asked=[], years_required=None,
        doctorate="not_required", citizenship_or_clearance="no_such_requirement",
        citizenship_or_clearance_words="", requirement_checks=checks,
        role_and_skills=38, seniority=18, hard_requirements=hard,
        location_and_preferences=9, reasons=["Ward-care skills overlap"],
        job_type="full_time_permanent", work_mode="on_site", fully_remote=False,
    )


def score(checks=None, hard=13, ad=AD, complete=True, profile=PROFILE):
    return scoring.finish(answer(checks, hard), profile, ad_text=ad, complete=complete)


def test_explicit_unmet_requirement_overrides_contradictory_high_points():
    result = score([check()], hard=14)
    assert result["parts"]["hard_requirements"] == 10
    assert result["score"] == 55
    assert result["limits"] == [{
        "at": 55, "why": "Active professional registration: not met by the stated profile",
    }]


@pytest.mark.parametrize(("field", "unsupported"), [
    ("ad_words", "Must already hold a specialist qualification"),
    ("ad_words", ""),
    ("profile_words", "The person has no professional registration"),
    ("profile_words", ""),
])
def test_unsupported_quotes_become_unknown_without_a_blocker(field, unsupported):
    alleged = check().model_copy(update={field: unsupported})
    result = score([alleged], hard=0)
    assert result["evidence"]["requirement_checks"][0]["status"] == "unclear"
    assert result["parts"]["hard_requirements"] == 11
    assert result["limits"] == []
    assert "could not be confirmed" in result["notes"][0]


def test_missing_checks_are_unknown_even_for_a_complete_ad():
    result = score(None, hard=15)
    assert result["parts"]["hard_requirements"] == 14
    assert result["notes"] == ["Mandatory requirements were not fully checked"]


def test_summary_is_incomplete_even_when_all_observed_requirements_are_met():
    result = score([], hard=15, complete=False)
    assert result["parts"]["hard_requirements"] == 14
    assert result["limits"] == []
    assert any("other requirements may be missing" in n for n in result["notes"])


def test_empty_text_cannot_establish_complete_evidence_even_if_source_claims_it():
    result = score([], hard=15, ad=" \n ", complete=True)
    assert result["parts"]["hard_requirements"] == 14
    assert result["evidence"]["requirements_complete"] is False


def test_supported_met_requirement_cannot_be_a_generic_numeric_blocker():
    registered = PROFILE.model_copy(update={"summary": "Active registration is held."})
    result = score([check("met", profile_words="Active registration is held.")],
                   hard=2, profile=registered)
    assert result["parts"]["hard_requirements"] == 15
    assert result["limits"] == []


def test_quote_validation_normalizes_case_unicode_and_whitespace():
    result = score([check(ad_words="MUST\nHOLD ACTIVE PROFESSIONAL REGISTRATION")],
                   ad="Applicants must hold active\u00a0professional registration.")
    assert result["score"] == 55


@pytest.mark.parametrize("reverse", [False, True])
def test_conflicting_comparisons_for_one_clause_are_unknown_in_either_order(reverse):
    checks = [check("met"), check("not_met")]
    if reverse:
        checks.reverse()
    result = score(checks, hard=0)
    assert len(result["evidence"]["requirement_checks"]) == 1
    assert result["evidence"]["requirement_checks"][0]["status"] == "unclear"
    assert result["limits"] == []


@pytest.mark.parametrize("later", [None, [], [check("unclear").model_dump()]])
def test_incomplete_online_notes_do_not_erase_a_known_blocker(later):
    initial = score([check()], complete=False)
    updated = scoring.with_ad_read_online(initial, PROFILE, [], None,
                                         requirement_checks=later)
    assert updated["score"] == 55
    assert updated["evidence"]["requirement_checks"][0]["status"] == "not_met"


def test_explicit_later_resolution_recomputes_points_without_a_sticky_penalty():
    initial = score([check()], complete=False)
    later = check("met", ad_words="Applicants awaiting registration are accepted").model_dump()
    updated = scoring.with_ad_read_online(initial, PROFILE, [], None,
                                         requirement_checks=[later])
    assert updated["limits"] == []
    assert updated["parts"]["hard_requirements"] == 13
    assert updated["score"] == 93
    assert any("incomplete" in n for n in updated["notes"])


def test_legacy_result_keeps_its_original_blocker_on_an_online_update():
    legacy = scoring.finish(answer(None, hard=5), PROFILE)
    updated = scoring.with_ad_read_online(legacy, PROFILE, [], None,
                                         requirement_checks=[check("unclear").model_dump()])
    assert updated["score"] == 55
    assert updated["parts"]["hard_requirements"] == 5


@pytest.mark.parametrize(("field", "fact", "clause", "requirement"), [
    ("Electronics", "graduate_or_entry", "Must be currently enrolled in a degree",
     "Current degree enrolment"),
    ("Teaching", "Teacher registration is pending", "Must hold active teacher registration",
     "Teacher registration"),
    ("Hospitality", "Food hygiene certificate has expired", "Must hold a current food certificate",
     "Current food hygiene certificate"),
])
def test_same_rubric_applies_across_professions(field, fact, clause, requirement):
    profile = PROFILE.model_copy(update={"field": field, "summary": fact,
                                         "seniority": "graduate_or_entry",
                                         "target_roles": [{"Electronics": "Hardware Engineer",
                                                           "Teaching": "Teacher",
                                                           "Hospitality": "Chef"}[field]]})
    result = score([check(ad_words=clause, profile_words=fact, name=requirement)],
                   ad=clause, profile=profile)
    assert result["score"] == 55


class Scripted(ProviderAdapter):
    def __init__(self, checks):
        super().__init__("fake")
        self.checks = checks
        self.calls = []

    def complete_json(self, **request):
        self.calls.append(request)
        ids = re.findall(r"JOB (J\d+)", request["prompt"])
        return RawReply(json.dumps({"scores": [
            answer(self.checks).model_copy(update={"job_id": i}).model_dump() for i in ids
        ]}), Usage(1, 1))

    def list_models(self):
        return []


@pytest.mark.parametrize("country", list(COUNTRIES))
def test_scoring_integration_preserves_every_country_without_extra_ai_calls(country):
    adapter = Scripted([check()])
    settings = Settings()
    settings.ai.provider = "gemini"
    settings.ai.model = "fictional-model"
    client = AIClient(settings, adapter=adapter)
    group = JobGroup(copies=[FoundJob(source="fictional", source_job_id="nurse-1",
                                     title="Ward Nurse", url="https://example.test/nurse-1",
                                     country=country, description=AD,
                                     description_is_complete=True)])
    plan = LocationPlan(text="", understood_as="Anywhere", countries=[country], places=[],
                        broad=True, not_checked_yet=[], outside_supported_area=[])
    result = scoring.score_groups(client, PROFILE, plan, [group], [0])
    assert result[0]["score"] == 55
    assert len(adapter.calls) == 1
    assert "requirement_checks" in adapter.calls[0]["system"]


def test_unseen_quote_at_end_of_long_ad_is_not_treated_as_read():
    adapter = Scripted([check()])
    settings = Settings()
    settings.ai.provider = "gemini"
    settings.ai.model = "fictional-model"
    client = AIClient(settings, adapter=adapter)
    group = JobGroup(copies=[FoundJob(source="fictional", source_job_id="long-1",
                                     title="Ward Nurse", url="https://example.test/long-1",
                                     description="x" * scoring.MAX_DESCRIPTION_CHARS + AD,
                                     description_is_complete=True)])
    plan = LocationPlan(text="", understood_as="Anywhere", countries=[], places=[], broad=True,
                        not_checked_yet=[], outside_supported_area=[])
    result = scoring.score_groups(client, PROFILE, plan, [group], [0])[0]
    assert result["limits"] == []
    assert result["evidence"]["requirement_checks"][0]["status"] == "unclear"
    assert "Only part of this lengthy ad was read for scoring" in result["notes"]


@pytest.mark.parametrize("supported", [True, False])
def test_online_structure_checks_quotes_in_research_notes_and_full_profile(supported):
    class Client:
        def research(self, **kwargs):
            return SimpleNamespace(text=AD if supported else "The vacancy was found.",
                                   usage=Usage(1, 1, web_searches=1))

        def generate(self, schema, **kwargs):
            assert "Registration is pending" in kwargs["prompt"]
            return jobplace.OnlineAnswer(jobs=[jobplace.OnlineJob(
                id="J0", found=True, towns=[], languages_asked=[], years_required=None,
                doctorate="not_required", citizenship_or_clearance="no_such_requirement",
                citizenship_or_clearance_words="", requirement_checks=[check()],
            )])

    result = jobplace._look_up(Client(), ["J0 | Ward Nurse"], 1, PROFILE)["J0"]
    assert result.requirement_checks[0].status == ("not_met" if supported else "unclear")


@pytest.mark.parametrize(("notes", "job_id", "jobs", "expected"), [
    ("JOB J0\nA clause.\nJOB J1\nAnother clause.", "J0", 2, "A clause."),
    ("JOB J0\nA clause.\nJOB J1\nAnother clause.", "J1", 2, "Another clause."),
    ("## JOB J0\nA clause.", "J0", 1, "A clause."),
    ("J0: A clause.\nJ1: Another clause.", "J0", 2, ": A clause."),
    ("A clause without an ID.", "J0", 1, "A clause without an ID."),
    ("A clause without an ID.", "J0", 2, ""),
    ("JOB J0\nOne.\nJOB J0\nTwo.", "J0", 2, ""),
    ("JOB J1\nAnother clause.", "J0", 2, ""),
])
def test_research_quotes_are_scoped_to_one_identifiable_job(notes, job_id, jobs, expected):
    assert jobplace._job_notes(notes, job_id, jobs).strip() == expected


def test_another_jobs_research_clause_cannot_become_a_blocker():
    notes = "JOB J0\nWard work; requirements unclear.\nJOB J1\n" + AD
    checks = requirements.ground([check()], jobplace._job_notes(notes, "J0", 2),
                                str(PROFILE.model_dump()))
    assert checks[0]["status"] == "unclear"
    assert requirements.judge({"requirements_complete": False,
                               "requirement_checks": checks}, 0).limits == []
