"""What Jobcu remembers about jobs between searches (HANDOVER section 12).

Only this is remembered: which jobs were shown before (for the "New" badge), which the user
marked Saved, Applied or Not interested, and the **text of ads already downloaded**, for a few
days, so the same ad isn't fetched again (DECISIONS.md). A job is recognised again through any
of its copies, so if one copy was marked Not interested, every copy stays hidden. Scores and
everything else about a search are always made fresh.
"""

import dataclasses
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jobcu import db
from jobcu.dedupe import JobGroup
from jobcu.freshness import parse_iso
from jobcu.jobidentity import IdentityIndex, copy_key, fingerprints, rows
from jobcu.jobidentity import identity_keys as identity_keys  # preserved helper for local tools
from jobcu.sources.base import FoundJob

# How long a downloaded ad text is trusted. Job ads barely change while they are open.
AD_TEXT_DAYS = 3
# What reading the full ad adds to what a source's job list already gave.
AD_DETAIL_FIELDS = ("description", "description_is_complete", "job_types", "work_mode",
                    "employer_url", "salary_text", "company", "posted_at", "closes_at",
                    "latitude", "longitude", "title", "location_text", "country",
                    "date_precision")
_TIMES = ("posted_at", "closes_at")


@dataclass
class JobState:
    saved: bool = False
    applied: bool = False
    dismissed: bool = False


def find_job_ids(groups: list[JobGroup]) -> list[int | None]:
    """The remembered job for each group, or None if this job was never seen."""
    with db.connect() as conn:
        index = IdentityIndex.load(conn, groups)
        return [index.resolve(group) for group in groups]


def states(job_ids: list[int]) -> dict[int, JobState]:
    if not job_ids:
        return {}
    with db.connect() as conn:
        return {row[0]: JobState(bool(row[1]), bool(row[2]), bool(row[3])) for row in rows(
            conn, "SELECT job_id, saved, applied, dismissed FROM job_states WHERE job_id IN ({})",
            job_ids)}


def remember(groups: list[JobGroup], search_id: int) -> tuple[list[int], list[bool]]:
    """Record the jobs shown in a search. Returns each job's id and whether it's new."""
    ids: list[int] = []
    new: list[bool] = []
    with db.connect() as conn:
        # Serialize identity allocation, so another writer cannot register these copies
        # between the lookup and bulk save. Owner marks are never rewritten here.
        conn.execute("BEGIN IMMEDIATE")
        index = IdentityIndex.load(conn, groups)
        existing = [job_id for group in groups if (job_id := index.resolve(group)) is not None]
        first_search = {row[0]: row[1] for row in rows(
            conn, "SELECT id, first_seen_search_id FROM jobs WHERE id IN ({})", existing)}
        copy_rows, name_rows = [], []
        for group in groups:
            job_id = index.resolve(group)
            if job_id is None:
                job_id = conn.execute(
                    "INSERT INTO jobs (first_seen_search_id, title, company) VALUES (?, ?, ?)",
                    (search_id, group.main.title, group.main.company),
                ).lastrowid
                first_search[job_id] = search_id
            new.append(first_search[job_id] == search_id)
            copy_rows.extend((copy_key(c.source, c.source_job_id), job_id)
                             for c in group.copies if c.source_job_id)
            name_rows.extend((key, job_id, country) for key, country in fingerprints(group))
            index.register(group, job_id)
            ids.append(job_id)
        conn.executemany("INSERT OR IGNORE INTO job_keys (key, job_id) VALUES (?, ?)", copy_rows)
        conn.executemany(
            "INSERT OR IGNORE INTO job_fingerprints (key, job_id, country) VALUES (?, ?, ?)",
            name_rows)
    return ids, new


def first_seen(job_ids: list[int]) -> dict[int, datetime]:
    """When Jobcu first showed each job, to tell a repost of an old ad from a new job."""
    if not job_ids:
        return {}
    with db.connect() as conn:
        return {row[0]: when for row in rows(
            conn, "SELECT id, first_seen_at FROM jobs WHERE id IN ({})", job_ids)
                if (when := parse_iso(row[1])) is not None}


