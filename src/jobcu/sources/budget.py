"""Keeps job sources within their free usage limits.

Some sources allow only a certain number of requests per day or month (Adzuna: 250 a
day and 2,500 a month). Jobcu counts every request and stops a source before a limit
is reached, and tells the user instead of failing.
"""

import json
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from jobcu import db


@dataclass(frozen=True)
class Limits:
    per_search: int | None = None
    per_day: int | None = None
    per_month: int | None = None


# How far back Jobcu looks to see how many searches a person runs a day.
HABIT_DAYS = 14
AVERAGE_MONTH_DAYS = 365.25 / 12


def share_of_month(
    source: str,
    limits: Limits,
    *,
    hours: float = 24,
    fewest: int = 25,
    most: int = 60,
    now=lambda: datetime.now(UTC),
) -> Limits:
    """This search's equal part of what is left of a monthly free allowance (`share`), between
    `fewest` and `most` for each day the search covers, never more than is left today."""
    if limits.per_month is None:
        return limits
    today = now()
    used_today, used_this_month = _used(source, today)
    start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = (start + timedelta(days=32)).replace(day=1)
    left_this_month = max(0, limits.per_month - used_this_month)
    days = search_days(hours)
    per_search = int(share(left_this_month, start, end, today, hours))
    per_search = max(round(fewest * days), min(round(most * days), per_search))
    if limits.per_day is not None:
        per_search = min(per_search, max(0, limits.per_day - used_today))
    return replace(limits, per_search=per_search)


def share_until(left: int, renews: datetime, *, hours: float = 24, fewest: int, most: int,
                now=lambda: datetime.now(UTC)) -> int:
    """Like share_of_month, for an allowance that renews on its own date rather than on the
    1st: JSearch's runs from the day the account was opened (2026-10-27: 132 credits left
    until 18 November, where the calendar month would have spent them by 31 October)."""
    days = search_days(hours)
    per_search = int(share(left, renews - timedelta(days=AVERAGE_MONTH_DAYS), renews, now(),
                           hours))
    return max(round(fewest * days), min(round(most * days), per_search))


def share(left: float, start: datetime, end: datetime, now: datetime, hours: float) -> float:
    """An equal part of what is left of an allowance that runs from `start` to `end`: what is
    left, times the days this search covers, over the planned search days still to come. The
    owner plans 24 searches a month, each covering a day (a 72-hour search when they missed
    two days counts as three), and wants each allowance divided equally between them."""
    days = search_days(hours)
    return left * days / max(days, search_days_left(start, end, now))


def search_days(hours: float) -> float:
    """The days a search covers: one for 24 hours, three for 72, at least a quarter."""
    return max(0.25, hours / 24)


def search_days_left(start: datetime, end: datetime, now: datetime) -> float:
    """The search days still planned until an allowance renews: the planned searches a month
    (Settings) for this period, less the days the finished searches since `start` covered; when
    the person searches more than planned, the planned pace over the days left instead, so the
    allowance still lasts. Without a plan, the person's recent searches a day."""
    from jobcu.settings import load_settings

    days_left = max(0.0, (end - now).total_seconds() / 86400)
    planned = load_settings().limits.searches_per_month
    if not planned:
        return max(1.0, days_left * searches_a_day(now))
    # Every allowance here renews monthly, and the plan is that many searches each month.
    period_days = max(1.0, (end - start).total_seconds() / 86400)
    return max(planned - _days_covered(start, now), planned * days_left / period_days)


def _days_covered(start: datetime, now: datetime) -> float:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT form_json FROM searches WHERE status = 'finished' AND started_at >= ? "
            "AND started_at < ?",
            (_stamp(start), _stamp(now))).fetchall()
    covered = 0.0
    for (form,) in rows:
        try:
            hours = json.loads(form).get("posted_within_hours") or 24
        except (ValueError, AttributeError):
            hours = 24
        covered += search_days(hours)
    return covered


