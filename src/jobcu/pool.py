"""The jobs of the latest search that the conditions about places decide about.

After a search, the person may correct how Jobcu read their location and apply the corrected
conditions to the jobs already found, without searching again.
For that, Jobcu keeps every job of the latest search that passed the other rules (dates, job
types, remote, countries, Not interested), together with what the search already worked out for
each one: the quick relevance check and the score. Jobs that come back in are checked and scored
then; nothing already worked out is asked of the AI twice.

Only the latest search is kept. It stays on this computer with the rest of the search results.
"""

import dataclasses
import json
from dataclasses import dataclass, field

from jobcu import db
from jobcu.dedupe import JobGroup
from jobcu.freshness import parse_iso
from jobcu.sources.base import FoundJob


@dataclass
class PoolJob:
    group: JobGroup
    unrelated: bool | None = None  # the quick relevance check's answer; None before it ran
    scored: dict | None = None  # the score and what scoring read from the ad
    online_evidence: dict | None = None  # completed lookup, kept before any later batch fails


@dataclass
class Pool:
    search_id: int
    jobs: list[PoolJob]
    profile: dict
    # What the rest of the search found, for the counts and "Search details".
    left_out: dict[str, int] = field(default_factory=dict)  # by the other rules, per reason
    reports: list[dict] = field(default_factory=list)
    source_names: dict[str, str] = field(default_factory=dict)
    ads_found: int = 0
    different_jobs: int = 0
    hidden_cards: list[dict] = field(default_factory=list)
    research_notes: dict[str, dict] = field(default_factory=dict)


def save(pool: Pool) -> None:
    """Keeps this pool and forgets older ones."""
    with db.connect() as conn:
        conn.execute("DELETE FROM search_pool WHERE search_id != ?", (pool.search_id,))
        conn.execute(
            "INSERT OR REPLACE INTO search_pool (search_id, pool_json) VALUES (?, ?)",
            (pool.search_id, json.dumps(_to_dict(pool))),
        )


def load(search_id: int) -> Pool | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT pool_json FROM search_pool WHERE search_id = ?", (search_id,)
        ).fetchone()
    if row is None:
        return None
    try:
        return _from_dict(json.loads(row["pool_json"]))
    except (ValueError, KeyError, TypeError):
        return None  # written by an older Jobcu: the conditions can't be changed afterwards


def exists(search_id: int) -> bool:
    with db.connect() as conn:
        return conn.execute(
            "SELECT 1 FROM search_pool WHERE search_id = ?", (search_id,)
        ).fetchone() is not None


def group_to_dict(group: JobGroup) -> dict:
    """One job group as plain JSON data; `group_from_dict` reads it back."""
    data = dataclasses.asdict(group)
    for copy, stored in zip(group.copies, data["copies"], strict=True):
        for name in ("posted_at", "closes_at"):
            when = getattr(copy, name)
            stored[name] = when.isoformat() if when else None
    return data


def group_from_dict(group: dict) -> JobGroup:
    copies = [
        FoundJob(**{**copy, "posted_at": parse_iso(copy["posted_at"]),
                    "closes_at": parse_iso(copy.get("closes_at"))})
        for copy in group["copies"]
    ]
    return JobGroup(copies=copies, possible_duplicate_of=group["possible_duplicate_of"],
                    source_kinds=group["source_kinds"],
                    place_from_text=group.get("place_from_text"),
                    place_from_web=group.get("place_from_web"))


def _to_dict(pool: Pool) -> dict:
    data = dataclasses.asdict(pool)
    for job, stored in zip(pool.jobs, data["jobs"], strict=True):
        stored["group"] = group_to_dict(job.group)
    return data


def _from_dict(data: dict) -> Pool:
    jobs = []
    for stored in data.pop("jobs"):
        jobs.append(PoolJob(
            group=group_from_dict(stored["group"]),
            unrelated=stored["unrelated"],
            scored=stored["scored"],
            online_evidence=stored.get("online_evidence"),
        ))
    return Pool(jobs=jobs, **data)
