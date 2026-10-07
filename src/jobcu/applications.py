"""Application links: exclude known unusable destinations without fetching private URLs."""

import json
from collections import Counter
from urllib.parse import parse_qsl, urlsplit

from jobcu import db
from jobcu.dedupe import SOURCE_KIND_RANK, JobGroup, is_agency

BLOCKED_HOSTS = frozenset({"cv-library.co.uk"})
REDIRECT_FIELDS = frozenset({"url", "redirect", "redirect_url", "target", "destination", "to"})
EXCLUSION_REASON = "CV-Library application route, with no other saved link"
REPORTED_EXCLUSION_REASON = "Application link marked unusable, with no other saved link"


def reported_urls() -> set[str]:
    with db.connect() as conn:
        return {row[0] for row in conn.execute("SELECT url FROM application_link_reports")}


def reports() -> list[dict]:
    with db.connect() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT r.id, r.url, r.source, j.title, j.company FROM application_link_reports r "
            "JOIN jobs j ON j.id = r.job_id ORDER BY r.id DESC"
        )]


def report_link(job_id: int, url: str) -> None:
    """Accept only an existing saved link; never fetch it or infer its final host."""
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Choose an available job link.")
    with db.connect() as conn:
        row = conn.execute("SELECT card_json FROM job_cards WHERE job_id = ?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        card = json.loads(row[0])
        links = [card.get("main_link") or {}, *card.get("also_on", [])]
        link = next((link for link in links if link.get("url") == url), None)
        if not url or link is None:
            raise ValueError("That link is no longer saved for this job. Refresh the job list.")
        if blocked(url):
            raise ValueError("Jobcu already excludes this application destination.")
        conn.execute(
            "INSERT OR IGNORE INTO application_link_reports (url, job_id, source) VALUES (?, ?, ?)",
            (url, job_id, link.get("source", "")),
        )


def undo_report(report_id: int) -> None:
    with db.connect() as conn:
        if not conn.execute("DELETE FROM application_link_reports WHERE id = ?",
                            (report_id,)).rowcount:
            raise KeyError(report_id)


def opaque(url: str | None) -> bool:
    if not url:
        return False
    try:
        host = (urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    parts = host.split(".")
    return (len(parts) >= 2 and parts[-2] == "adzuna") or (
        len(parts) >= 3 and parts[-3] == "adzuna" and parts[-2] in {"co", "com"})


def blocked(url: str | None, depth: int = 0) -> bool:
    if not url:
        return False
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    if any(host == site or host.endswith("." + site) for site in BLOCKED_HOSTS):
        return True
    # Some trackers expose their destination; opaque IDs cannot prove a final host.
    return depth < 3 and any(
        blocked(value, depth + 1) for key, value in parse_qsl(parts.query)
        if key.lower() in REDIRECT_FIELDS
    )


def links(group: JobGroup, source_names: dict[str, str],
          reported: set[str] | None = None) -> tuple[dict, list[dict]]:
    reported = reported_urls() if reported is None else reported
    known_blocked = any(blocked(url) or url in reported
                        for c in group.copies for url in (c.url, c.employer_url))

    def allowed(url):
        return url and url not in reported and not blocked(url) and not (
            known_blocked and opaque(url))

    copies = sorted(group.copies, key=lambda c: (
        SOURCE_KIND_RANK.get(group.source_kinds.get(c.source, "aggregator"), 3),
        not c.description_is_complete,
    ))
    employer = next((c for c in copies if allowed(c.employer_url)
                     and not is_agency(c.company)), None)
    other = [{"source": source_names.get(c.source, c.source), "url": c.url}
             for c in copies if allowed(c.url)]
    main = ({"source": "Employer's site", "url": employer.employer_url}
            if employer else other.pop(0) if other else {"source": "", "url": ""})
    seen = {main["source"]} if not employer else set()
    also = []
    for link in other:
        if link["source"] not in seen and link["url"] != main["url"]:
            seen.add(link["source"])
            also.append(link)
    return main, also


def exclusion_key(group: JobGroup, reported: set[str] | None = None) -> str | None:
    reported = reported_urls() if reported is None else reported
    known = any(blocked(c.url) or blocked(c.employer_url) for c in group.copies)
    marked = any(c.url in reported or c.employer_url in reported for c in group.copies)
    if (known or marked) and not links(group, {}, reported)[0]["url"]:
        return "application_route" if known else "reported_application_route"
    return None


def unavailable(group: JobGroup, reported: set[str] | None = None) -> bool:
    return exclusion_key(group, reported) is not None


def clean_card(card: dict, reported: set[str] | None = None) -> dict:
    """Preserve saved history while removing blocked links from a response copy."""
    if "main_link" not in card:
        return card
    reported = reported_urls() if reported is None else reported
    main = card.get("main_link") or {"source": "", "url": ""}
    all_links = [main, *card.get("also_on", [])]
    marked = any(link.get("url") in reported for link in all_links)
    known_blocked = marked or any(blocked(link.get("url")) for link in all_links)
    other = [link for link in card.get("also_on", []) if link.get("url")
             and link["url"] not in reported and not blocked(link["url"])
             and not (known_blocked and opaque(link["url"]))]
    if main.get("url") in reported or blocked(main.get("url")) or (
            known_blocked and opaque(main.get("url"))):
        main = other.pop(0) if other else {"source": "", "url": ""}
    return {**card, "main_link": main, "also_on": other,
            "application_link_unavailable": not main["url"] and (
                known_blocked or card.get("application_link_unavailable", False)),
            "application_destination_unverified": opaque(main["url"]),
            "application_link_reported": marked}


def filter_snapshot(snapshot: dict) -> None:
    jobs = (snapshot.get("result") or {}).get("jobs")
    if not jobs:
        return
    reported = reported_urls()
    removed = Counter()
    for section in ("cards", "date_unknown"):
        if section not in jobs:
            continue
        kept = []
        for card in jobs.get(section, []):
            cleaned = clean_card(card, reported)
            if cleaned.get("application_link_unavailable"):
                reason = REPORTED_EXCLUSION_REASON if cleaned["application_link_reported"] else (
                    EXCLUSION_REASON)
                removed[reason] += 1
            else:
                kept.append(cleaned)
        jobs[section] = kept
    for section in ("hidden", "ruled_out_by_conditions"):
        if section in jobs:
            jobs[section] = [clean_card(card, reported) for card in jobs[section]]
    if removed:
        counts = jobs.setdefault("counts", {})
        counts["shown"] = len(jobs["cards"]) + len(jobs["date_unknown"])
        counts["left_out"] = [*counts.get("left_out", []),
                              *({"reason": reason, "count": count}
                                for reason, count in removed.items())]
        jobs["new_count"] = sum(c.get("is_new", False)
                                for c in jobs["cards"] + jobs["date_unknown"])
        snapshot.setdefault("notes", []).append(
            "Unavailable application links were removed. Jobs without another saved link "
            "are left out; the original saved search is preserved."
        )
