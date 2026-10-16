"""Saved fictional evidence recovery must not guess missing verdicts or erase blockers."""

import copy

import pytest
from test_requirements import PROFILE, answer, check

from jobcu import pool, recheck, requirements, scoring, search
from jobcu.ai.base import AIConnectionError
from jobcu.dedupe import JobGroup
from jobcu.pool import PoolJob
from jobcu.settings import SearchForm, Settings
from jobcu.sources.base import FoundJob

AD = ("Applicants must hold active professional registration. Ward care is required. "
      "A specialist licence is required.")
FACT = "Active registration is held."
PERSON = PROFILE.model_copy(update={"summary": FACT + " A specialist licence is not held."})


def saved(checks, *, complete=True):
    group = JobGroup([FoundJob(
        source="fictional", source_job_id="example", url="https://example.test/job",
        title="Ward nurse", company="Fictional Hospital", country="DE",
        description=AD, description_is_complete=complete)])
    result = scoring.finish(answer(checks, hard=15), PERSON, ad_text=AD, complete=complete)
    return PoolJob(group, unrelated=False, scored=result)


class Client:
    def __init__(self, rows=(), failure=False):
        self.rows, self.failure, self.calls, self.notices = rows, failure, [], []

    def generate(self, output, **request):
        assert output is recheck.Comparisons
        self.calls.append(request)
        if self.failure:
            raise AIConnectionError("A fictional connection failed")
        return recheck.Comparisons(checks=self.rows)

    def notify(self, text):
        self.notices.append(text)


def comparison(**changes):
    return recheck.Comparison.model_validate({
        **check("met", profile_words=FACT).model_dump(), "id": "R0", **changes})


def test_grounding_keeps_the_proposal_and_exact_validation_failure():
    original = check("met", ad_words="An invented required qualification", profile_words=FACT)
    grounded = requirements.ground([original], AD, PERSON.model_dump())[0]
    assert grounded["status"] == "unclear" and grounded["proposed_status"] == "met"
    assert grounded["grounding_issues"] == ["ad_quote_unverified"]
    assert requirements.revalidate([grounded], AD, PERSON.model_dump())[0]["status"] == "unclear"


def test_a_retained_verdict_can_recover_after_format_validation_is_fixed_without_ai():
    job = saved([check("unclear", profile_words=FACT)])
    job.scored["evidence"]["requirement_checks"][0].update(
        proposed_status="met", grounding_issues=["ad_quote_unverified"])
    before = dict(job.scored["parts"])
    recheck.refresh_validation(job, PERSON)
    assert job.scored["evidence"]["requirement_checks"][0]["status"] == "met"
    assert job.scored["parts"]["hard_requirements"] == 15
    assert {k: v for k, v in job.scored["parts"].items() if k != "hard_requirements"} == {
        k: v for k, v in before.items() if k != "hard_requirements"}
    assert not recheck.needs_comparison(job)


def test_legacy_unknown_cannot_be_restored_from_high_points_or_valid_quotes():
    job = saved([check("unclear", profile_words=FACT)])
    for row in job.scored["evidence"]["requirement_checks"]:
        row.pop("proposed_status")
        row.pop("grounding_issues")
    original = copy.deepcopy(job.scored)
    recheck.refresh_validation(job, PERSON)
    assert job.scored == original and recheck.needs_comparison(job)


@pytest.mark.parametrize("skill", ["Circuit simulation", "Ward care", "Lesson planning"])
def test_fresh_focused_comparison_can_resolve_evidence_without_changing_other_parts(skill):
    person = PERSON.model_copy(update={"skills": [skill]})
    job = saved([check("unclear", profile_words=FACT)])
    before = dict(job.scored["parts"])
    client = Client([comparison()])
    assert recheck.compare(client, job, person)
    assert len(client.calls) == 1 and client.calls[0]["step"] == "requirements"
    assert job.scored["evidence"]["requirement_checks"][0]["status"] == "met"
    assert not any("could not be confirmed" in n for n in job.scored["notes"])
    for part in before.keys() - {"hard_requirements"}:
        assert job.scored["parts"][part] == before[part]


def test_recheck_cannot_target_a_confirmed_blocker_or_erase_it_by_omission():
    job = saved([check("unclear", profile_words=FACT), check(
        "not_met", ad_words="A specialist licence is required",
        profile_words="A specialist licence is not held.", name="Specialist licence")])
    known = copy.deepcopy(job.scored["evidence"]["requirement_checks"][1])
    client = Client([comparison(), comparison(id="R1")])
    recheck.compare(client, job, PERSON)
    assert job.scored["evidence"]["requirement_checks"][1] == known
    assert job.scored["score"] == 55


@pytest.mark.parametrize("rows", [[], [comparison(id="R99")],
                                  [comparison(), comparison(status="not_met")],
                                  [comparison(profile_words="An invented completed licence")]])
def test_unsupported_missing_or_ambiguous_answers_remain_unknown(rows):
    job = saved([check("unclear", profile_words=FACT)])
    recheck.compare(Client(rows), job, PERSON)
    assert job.scored["evidence"]["requirement_checks"][0]["status"] == "unclear"


def test_summary_and_connection_failure_do_not_become_confirmed_requirements():
    job = saved([check("unclear", profile_words=FACT)], complete=False)
    client = Client()
    assert recheck.compare(client, job, PERSON) and not client.calls
    job = saved([check("unclear", profile_words=FACT)])
    before = copy.deepcopy(job.scored)
    failed = Client(failure=True)
    assert not recheck.compare(failed, job, PERSON)
    assert job.scored == before and len(failed.notices) == 1


@pytest.mark.parametrize("failure", [False, True])
def test_recovery_respects_scoring_limit_and_stops_queued_work_after_failure(failure):
    jobs = [saved([check("unclear", profile_words=FACT)]) for _ in range(5)]
    kept = pool.Pool(search_id=1, jobs=jobs, profile=PERSON.model_dump())
    run = search.SearchRun(id=1, form=SearchForm(), started_at="2026-01-01T00:00:00Z",
                           steps=[search.Step("requirements", "Rechecking requirements")])
    asked = []
    run.ask = lambda question: asked.append(question) or False
    settings = Settings()
    settings.limits.scoring_cap = 2
    client = Client([comparison()], failure=failure)
    client.parallel_requests = 1
    search._retry_requirements(run, client, kept, settings)
    assert len(client.calls) == (1 if failure else 2)
    assert len(asked) == (0 if failure else 1)
    assert sum(j.scored["evidence"]["requirement_checks"][0]["status"] == "met"
               for j in jobs) == (0 if failure else 2)
    assert all(j.scored["evidence"]["requirement_checks"][0]["status"] == "unclear"
               for j in jobs[2:])
