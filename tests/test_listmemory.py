"""A job's first sight on an employer's own list dates it where its page gives no date."""

from datetime import UTC, datetime, timedelta

import pytest

from jobcu import listmemory
from jobcu.freshness import freshness

NOW = datetime(2026, 11, 14, 18, 0, tzinfo=UTC)
DAY = timedelta(days=1)


def read(ids, when):
    return listmemory.note("fictional-system", "jobs.fake.example", ids, when)


def test_a_job_that_appears_between_two_readings_a_day_apart_was_posted_on_that_day():
    read(["1", "2"], NOW - DAY)
    sights = read(["1", "2", "3"], NOW)
    posted, precision = listmemory.posted(sights["3"], NOW - DAY)
    assert (posted.date(), precision) == (NOW.date(), "day")
    assert freshness(posted, precision, NOW - DAY) == "fresh"
    # A later search knows the same day, however often the list is read.
    later = read(["1", "2", "3"], NOW + 3 * DAY)
    assert listmemory.posted(later["3"], NOW + 2 * DAY) == (posted, "day")
    assert freshness(posted, "day", NOW + 2 * DAY) == "too_old"


def test_a_job_on_the_list_at_its_first_reading_has_no_date_until_the_window_has_passed_it():
    sights = read(["1", "2"], NOW)
    # It may be a day old or a year old: nothing dates it in the search that first reads it.
    assert listmemory.posted(sights["1"], NOW - DAY) == (None, "unknown")
    # In a later search it is known to be older than the window, which is all the rule needs.
    later = read(["1", "2"], NOW + 2 * DAY)
    posted, precision = listmemory.posted(later["1"], NOW + DAY)
    assert freshness(posted, precision, NOW + DAY) == "too_old"
    assert listmemory.posted(later["1"], None) == (None, "unknown")  # no window: no claim


def test_a_job_first_seen_after_a_long_pause_stays_undated():
    # A week without a search: the job appeared some day in between, and "Posted within 24
    # hours" must not take it for today's.
    read(["1"], NOW - 7 * DAY)
    sights = read(["1", "2"], NOW)
    assert listmemory.posted(sights["2"], NOW - DAY) == (None, "unknown")
    # Searches a day apart still fit when the second one starts some hours later.
    read(["1", "2"], NOW + DAY)
    sights = read(["1", "2", "3"], NOW + 2 * DAY + timedelta(hours=5))
    assert listmemory.posted(sights["3"], NOW + DAY)[1] == "day"


def test_a_job_that_leaves_the_list_and_comes_back_keeps_its_first_sight():
    read(["1", "2"], NOW - 3 * DAY)
    read(["1"], NOW - 2 * DAY)
    sights = read(["1", "2"], NOW)
    assert sights["2"].first_seen_at == NOW - 3 * DAY


def test_an_empty_answer_is_no_reading():
    assert read([], NOW - DAY) == {}
    sights = read(["1", "2"], NOW)
    # Nothing was known before: this is the list's first reading, and dates nothing.
    assert all(sight.absent_at is None for sight in sights.values())


@pytest.mark.parametrize("listed_before", [0, 30])
def test_a_list_that_is_mostly_new_at_once_changed_its_numbering_and_dates_nothing(listed_before):
    old = [f"old-{i}" for i in range(listed_before)] or ["only"]
    read(old, NOW - DAY)
    renumbered = [f"new-{i}" for i in range(40)]
    sights = read([*old[:5], *renumbered], NOW)
    assert listmemory.posted(sights["new-0"], NOW - DAY) == (None, "unknown")
    # A small employer's list can turn over in a day; a few new jobs on a long list are news.
    read(["a", "b"], NOW - DAY)
    assert listmemory.posted(read(["c", "d", "e"], NOW)["c"], NOW - DAY)[1] == "day"
    again = read([*old[:5], *renumbered, "one-more"], NOW + DAY)
    assert listmemory.posted(again["one-more"], NOW)[1] == "day"


def test_lists_are_remembered_apart():
    read(["1"], NOW - DAY)
    other = listmemory.note("fictional-system", "jobs.other.example", ["1", "2"], NOW)
    assert other["2"].absent_at is None  # that list's own first reading
