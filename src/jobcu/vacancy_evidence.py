"""Verified evidence about exact saved vacancies; no collection or provider calls.

Keep original publication bounds and explicit closure separate from board refresh dates,
Jobcu's first showing, scores and owner marks. A reader/reviewer must verify the same vacancy;
a loading/error page, another requisition or a company-level statement is not evidence.
"""

from collections import Counter
from datetime import datetime
from urllib.parse import urlsplit

from jobcu import db, jobstore
from jobcu.freshness import parse_iso, window_start
from jobcu.jobidentity import aliases

CLOSED = "The original confirms this vacancy is unavailable"
OLD = 'The verified original predates your "Posted within" choice'
REASONS = {"verified_closed": CLOSED, "original_date": OLD}


def record(job_id: int, kind: str, source_url: str, note: str, *,
           posted_before: datetime | None = None) -> int:
    """Record an independently verified original fact, never a guessed posting date.

    A conservative latest-possible publication bound suffices; it is not an exact date.
    No owner mark, key, snapshot or original job row is changed. Undo removes only this fact.
    """
    try:
        parsed = urlsplit(source_url)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        valid = False
    if (not valid or not note.strip() or kind not in {"closed", "posted_before"}
            or kind == "posted_before" and (posted_before is None or posted_before.tzinfo is None)):
        raise ValueError("Verified vacancy evidence needs its source, fact and date bound.")
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone():
            raise KeyError(job_id)
        value = posted_before.isoformat() if posted_before else None
        existing = conn.execute(
            "SELECT id FROM vacancy_evidence WHERE job_id=? AND kind=? AND value IS ? "
            "AND source_url=? AND note=?", (job_id, kind, value, source_url, note.strip()),
        ).fetchone()
        if existing:
            return existing[0]
        return conn.execute(
            "INSERT INTO vacancy_evidence (job_id, kind, value, source_url, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (job_id, kind, value, source_url, note.strip()),
        ).lastrowid


def records() -> list[dict]:
    with db.connect() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT v.*, j.title, j.company FROM vacancy_evidence v JOIN jobs j "
            "ON j.id = v.job_id ORDER BY v.id DESC")]


def undo(evidence_id: int) -> None:
    with db.connect() as conn:
        if not conn.execute("DELETE FROM vacancy_evidence WHERE id = ?", (evidence_id,)).rowcount:
            raise KeyError(evidence_id)


def reasons(job_ids: list[int], start: datetime | None) -> dict[int, str]:
    if not job_ids:
        return {}
    with db.connect() as conn:
        linked = aliases(conn)
        wanted = {linked.get(job_id, job_id) for job_id in job_ids}
        found = {}
        for row in conn.execute("SELECT job_id, kind, value FROM vacancy_evidence"):
            root = linked.get(row[0], row[0])
            if root not in wanted:
                continue
            if row[1] == "closed":
                found[root] = "verified_closed"
            elif (start and (bound := parse_iso(row[2])) and bound < start
                  and root not in found):
                found[root] = "original_date"
        return {job_id: found[root] for job_id in job_ids
                if (root := linked.get(job_id, job_id)) in found}


def group_reasons(groups, start: datetime) -> dict[int, str]:
    if not groups:
        return {}
    with db.connect() as conn:
        if not conn.execute("SELECT 1 FROM vacancy_evidence LIMIT 1").fetchone():
            return {}
    ids = jobstore.find_job_ids(groups)
    excluded = reasons([job_id for job_id in ids if job_id is not None], start)
    return {i: excluded[job_id] for i, job_id in enumerate(ids) if job_id in excluded}


def annotate(card: dict, closed_ids: set[int] | None = None) -> dict:
    """Saved/Applied history survives; a confirmed closed destination is not offered."""
    known = closed_ids if closed_ids is not None else reasons([card["job_id"]], None)
    if card["job_id"] not in known:
        return card
    return {**card, "main_link": {"source": "", "url": ""}, "also_on": [],
            "application_link_unavailable": True,
            "score_checks": [*card.get("score_checks", []), {"text": CLOSED, "status": "info"}]}


def filter_snapshot(snapshot: dict) -> None:
    """Only the current recommendation view changes; saved snapshots remain intact."""
    jobs = (snapshot.get("result") or {}).get("jobs")
    if not jobs:
        return
    sections = [s for s in ("cards", "date_unknown", "location_unchecked") if s in jobs]
    ids = [c["job_id"] for section in sections for c in jobs[section]]
    started = parse_iso(snapshot.get("started_at"))
    hours = (snapshot.get("form") or {}).get("posted_within_hours")
    start = window_start(started, hours) if started and hours else None
    excluded = reasons(ids, start)
    if not excluded:
        return
    removed = Counter()
    for section in sections:
        kept = []
        for card in jobs[section]:
            if reason := excluded.get(card["job_id"]):
                removed[reason] += 1
            else:
                kept.append(card)
        jobs[section] = kept
    counts = jobs.setdefault("counts", {})
    shown = [c for section in sections for c in jobs[section]]
    counts["shown"] = len(shown)
    if "location_unchecked" in jobs:
        counts["location_unchecked"] = len(jobs["location_unchecked"])
    counts["left_out"] = [*counts.get("left_out", []),
                          *({"reason": REASONS[kind], "count": count}
                            for kind, count in removed.items())]
    jobs["new_count"] = sum(bool(c.get("is_new")) for c in shown)