def set_state(job_id: int, **changes: bool) -> JobState:
    allowed = {"saved", "applied", "dismissed"}
    changes = {k: bool(v) for k, v in changes.items() if k in allowed}
    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone() is None:
            raise KeyError(job_id)
        conn.execute("INSERT OR IGNORE INTO job_states (job_id) VALUES (?)", (job_id,))
        for name, value in changes.items():
            conn.execute(
                f"UPDATE job_states SET {name} = ?, "
                "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE job_id = ?",
                (int(value), job_id),
            )
    return states([job_id])[job_id]


def finish_search(search_id: int, status: str, result_json: str | None) -> None:
    """Commit the final results and search status together, before reporting completion."""
    with db.connect() as conn:
        if result_json is not None:
            conn.execute(
                "INSERT OR REPLACE INTO search_results (search_id, result_json) VALUES (?, ?)",
                (search_id, result_json),
            )
        conn.execute(
            "UPDATE searches SET status = ?, finished_at = ? WHERE id = ?",
            (status, datetime.now(UTC).isoformat(timespec="seconds"), search_id),
        )


def latest_results() -> tuple[int, str] | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT search_id, result_json FROM search_results ORDER BY search_id DESC LIMIT 1"
        ).fetchone()
    return (row[0], row[1]) if row else None


def save_cards(cards: list[dict]) -> None:
    with db.connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO job_cards (job_id, card_json) VALUES (?, ?)",
            [(card["job_id"], json.dumps(card)) for card in cards],
        )


def marked_cards(kind: str) -> list[dict]:
    """Cards of every job marked Saved or Applied, newest change first."""
    if kind not in ("saved", "applied"):
        return []
    with db.connect() as conn:
        rows = conn.execute(
            f"SELECT c.card_json, s.saved, s.applied, s.dismissed FROM job_states s "
            f"JOIN job_cards c ON c.job_id = s.job_id WHERE s.{kind} = 1 "
            "ORDER BY s.updated_at DESC"
        ).fetchall()
    cards = []
    for row in rows:
        card = json.loads(row[0])
        card["state"] = {"saved": bool(row[1]), "applied": bool(row[2]), "dismissed": bool(row[3])}
        cards.append(card)
    return cards


def remember_ad(job: FoundJob) -> None:
    """Keeps the text of a full ad, so the next search doesn't download it again."""
    if not job.description_is_complete or not job.source_job_id:
        return
    details = {field: getattr(job, field) for field in AD_DETAIL_FIELDS}
    for name in _TIMES:
        details[name] = details[name].isoformat() if details[name] else None
    with db.connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ad_texts (source, source_job_id, fetched_at, details_json) "
            "VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'), ?)",
            (job.source, job.source_job_id, json.dumps(details)),
        )
        conn.execute(
            "DELETE FROM ad_texts WHERE fetched_at < ?",
            ((datetime.now(UTC) - timedelta(days=AD_TEXT_DAYS)).isoformat(),),
        )


def remembered_ad(job: FoundJob) -> FoundJob | None:
    """The same ad's text from an earlier search, if it was downloaded in the last few days."""
    if not job.source_job_id:
        return None
    since = (datetime.now(UTC) - timedelta(days=AD_TEXT_DAYS)).isoformat()
    with db.connect() as conn:
        row = conn.execute(
            "SELECT details_json FROM ad_texts WHERE source = ? AND source_job_id = ? "
            "AND fetched_at >= ?",
            (job.source, job.source_job_id, since),
        ).fetchone()
    if row is None:
        return None
    try:
        details = json.loads(row["details_json"])
    except ValueError:
        return None
    details = {field: value for field, value in details.items()
               if field in AD_DETAIL_FIELDS and value not in (None, "", [])}
    if not details.get("description"):
        return None
    for name in _TIMES:
        if name in details:
            details[name] = parse_iso(details[name]) or getattr(job, name)
    return dataclasses.replace(job, **details)
