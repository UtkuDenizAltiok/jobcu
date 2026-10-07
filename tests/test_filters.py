from datetime import UTC, datetime, timedelta

from jobcu.dedupe import group_duplicates
from jobcu.filters import apply_rules
from jobcu.jobstore import JobState
from jobcu.settings import JOB_TYPES
from jobcu.sources.base import FoundJob

NOW = datetime(2026, 9, 17, 12, tzinfo=UTC)


def found(job_id, **extra):
    base = dict(source="s", source_job_id=job_id, url="https://x", title=f"Title {job_id}",
                company=f"Company {job_id}", country="DE", posted_at=NOW, date_precision="exact")
    return FoundJob(**{**base, **extra})


def run(jobs, states=None, **options):
    groups = group_duplicates(jobs, {"s": "job_board"})
    settings = dict(started_at=NOW, posted_within_hours=24, job_types=list(JOB_TYPES),
                    exclude_remote=False, countries=["DE"])
    settings.update(options)
    return groups, apply_rules(groups, states or [None] * len(groups), **settings)


def test_every_rule_leaves_jobs_out_with_a_reason():
    jobs = [
        found("ok"),
        found("old", posted_at=NOW - timedelta(days=3)),
        found("type", job_types=["part_time"]),
        found("remote", work_mode="remote"),
        found("abroad", country="FR"),
        found("undated", posted_at=None, date_precision="unknown"),
    ]
    groups, outcome = run(
        jobs, job_types=["full_time_permanent"], exclude_remote=True
    )
    kept = {groups[i].main.source_job_id for i in outcome.kept}
    assert kept == {"ok", "undated"}
    assert dict(outcome.left_out) == {"too_old": 1, "job_type": 1, "remote": 1, "country": 1}


def test_jobs_marked_not_interested_are_left_out_first():
    groups, outcome = run([found("a")], states=[JobState(dismissed=True)])
    assert outcome.kept == [] and outcome.left_out["dismissed"] == 1


def test_unusable_application_route_is_excluded_before_ai_work():
    for title in ("Power Electronics Engineer", "Registered Nurse"):
        _, outcome = run([found("blocked", title=title,
                                url="https://www.cv-library.co.uk/job/fictional-1")])
        assert outcome.kept == [] and outcome.left_out["application_route"] == 1


def test_reported_routes_are_loaded_once_for_the_free_filter(monkeypatch):
    from jobcu import applications

    calls = []

    def reports():
        calls.append(True)
        return {"https://jobs.example.test/blocked"}

    monkeypatch.setattr(applications, "reported_urls", reports)
    jobs = [found("blocked", url="https://jobs.example.test/blocked", title="Nurse"),
            *[found(str(i), url=f"https://jobs.example.test/{i}") for i in range(100)]]
    groups, outcome = run(jobs)
    assert len(calls) == 1 and len(outcome.kept) == 100
    assert outcome.left_out["reported_application_route"] == 1
    assert all(groups[i].main.url != "https://jobs.example.test/blocked" for i in outcome.kept)


def test_a_job_is_kept_when_one_copy_states_a_ticked_type():
    jobs = [found("a", job_types=["part_time"]),
            found("b", title="Title a", company="Company a", job_types=["full_time_permanent"])]
    _, outcome = run(jobs, job_types=["full_time_permanent"])
    assert len(outcome.kept) == 1
