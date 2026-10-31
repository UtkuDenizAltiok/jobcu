"""Application links: exclude known unusable destinations without fetching private URLs. Finding
the page behind a link happens only when the person clicks it (applylink.py)."""

import json
import re
from collections import Counter
from urllib.parse import parse_qsl, urlsplit

from jobcu import db
from jobcu.dedupe import SOURCE_KIND_RANK, JobGroup, is_agency

BLOCKED_HOSTS = frozenset({"cv-library.co.uk"})
REDIRECT_FIELDS = frozenset({"url", "redirect", "redirect_url", "target", "destination", "to"})
REPEATS_ADS = frozenset({"adzuna", "arbeitsagentur", "jobleads", "jooble", "learn4good", "talent",
                         "trabajo"})
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


def saved_link(conn, job_id: int, url: str) -> dict:
    """The job's saved link with this address: only those can be opened or reported."""
    try:
        parsed = urlsplit(url)
        valid = parsed.scheme in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Choose an available job link.")
    row = conn.execute("SELECT card_json FROM job_cards WHERE job_id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(job_id)
    card = json.loads(row[0])
    links = [card.get("main_link") or {}, *card.get("also_on", [])]
    link = next((link for link in links if link.get("url") == url), None)
    if not url or link is None:
        raise ValueError("That link is no longer saved for this job. Refresh the job list.")
    return link


def link_to_open(job_id: int, url: str) -> dict:
    with db.connect() as conn:
        return saved_link(conn, job_id, url)


def report_link(job_id: int, url: str) -> None:
    """Accept only an existing saved link; never fetch it or infer its final host."""
    with db.connect() as conn:
        link = saved_link(conn, job_id, url)
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


def _advertisement_identity(url: str | None) -> tuple[str, str] | None:
    """Recognized opaque ad identity only; never follow a redirect or rewrite its URL."""
    if not opaque(url):
        return None
    try:
        parts = urlsplit(url)
        if (parts.scheme not in {"http", "https"} or parts.username is not None
                or parts.port not in {None, 443 if parts.scheme == "https" else 80}):
            return None
        match = re.fullmatch(r"/(?:jobs/)?(?:details|land/ad)/(\d+)/?", parts.path)
        # Unknown query fields may change the destination/request identity.
        if not match or any(key.casefold() not in {"se", "v"} and not
                            key.casefold().startswith("utm_")
                            for key, _ in parse_qsl(parts.query, keep_blank_values=True)):
            return None
        return ((parts.hostname or "").lower().rstrip(".").removeprefix("www."),
                match.group(1))
    except ValueError:
        return None


def _reported(url: str | None, reports: set[str]) -> bool:
    if url in reports:
        return True
    identity = _advertisement_identity(url)
    return identity is not None and any(
        _advertisement_identity(earlier) == identity for earlier in reports)


def _repeats_an_ad(url: str | None) -> bool:
    """A site that shows other sites' ads: another saved link comes first, nearer the original."""
    try:
        host = (urlsplit(url or "").hostname or "").lower().rstrip(".")
    except ValueError:
        return False
    return bool(set(host.split(".")) & REPEATS_ADS)


def _copy_urls(copy):
    return (copy.url, copy.employer_url, *(o.get("url") for o in copy.application_options))


def links(group: JobGroup, source_names: dict[str, str],
          reported: set[str] | None = None) -> tuple[dict, list[dict]]:
    reported = reported_urls() if reported is None else reported
    known_blocked = any(blocked(url) or _reported(url, reported)
                        for c in group.copies for url in _copy_urls(c))

    def allowed(url):
        return url and not _reported(url, reported) and not blocked(url) and not (
            known_blocked and opaque(url))

    copies = sorted(group.copies, key=lambda c: (
        SOURCE_KIND_RANK.get(group.source_kinds.get(c.source, "aggregator"), 3),
        not c.description_is_complete,
    ))
    employer = next((c for c in copies if allowed(c.employer_url)
                     and not is_agency(c.company)), None)
    other = [{"source": source_names.get(c.source, c.source), "url": c.url}
             for c in copies if allowed(c.url)]
    other += [option for c in copies for option in c.application_options
              if allowed(option.get("url"))]
    other.sort(key=lambda link: _repeats_an_ad(link["url"]))
    main = ({"source": "Employer's site", "url": employer.employer_url}
            if employer else other.pop(0) if other else {"source": "", "url": ""})
    seen = {main["source"]} if not employer else set()
    urls = {main["url"]}
    also = []
    for link in other:
        if link["source"] not in seen and link["url"] not in urls:
            seen.add(link["source"])
            urls.add(link["url"])
            also.append(link)
    return main, also


def exclusion_key(group: JobGroup, reported: set[str] | None = None) -> str | None:
    reported = reported_urls() if reported is None else reported
    known = any(blocked(url) for c in group.copies for url in _copy_urls(c))
    marked = any(_reported(url, reported) for c in group.copies for url in _copy_urls(c))
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
    marked = any(_reported(link.get("url"), reported) for link in all_links)
    known_blocked = marked or any(blocked(link.get("url")) for link in all_links)
    other = [link for link in card.get("also_on", []) if link.get("url")
             and not _reported(link["url"], reported) and not blocked(link["url"])
             and not (known_blocked and opaque(link["url"]))]
    if _reported(main.get("url"), reported) or blocked(main.get("url")) or (
            known_blocked and opaque(main.get("url"))):
        main = other.pop(0) if other else {"source": "", "url": ""}
    elif opaque(main.get("url")):
        # Only an independently saved employer link can replace this opaque route.
        # Never resolve, unwrap or discard the advertiser URL required by Adzuna. A click still
        # goes through Adzuna's own apply link, in the person's browser (applylink.py).
        employer = next((i for i, link in enumerate(other)
                         if link.get("source") == "Employer's site"
                         and not opaque(link["url"])), None)
        if employer is not None:
            main, original = other.pop(employer), main
            other.insert(0, original)
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
    for section in ("cards", "date_unknown", "location_unchecked"):
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
        shown = jobs["cards"] + jobs["date_unknown"] + jobs.get("location_unchecked", [])
        counts["shown"] = len(shown)
        if "location_unchecked" in jobs:
            counts["location_unchecked"] = len(jobs["location_unchecked"])
        counts["left_out"] = [*counts.get("left_out", []),
                              *({"reason": reason, "count": count}
                                for reason, count in removed.items())]
        jobs["new_count"] = sum(c.get("is_new", False) for c in shown)
        snapshot.setdefault("notes", []).append(
            "Unavailable application links were removed. Jobs without another saved link "
            "are left out; the original saved search is preserved."
        )
