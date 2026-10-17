"""What Jobcu remembers about jobs between searches.

Only this is remembered: which jobs were shown before (for the "New" badge), which the user
marked Saved, Applied or Not interested, and the **text of ads already downloaded**, for a few
days, so the same ad isn't fetched again. A job is recognised again through any
of its copies, so if one copy was marked Not interested, every copy stays hidden. Scores and
everything else about a search are always made fresh.
"""

import dataclasses
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from jobcu import db
from jobcu.dedupe import JobGroup, group_duplicates
from jobcu.freshness import parse_iso
from jobcu.jobidentity import IdentityIndex, aliases, copy_key, family_ids, rows
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
        linked = aliases(conn)
        found: dict[int, JobState] = {}
        for row in rows(
            conn, "SELECT job_id, saved, applied, dismissed FROM job_states WHERE job_id IN ({})",
            family_ids(job_ids, linked)):
            state = found.setdefault(linked.get(row[0], row[0]), JobState())
            state.saved |= bool(row[1])
            state.applied |= bool(row[2])
            state.dismissed |= bool(row[3])
        return {job_id: found[root] for job_id in job_ids
                if (root := linked.get(job_id, job_id)) in found}


def _link_copies(conn, groups: list[JobGroup]) -> None:
    groups = [g for g in groups if len(g.copies) > 1]
    if not groups:
        return
    linked = aliases(conn)
    keys = [copy_key(c.source, c.source_job_id)
            for g in groups for c in g.copies if c.source_job_id]
    known = {r[0]: r[1] for r in rows(
        conn, "SELECT key, job_id FROM job_keys WHERE key IN ({})", keys)}
    for group in groups:
        ids = {linked.get(known[key], known[key]) for c in group.copies if c.source_job_id
               and (key := copy_key(c.source, c.source_job_id)) in known}
        if len(ids) < 2 or len(group_duplicates(group.copies, group.source_kinds)) != 1:
            continue
        employer_ids = defaultdict(set)
        for row in rows(conn, "SELECT key, job_id FROM job_keys WHERE job_id IN ({}) "
                             "AND key LIKE 'copy:%'", family_ids(ids, linked)):
            _, source, vacancy = row[0].split(":", 2)
            if group.source_kinds.get(source) == "employer":
                employer_ids[source].add(vacancy)
        if any(len(vacancies) > 1 for vacancies in employer_ids.values()):
            continue  # a recycled board copy cannot bridge two employer requisitions
        root = min(ids)
        children = family_ids(ids, linked) - {root}
        conn.executemany("INSERT OR REPLACE INTO job_aliases (job_id, canonical_id) VALUES (?, ?)",
                         [(child, root) for child in children])
        linked.update({child: root for child in children})


def link_copies(groups: list[JobGroup]) -> None:
    """Link only currently confirmed duplicate copies before filtering or paid assessment."""
    if not any(len(g.copies) > 1 for g in groups):
        return
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        _link_copies(conn, groups)


def remember(groups: list[JobGroup], search_id: int) -> tuple[list[int], list[bool]]:
    """Record the jobs shown in a search. Returns each job's id and whether it's new."""
    ids: list[int] = []
    new: list[bool] = []
    with db.connect() as conn:
        # Serialize identity allocation, so another writer cannot register these copies
        # between the lookup and bulk save. Owner marks are never rewritten here.
        conn.execute("BEGIN IMMEDIATE")
        _link_copies(conn, groups)
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
            name_rows.extend((key, job_id, country) for key, country in index.name_entries(group))
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
        linked = aliases(conn)
        found = {}
        for row in rows(conn, "SELECT id, first_seen_at FROM jobs WHERE id IN ({})",
                        family_ids(job_ids, linked)):
            if (when := parse_iso(row[1])) is not None:
                root = linked.get(row[0], row[0])
                found[root] = min(found.get(root, when), when)
        return {job_id: found[root] for job_id in job_ids
                if (root := linked.get(job_id, job_id)) in found}


def canonical_ids(job_ids: list[int]) -> dict[int, int]:
    with db.connect() as conn:
        linked = aliases(conn)
        return {job_id: linked.get(job_id, job_id) for job_id in job_ids}


def set_state(job_id: int, **changes: bool) -> JobState:
    allowed = {"saved", "applied", "dismissed"}
    changes = {k: bool(v) for k, v in changes.items() if k in allowed}
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone() is None:
            raise KeyError(job_id)
        linked = aliases(conn)
        members = family_ids([job_id], linked)
        conn.executemany("INSERT OR IGNORE INTO job_states (job_id) VALUES (?)",
                         [(member,) for member in members])
        for name, value in changes.items():
            conn.executemany(
                f"UPDATE job_states SET {name} = ?, "
                "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE job_id = ?",
                [(int(value), member) for member in members],
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
        linked = aliases(conn)
        rows = conn.execute(
            f"SELECT c.card_json, s.saved, s.applied, s.dismissed FROM job_states s "
            f"JOIN job_cards c ON c.job_id = s.job_id WHERE s.{kind} = 1 "
            "ORDER BY s.updated_at DESC"
        ).fetchall()
        stored_cards = {row[0]: row[1] for row in conn.execute(
            "SELECT job_id, card_json FROM job_cards WHERE job_id IN ("
            "SELECT canonical_id FROM job_aliases)")}
    cards = []
    seen = set()
    for row in rows:
        card = json.loads(row[0])
        root = linked.get(card["job_id"], card["job_id"])
        if root in seen:
            continue
        seen.add(root)
        card = json.loads(stored_cards[root]) if root in stored_cards else card
        card["job_id"] = root
        cards.append(card)
    combined = states([c["job_id"] for c in cards])
    for card in cards:
        card["state"] = dataclasses.asdict(combined.get(card["job_id"], JobState()))
    return cards


def remember_ad(job: FoundJob, *, reader_version: int = 1) -> None:
    """Keeps the text of a full ad, so the next search doesn't download it again."""
    if not job.description_is_complete or not job.source_job_id:
        return
    details = {field: getattr(job, field) for field in AD_DETAIL_FIELDS}
    details["_reader_version"] = reader_version
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


def remembered_ad(job: FoundJob, *, reader_version: int = 1) -> FoundJob | None:
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
    if not isinstance(details, dict) or details.get("_reader_version", 1) != reader_version:
        return None
    details = {field: value for field, value in details.items()
               if field in AD_DETAIL_FIELDS and value not in (None, "", [])}
    if not details.get("description"):
        return None
    for name in _TIMES:
        if name in details:
            details[name] = parse_iso(details[name]) or getattr(job, name)
    return dataclasses.replace(job, **details)
