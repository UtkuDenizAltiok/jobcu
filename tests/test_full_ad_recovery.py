"""Matched-copy recovery uses fictional ads and disposable local data, never live sources."""

import dataclasses
import threading
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from jobcu import db, jobstore, pipeline
from jobcu.dedupe import JobGroup
from jobcu.sources.base import FoundJob, JobSource, SourceError, SourceReport
from jobcu.sources.budget import BudgetExhausted, Limits, RequestBudget
from jobcu.sources.http import Blocked, RequestStopped

FULL = "Full fictional requirements: five years of experience and fluent German are required."


def ad(source, reference="1", title="Power Electronics Engineer", **kwargs):
    return FoundJob(source=source, source_job_id=reference,
                    url=f"https://{source}.example.test/{reference}", title=title,
                    company="Fictional Employer", country="DE", location_text="Berlin",
                    description="Short summary", posted_at=datetime.now(UTC),
                    date_precision="exact", **kwargs)


class Source(JobSource):
    def __init__(self, name, outcome="full", kind="job_board"):
        self.id, self.name, self.kind = name, name, kind
        self.outcome, self.calls = outcome, []

    def search(self, query, ctx):
        return iter([])

    def load_details(self, job, ctx):
        self.calls.append(job.source_job_id)
        ctx.report.requests += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        if callable(self.outcome):
            return self.outcome(job, ctx)
        if self.outcome == "summary":
            return job
        return dataclasses.replace(job, description=FULL, description_is_complete=True)


def load(groups, sources, statuses=None, run=None, indexes=None):
    reports = [SourceReport(s.id, s.name, status=(statuses or {}).get(s.id, "ok"))
               for s in sources]
    collected = pipeline.Collected([], reports, {s.id: s for s in sources})
    if run is None:
        run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, list(range(len(groups))) if indexes is None else indexes,
                           collected, None, None, run)
    return collected


@pytest.mark.parametrize("failure", ["summary", SourceError("Unavailable"),
                                     Blocked("fictional.example.test"), BudgetExhausted("Limit")])
@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse", "Chef"])
def test_an_alternative_matched_copy_supplies_full_requirements(failure, title):
    first, second = Source("first", failure), Source("second")
    group = JobGroup([ad("first", title=title), ad("second", title=title)])
    load([group], [first, second])
    assert group.best_description_copy.description == FULL
    assert group.best_description_copy.description_is_complete
    assert first.calls == second.calls == ["1"]
    assert [(c.source, c.source_job_id) for c in group.copies] == [("first", "1"), ("second", "1")]


def test_cached_full_copy_is_used_before_any_network_reader():
    first, second = Source("first"), Source("second")
    group = JobGroup([ad("first"), ad("second")])
    jobstore.remember_ad(dataclasses.replace(group.copies[1], description=FULL,
                                           description_is_complete=True))
    load([group], [first, second])
    assert group.best_description_copy.description == FULL
    assert first.calls == second.calls == []


def test_cached_full_copy_does_not_need_a_live_detail_adapter():
    class ListOnly(Source):
        load_details = JobSource.load_details

    first, cached = Source("first"), ListOnly("cached")
    group = JobGroup([ad("first"), ad("cached")])
    jobstore.remember_ad(dataclasses.replace(group.copies[1], description=FULL,
                                           description_is_complete=True))
    load([group], [first, cached], statuses={"cached": "unavailable"})
    assert group.best_description_copy.description == FULL
    assert first.calls == cached.calls == []


def test_original_employer_copy_is_read_before_board_copy():
    board, employer = Source("board"), Source("employer", kind="employer")
    group = JobGroup([ad("board"), ad("employer")],
                     source_kinds={"board": "job_board", "employer": "employer"})
    load([group], [board, employer])
    assert employer.calls == ["1"] and board.calls == []


@pytest.mark.parametrize("status", ["unavailable", "skipped"])
def test_unavailable_sources_are_not_probed(status):
    unavailable, allowed = Source("unavailable"), Source("allowed")
    group = JobGroup([ad("unavailable"), ad("allowed")])
    load([group], [unavailable, allowed], statuses={"unavailable": status})
    assert unavailable.calls == []
    assert allowed.calls == ["1"]


def test_existing_complete_ad_prevents_all_other_reads():
    first, second = Source("first"), Source("second")
    group = JobGroup([dataclasses.replace(ad("first"), description=FULL,
                                         description_is_complete=True), ad("second")])
    load([group], [first, second])
    assert first.calls == second.calls == []


def test_empty_complete_response_preserves_summary_and_tries_another_copy():
    first = Source("first", lambda job, ctx: dataclasses.replace(
        job, description=" ", description_is_complete=True))
    second = Source("second")
    group = JobGroup([ad("first"), ad("second")])
    load([group], [first, second])
    assert group.copies[0].description == "Short summary"
    assert not group.copies[0].description_is_complete
    assert group.best_description_copy.description == FULL


def test_mismatched_identity_cannot_replace_or_enter_the_cache():
    first = Source("first", lambda job, ctx: dataclasses.replace(
        job, source_job_id="unrelated-vacancy", description=FULL, description_is_complete=True))
    second = Source("second")
    group = JobGroup([ad("first"), ad("second")])
    load([group], [first, second])
    assert group.copies[0].source_job_id == "1" and group.copies[0].description == "Short summary"
    assert jobstore.remembered_ad(ad("first", "unrelated-vacancy")) is None
    assert group.best_description_copy.source == "second"


