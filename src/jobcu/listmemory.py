"""When Jobcu first saw each job on an employer's own job list.

Some career sites give their jobs no posting date: 13 of the 49 SuccessFactors sites read in
November 2026, large engineering employers among them. Every job of theirs stayed under "Posting
date unknown", however new, and an old one could not show that a job site's fresh copy of it was
a repost. The list itself still tells when a job appears: one that wasn't there at the last
reading and is there now was posted in between. So Jobcu remembers, for each list it reads
whole, every job's first sight and the reading before it (`note`), and dates a job without a
date from that (`posted`):

- first seen within FIRST_SIGHT_GAP of a reading that didn't have it: posted on the day it was
  first seen, to the day, like the sites that give only a day;
- on the list since before the search's window began: older than the window, though by how
  much isn't known. That is all the "Posted within" rule and the repost check need;
- otherwise (a list's first reading, or a first sight after a longer pause): unknown, as before.

Only a list's public job numbers and the reading times are kept, in the person's data folder;
a full reset removes them.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jobcu import db
from jobcu.freshness import day_at_utc, parse_iso

# A job that appeared between two readings this far apart was posted "on the day it was first
# seen", give or take a day: the precision of a site that gives only days. Searches a day apart
# fit, also when the second starts some hours later; after a longer pause the day isn't known.
FIRST_SIGHT_GAP = timedelta(hours=36)


# A reading in which most of a list is new shows a list that changed its numbering or wasn't
# read whole before, not that many new jobs: no employer posts half its list in a day. Those
# jobs get no date, like a first reading's. Small lists can turn over in a day.
MANY_NEW = 20


@dataclass(frozen=True)
class Sight:
    first_seen_at: datetime
    # The list's last reading before that, which didn't have the job; None for a job that was
    # there when Jobcu first read the list.
    absent_at: datetime | None = None


def note(source: str, board: str, job_ids: Iterable[str],
         now: datetime | None = None) -> dict[str, Sight]:
    """Records one reading of an employer's whole list and returns each listed job's first
    sight. A job that leaves the list and comes back keeps its first sight."""
    now = now or datetime.now(UTC)
    stamp = now.isoformat(timespec="seconds")
    ids = list(dict.fromkeys(job_ids))
    if not ids:
        return {}  # an empty answer is no reading: after it, every job would look new
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")  # two readings of one list never both see "no reading"
        reading = conn.execute(
            "SELECT read_at FROM list_readings WHERE source = ? AND board = ?",
            (source, board)).fetchone()
        previous = reading["read_at"] if reading else None
        known = {row["job_id"]: (row["first_seen_at"], row["absent_at"]) for row in conn.execute(
            "SELECT job_id, first_seen_at, absent_at FROM listed_jobs "
            "WHERE source = ? AND board = ?", (source, board))}
        new = [job_id for job_id in ids if job_id not in known]
        if len(new) >= MANY_NEW and len(new) > len(ids) / 2:
            previous = None
        conn.executemany(
            "INSERT INTO listed_jobs (source, board, job_id, first_seen_at, absent_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [(source, board, job_id, stamp, previous) for job_id in new])
        conn.execute("INSERT OR REPLACE INTO list_readings (source, board, read_at) "
                     "VALUES (?, ?, ?)", (source, board, stamp))
    sights = {}
    for job_id in ids:
        first, absent = known.get(job_id, (stamp, previous))
        sights[job_id] = Sight(parse_iso(first) or now, parse_iso(absent))
    return sights


def posted(sight: Sight | None, start: datetime | None) -> tuple[datetime | None, str]:
    """The posting date a job's first sight proves, with its precision: `(None, "unknown")`
    when it proves none. `start` is where the search's "Posted within" window begins."""
    if sight is None:
        return None, "unknown"
    if sight.absent_at is not None and sight.first_seen_at - sight.absent_at <= FIRST_SIGHT_GAP:
        return day_at_utc(sight.first_seen_at.date()), "day"
    if start is not None and sight.first_seen_at < start:
        return sight.first_seen_at, "exact"
    return None, "unknown"
