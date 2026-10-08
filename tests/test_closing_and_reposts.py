"""Closing dates for applications, and ads posted again."""

from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from jobcu import db, jobstore
from jobcu.dedupe import group_duplicates
from jobcu.filters import REASONS, apply_rules
from jobcu.freshness import end_of_day, parse_closing
from jobcu.jobposting import find_job_posting
from jobcu.location import LocationPlan
from jobcu.pipeline import Collected, build_card, make_groups
from jobcu.settings import JOB_TYPES
from jobcu.sources.base import FoundJob

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)
class FakeSource:
    def __init__(self, kind):
        self.kind = kind


PLAN = LocationPlan(text="", understood_as="Anywhere.", countries=["DE"], places=[],
                    not_checked_yet=[], outside_supported_area=[], broad=True)


def found(job_id, **extra):
    base = dict(source="s", source_job_id=job_id, url=f"https://board.test/{job_id}",
                title=f"Sozialarbeiter {job_id}", company=f"Stadt {job_id}", country="DE",
                posted_at=NOW - timedelta(hours=2), date_precision="exact")
    return FoundJob(**{**base, **extra})


def test_a_passed_closing_date_leaves_the_job_out():
    jobs = [found("open", closes_at=NOW + timedelta(days=5)),
            found("closed", closes_at=NOW - timedelta(minutes=1)),
            found("unknown")]
    groups = group_duplicates(jobs, {"s": "job_board"})
    outcome = apply_rules(groups, [None] * len(groups), started_at=NOW, posted_within_hours=24,
                          job_types=list(JOB_TYPES), exclude_remote=False, countries=["DE"])
    assert {groups[i].main.source_job_id for i in outcome.kept} == {"open", "unknown"}
    assert dict(outcome.left_out) == {"closed": 1}
    assert "closing date" in REASONS["closed"]


def test_the_latest_closing_date_of_a_jobs_copies_counts():
    # The same job on two sites, one with an extended deadline: it's still open.
    first = found("1", title="Sozialarbeiter", company="Stadt Beispiel",
                  closes_at=NOW - timedelta(days=1))
    second = found("2", source="t", title="Sozialarbeiter", company="Stadt Beispiel",
                   closes_at=NOW + timedelta(days=3))
    groups = group_duplicates([first, second], {"s": "job_board", "t": "job_board"})
    assert len(groups) == 1 and groups[0].closes_at == NOW + timedelta(days=3)


def test_a_closing_day_lasts_until_its_end():
    berlin = ZoneInfo("Europe/Berlin")
    assert end_of_day(date(2026, 10, 7), berlin) == datetime(2026, 10, 7, 21, 59, tzinfo=UTC)
    assert parse_closing("2026-10-16") == datetime(2026, 10, 16, 23, 59, tzinfo=UTC)
    assert parse_closing("2026-10-16T23:59:00+01:00") == datetime(2026, 10, 16, 22, 59,
                                                                   tzinfo=UTC)
    assert parse_closing("") is None and parse_closing("soon") is None


def test_the_standard_job_data_gives_the_closing_date():
    page = ('<script type="application/ld+json">{"@type": "JobPosting", "title": "Teacher", '
            '"datePosted": "2026-09-24", "validThrough": "2026-10-16", '
            '"description": "Teach."}</script>')
    assert find_job_posting(page).valid_through == datetime(2026, 10, 16, 23, 59, tzinfo=UTC)


def card(job, first_seen_at=None):
    group = group_duplicates([job], {"s": "job_board"})[0]
    return build_card(group, job_id=1, is_new=False, state=None, scored=None, plan=PLAN,
                      source_names={"s": "Board"}, possible_duplicate_of=None, started_at=NOW,
                      posted_within_hours=24, first_seen_at=first_seen_at)


def test_cards_show_the_closing_date():
    closes = NOW + timedelta(days=5)
    assert card(found("1", closes_at=closes))["closes_at"] == closes.isoformat()
    assert card(found("2"))["closes_at"] is None


def test_a_job_seen_well_before_its_posting_date_is_marked_as_a_repost():
    job = found("1")  # the ad says two hours ago
    long_ago = NOW - timedelta(days=40)
    assert card(job, first_seen_at=long_ago)["first_seen_at"] == long_ago.isoformat()
    # Seen in this search, or since the ad was posted: nothing to say.
    assert card(job, first_seen_at=NOW)["first_seen_at"] is None
    assert card(job, first_seen_at=NOW - timedelta(hours=20))["first_seen_at"] is None
    assert card(job)["first_seen_at"] is None


