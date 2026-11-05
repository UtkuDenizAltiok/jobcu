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
    groups = group_duplicates(jobs, {"s": "job_board", "e": "employer"})
    settings = dict(started_at=NOW, posted_within_hours=24, job_types=list(JOB_TYPES),
                    exclude_remote=False, countries=["DE"])
    settings.update(options)
    return groups, apply_rules(groups, states or [None] * len(groups), **settings)


def test_every_rule_leaves_jobs_out_with_a_reason():
    jobs = [
        found("ok"),
        found("old", posted_at=NOW - timedelta(days=3)),
        found("type", source="e", job_types=["part_time"]),
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


def test_a_job_site_s_type_tag_alone_never_leaves_a_job_out():
    # Three of hackajob's £37,000-85,000 engineering roles and an ad asking for at least 35 hours
    # a week were "part-time" on job sites: the ad text decides after scoring.
    jobs = [found("board", job_types=["part_time"]),
            found("employer", source="e", job_types=["part_time"]),
            found("both", source="e", job_types=["full_time_permanent"], title="Same job"),
            found("both-board", job_types=["part_time"], title="Same job", company="Company both")]
    groups, outcome = run(jobs, job_types=["full_time_permanent"])
    assert {groups[i].main.source_job_id for i in outcome.kept} == {"board", "both"}
    assert dict(outcome.left_out) == {"job_type": 1}


def test_the_ad_text_or_the_employer_proves_a_type_and_a_disagreement_keeps_the_job():
    from jobcu.filters import leaves_for_job_type
    from jobcu.pipeline import job_types_of

    board = group_duplicates([found("b", job_types=["part_time"])], {"s": "job_board"})[0]
    employer = group_duplicates([found("e", source="e", job_types=["part_time"])],
                                {"e": "employer"})[0]
    open_tag = group_duplicates([found("o", job_types=[
        "fixed_term", "freelance_or_contract", "part_time"])], {"s": "job_board"})[0]  # "contract"
    full_tag = group_duplicates([found("f", job_types=["full_time_permanent"])],
                                {"s": "job_board"})[0]
    full, part, unclear, freelance = ({"job_type": t} for t in (
        "full_time_permanent", "part_time", "unclear", "freelance_or_contract"))
    wanted = ["full_time_permanent", "fixed_term"]
    assert not leaves_for_job_type(board, None, wanted)  # a site's tag alone
    assert not leaves_for_job_type(board, unclear, wanted)
    assert not leaves_for_job_type(board, full, wanted)
    assert leaves_for_job_type(board, part, wanted)  # the ad text agrees
    assert leaves_for_job_type(open_tag, freelance, wanted)  # the ad text says which one
    assert not leaves_for_job_type(full_tag, part, wanted)  # a site's tag can keep a job
    assert leaves_for_job_type(employer, None, wanted)
    assert leaves_for_job_type(employer, unclear, wanted)
    assert not leaves_for_job_type(employer, full, wanted)  # the ad names a ticked type
    assert job_types_of(board, full) == ["part_time"]  # what the card shows stays the site's


def test_a_remote_label_is_certain_only_when_no_copy_names_an_office():
    jobs = [found("remote-uk", work_mode="remote", location_text="UK, Remote"),
            found("anywhere", work_mode="remote", location_text="Anywhere"),
            found("or-london", work_mode="remote", location_text="London - UK2; Remote - UK"),
            found("offices", work_mode="remote", location_text="Sunnyvale, California USA; "
                  "London, United Kingdom; Remote, Germany; Yokohama, Japan"),
            found("mixed", work_mode="remote", location_text="Germany", title="Same job"),
            found("mixed-site", work_mode="on_site", location_text="Germany", title="Same job",
                  company="Company mixed"),
            found("mixed-town", work_mode="remote", location_text="Germany", title="Other job"),
            found("mixed-town-2", location_text="München", title="Other job",
                  company="Company mixed-town")]
    groups, outcome = run(jobs, exclude_remote=True)
    kept = {groups[i].main.source_job_id for i in outcome.kept}
    assert kept == {"or-london", "offices", "mixed", "mixed-town"}
    assert dict(outcome.left_out) == {"remote": 2}


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


def test_posted_within_is_strict_also_for_sites_that_list_ads_late():
    # JSearch lists ads days after their date (68-92 hours, 2026-10-29). Those ads used to count
    # while Jobcu never showed the job; the person wants nothing older than the window
    # (2026-11-04), so a late-listed ad is too old like any other.
    def late(job_id, hours, source="jsearch", **extra):
        return found(job_id, source=source, posted_at=NOW - timedelta(hours=hours),
                     date_precision="day", **extra)

    groups, outcome = run([late("lag", 60), late("beyond", 24 + 72 + 30),
                           late("board", 60, source="s"), late("fresh", 3)])
    assert {groups[i].main.source_job_id for i in outcome.kept} == {"fresh"}
    assert outcome.left_out["too_old"] == 3
    # Shown by an earlier search inside this window: not new to the person (search 16).
    groups, outcome = run([late("fresh", 20)], first_shown=[NOW - timedelta(hours=2)])
    assert outcome.kept == [] and outcome.left_out["shown_before"] == 1


def test_a_job_an_earlier_search_showed_inside_the_window_never_comes_back_as_new():
    # Search 17 began 50 minutes earlier in the day than search 16: an ad dated 19:34 that
    # search 16 had shown at 21:46 came back, and so did one a job site dated again after it.
    shown = [NOW - timedelta(hours=2)]
    day = found("day", posted_at=NOW - timedelta(hours=20), date_precision="day")
    before = found("before", posted_at=NOW - timedelta(hours=3), date_precision="exact")
    dated_again = found("again", posted_at=NOW - timedelta(minutes=30), date_precision="exact")
    for job in (day, before, dated_again):
        groups, outcome = run([job], first_shown=shown)
        assert outcome.kept == [] and outcome.left_out["shown_before"] == 1
    groups, outcome = run([day])
    assert outcome.kept == [0]  # never shown: new, whatever its date's precision