def test_stop_prevents_fallback_requests_and_keeps_evidence():
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    def stopped(job, ctx):
        run.stop_requested = True
        raise RequestStopped()
    first, second = Source("first", stopped), Source("second")
    group = JobGroup([ad("first"), ad("second")])
    load([group], [first, second], run=run)
    assert first.calls == ["1"] and second.calls == []
    assert all(c.description == "Short summary" for c in group.copies)


def test_failure_keeps_job_summary_and_never_marks_it_complete():
    first, second = Source("first", "summary"), Source("second", SourceError("Unavailable"))
    group = JobGroup([ad("first"), ad("second")])
    load([group], [first, second])
    assert len(group.copies) == 2
    assert group.best_description_copy.description == "Short summary"
    assert not group.best_description_copy.description_is_complete


def test_other_groups_are_not_read_and_duplicate_copy_ids_are_not_retried():
    first, second = Source("first", "summary"), Source("second")
    group = JobGroup([ad("first"), ad("first"), ad("second")])
    other = JobGroup([ad("second", "2")])
    load([group, other], [first, second], indexes=[0])
    assert first.calls == second.calls == ["1"]
    assert other.best_description_copy.description == "Short summary"


def test_success_is_cached_and_does_not_get_scored_or_saved_as_a_new_identity():
    source = Source("first")
    group = JobGroup([ad("first")])
    ids, _ = jobstore.remember([group], search_id=1)
    jobstore.set_state(ids[0], saved=True, applied=True)
    load([group], [source])
    assert jobstore.remembered_ad(ad("first")).description == FULL
    assert jobstore.find_job_ids([group]) == ids
    state = jobstore.states(ids)[ids[0]]
    assert state.saved and state.applied


def test_exhausted_budget_is_not_expanded_by_fallback():
    budget = RequestBudget("limited", "Limited source", Limits(per_search=1))
    budget.spend()
    def limited(job, ctx):
        budget.spend()
        pytest.fail("A source past its limit must not read another page")
    first, second = Source("limited", limited), Source("second")
    group = JobGroup([ad("limited"), ad("second")])
    collected = load([group], [first, second])
    assert budget.used_this_search == 1
    assert second.calls == ["1"]
    assert collected.reports[0].status == "partial"
    assert "most requests" in collected.reports[0].message


def test_independent_sources_run_together_but_each_source_stays_serial():
    barrier = threading.Barrier(2)
    active = threading.Lock()
    def first_read(job, ctx):
        assert active.acquire(blocking=False)
        try:
            if job.source_job_id == "1":
                barrier.wait(timeout=5)
            return dataclasses.replace(job, description=FULL, description_is_complete=True)
        finally:
            active.release()
    def other_read(job, ctx):
        barrier.wait(timeout=5)
        return dataclasses.replace(job, description=FULL, description_is_complete=True)
    first, other = Source("first", first_read), Source("other", other_read)
    groups = [JobGroup([ad("first")]), JobGroup([ad("first", "2")]),
              JobGroup([ad("other")])]
    load(groups, [first, other])
    assert first.calls == ["1", "2"] and other.calls == ["1"]
    assert all(group.best_description_copy.description == FULL for group in groups)


def test_expired_cached_text_is_not_reused():
    source = Source("first")
    copy = ad("first")
    jobstore.remember_ad(dataclasses.replace(copy, description=FULL, description_is_complete=True))
    with db.connect() as conn:
        conn.execute("UPDATE ad_texts SET fetched_at = ?",
                     ((datetime.now(UTC) - timedelta(days=jobstore.AD_TEXT_DAYS + 1)).isoformat(),))
    group = JobGroup([copy])
    load([group], [source])
    assert source.calls == ["1"]


def test_failed_mutating_reader_cannot_change_retained_evidence():
    def mutate_then_fail(job, ctx):
        job.source_job_id = "wrong"
        job.description = "Unrelated evidence"
        job.job_types.append("part_time")
        raise SourceError("Unavailable")
    first, second = Source("first", mutate_then_fail), Source("second")
    group = JobGroup([ad("first"), ad("second")])
    load([group], [first, second])
    assert group.copies[0].source_job_id == "1"
    assert group.copies[0].description == "Short summary"
    assert group.copies[0].job_types == []
    assert group.best_description_copy.description == FULL


def test_shorter_incomplete_response_keeps_richer_summary():
    first = Source("first", lambda job, ctx: dataclasses.replace(job, description="Short"))
    group = JobGroup([ad("first")])
    load([group], [first])
    assert group.best_description_copy.description == "Short summary"
    assert not group.best_description_copy.description_is_complete


@pytest.mark.parametrize("cache_failure", ["remembered_ad", "remember_ad"])
def test_cache_failure_cannot_prevent_recovery(monkeypatch, cache_failure):
    def fail(*args):
        raise OSError("Fictional local storage failure")
    monkeypatch.setattr(jobstore, cache_failure, fail)
    source = Source("first")
    group = JobGroup([ad("first")])
    load([group], [source])
    assert group.best_description_copy.description == FULL
    assert group.best_description_copy.description_is_complete