def test_the_job_memory_says_when_a_job_was_first_shown():
    with db.connect() as conn:
        search_id = conn.execute(
            "INSERT INTO searches (status, form_json) VALUES ('running', '{}')").lastrowid
    group = group_duplicates([found("1")], {"s": "job_board"})[0]
    ids, _ = jobstore.remember([group], search_id)
    seen = jobstore.first_seen(ids)
    assert abs((seen[ids[0]] - datetime.now(UTC)).total_seconds()) < 60
    assert jobstore.first_seen([]) == {}


def rules(groups, first_shown=None, hours=72):
    return apply_rules(groups, [None] * len(groups), started_at=NOW, posted_within_hours=hours,
                       job_types=list(JOB_TYPES), exclude_remote=False, countries=["DE"],
                       first_shown=first_shown)


def test_a_job_shown_before_the_window_began_is_left_out_as_posted_again():
    # Search 11: Adzuna dated Redline's SMPS job 30 September; Jobcu had shown it on the 22nd.
    groups = group_duplicates([found("1"), found("2"), found("3")], {"s": "job_board"})
    outcome = rules(groups, first_shown=[NOW - timedelta(days=10), NOW - timedelta(hours=60),
                                         None])
    assert [groups[i].main.source_job_id for i in outcome.kept] == ["2", "3"]
    assert dict(outcome.left_out) == {"repost": 1}
    assert "Posted again" in REASONS["repost"]


def career_copy(job_id, days_old, older):
    return found(job_id, source="workday", title="Power Electronics Development Engineer",
                 company="GE Vernova", location_text="Berlin", older_copy=older,
                 posted_at=NOW - timedelta(days=days_old), date_precision="day")


def test_an_older_copy_on_the_employers_site_dates_the_same_job_elsewhere():
    # Search 11: "Posted 4 Days Ago" on GE Vernova's Workday site, dated yesterday on Adzuna.
    board = found("a1", source="adzuna", title="Power Electronics Development Engineer (m/w/d)",
                  company="GE Vernova", location_text="Berlin, Deutschland",
                  posted_at=NOW - timedelta(days=1))
    collected = Collected([board, career_copy("w1", 4, True)], [],
                          {"adzuna": FakeSource("aggregator"), "workday": FakeSource("employer")})
    assert collected.ads_found == 1
    groups = make_groups(collected)
    assert len(groups) == 1 and len(groups[0].copies) == 2
    assert dict(rules(groups).left_out) == {"repost": 1}


def test_older_copies_alone_are_no_job_and_never_count_against_their_own_site():
    alone = career_copy("w1", 9, True)
    # The same title on the same site, fresh: perhaps a second vacancy, so it stays new.
    second = career_copy("w2", 1, False)
    other = found("x", source="workday", title="Hardware Engineer", company="Other GmbH",
                  older_copy=True, posted_at=NOW - timedelta(days=9))
    collected = Collected([alone, second, other], [], {"workday": FakeSource("employer")})
    groups = make_groups(collected)
    assert [[c.source_job_id for c in g.copies] for g in groups] == [["w2"]]
    assert rules(groups).kept == [0]


def test_an_exact_source_id_still_proves_a_repost_when_one_copy_was_redated():
    old = career_copy("same-req", 9, True)
    redated = career_copy("same-req", 1, False)
    collected = Collected([old, redated], [], {"workday": FakeSource("employer")})
    (group,) = make_groups(collected)
    assert len(group.copies) == 2 and group.posted_at == old.posted_at
    assert dict(rules([group]).left_out) == {"repost": 1}


def test_the_closing_date_survives_the_saved_pool_and_the_ad_memory():
    from jobcu import pool

    closes = NOW + timedelta(days=9)
    job = found("1", closes_at=closes, description="Ganze Anzeige.", description_is_complete=True,
                latitude=52.5, longitude=13.4)
    saved = pool.Pool(search_id=41, jobs=[pool.PoolJob(group_duplicates([job], {})[0])],
                      profile={})
    pool.save(saved)
    assert pool.load(41).jobs[0].group.copies[0].closes_at == closes
    # The full ad remembered for a few days keeps its closing date and the page's coordinates.
    jobstore.remember_ad(job)
    summary = found("1")
    again = jobstore.remembered_ad(summary)
    assert again.closes_at == closes and (again.latitude, again.longitude) == (52.5, 13.4)