def _stamp(when: datetime) -> str:
    return when.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")


def searches_a_day(now: datetime) -> float:
    """The searches a day the person plans (Settings: searches a month), or else ran in the
    last two weeks: at least one."""
    from jobcu.settings import load_settings

    planned = load_settings().limits.searches_per_month
    if planned:
        return planned / AVERAGE_MONTH_DAYS
    since = (now - timedelta(days=HABIT_DAYS)).strftime("%Y-%m-%dT%H:%M:%S")
    with db.connect() as conn:
        searches = conn.execute(
            "SELECT COUNT(*) FROM searches WHERE started_at >= ?", (since,)
        ).fetchone()[0]
    return max(1.0, searches / HABIT_DAYS)


def month_usage(source: str, now: datetime) -> tuple[int, int]:
    """What a source used today and this month (requests or billed items)."""
    return _used(source, now)


def _used(source: str, now: datetime) -> tuple[int, int]:
    day = now.strftime("%Y-%m-%d")
    with db.connect() as conn:
        today = conn.execute(
            "SELECT COALESCE(SUM(count), 0) FROM source_requests WHERE source = ? AND day = ?",
            (source, day),
        ).fetchone()[0]
        month = conn.execute(
            "SELECT COALESCE(SUM(count), 0) FROM source_requests "
            "WHERE source = ? AND substr(day, 1, 7) = ?",
            (source, day[:7]),
        ).fetchone()[0]
    return today, month


class BudgetExhausted(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RequestBudget:
    def __init__(self, source: str, name: str, limits: Limits, now=lambda: datetime.now(UTC)):
        self.source = source
        self.name = name
        self.limits = limits
        self.used_this_search = 0
        self._now = now
        self._lock = threading.Lock()

    def spend(self, count: int = 1) -> None:
        """Count one request (or `count` billed items), or raise BudgetExhausted if a limit
        would be passed."""
        self._use(count, commit=True)

    def check(self, count: int = 1) -> None:
        """Check allowance before waiting; spending rechecks it atomically before sending."""
        self._use(count, commit=False)

    def _use(self, count: int, *, commit: bool) -> None:
        with self._lock:
            today = self._now().strftime("%Y-%m-%d")
            month = today[:7]
            with db.connect() as conn:
                if commit:
                    conn.execute("BEGIN IMMEDIATE")
                used_today = conn.execute(
                    "SELECT COALESCE(SUM(count), 0) FROM source_requests "
                    "WHERE source = ? AND day = ?",
                    (self.source, today),
                ).fetchone()[0]
                used_month = conn.execute(
                    "SELECT COALESCE(SUM(count), 0) FROM source_requests "
                    "WHERE source = ? AND substr(day, 1, 7) = ?",
                    (self.source, month),
                ).fetchone()[0]
                if self.limits.per_search is not None and (
                    self.used_this_search + count > self.limits.per_search
                ):
                    # Not always a free allowance (Adzuna's is): some sources only have Jobcu's own
                    # cap per search, so the message says what happened, not why.
                    raise BudgetExhausted(
                        f"{self.name}: reached the most requests Jobcu sends it in one search, so "
                        "some of its jobs may not have been read."
                    )
                if self.limits.per_day is not None and used_today + count > self.limits.per_day:
                    raise BudgetExhausted(
                        f"{self.name}: today's free requests are used up. It will work again "
                        "tomorrow."
                    )
                if self.limits.per_month is not None and (
                    used_month + count > self.limits.per_month
                ):
                    raise BudgetExhausted(
                        f"{self.name}: this month's free requests are used up. It will work again "
                        "next month."
                    )
                if commit:
                    conn.execute(
                        "INSERT INTO source_requests (day, source, count) VALUES (?, ?, ?) "
                        "ON CONFLICT (day, source) DO UPDATE SET count = count + excluded.count",
                        (today, self.source, count),
                    )
            if commit:
                self.used_this_search += count
