"""Application links: exclude known unusable destinations without fetching private URLs."""

from urllib.parse import parse_qsl, urlsplit

from jobcu.dedupe import SOURCE_KIND_RANK, JobGroup, is_agency

BLOCKED_HOSTS = frozenset({"cv-library.co.uk"})
REDIRECT_FIELDS = frozenset({"url", "redirect", "redirect_url", "target", "destination", "to"})
EXCLUSION_REASON = "CV-Library application route, with no other saved link"


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


def links(group: JobGroup, source_names: dict[str, str]) -> tuple[dict, list[dict]]:
    known_blocked = any(blocked(c.url) or blocked(c.employer_url) for c in group.copies)

    def allowed(url):
        return url and not blocked(url) and not (known_blocked and opaque(url))

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


def unavailable(group: JobGroup) -> bool:
    return any(blocked(c.url) or blocked(c.employer_url) for c in group.copies) and not (
        links(group, {})[0]["url"]
    )


def clean_card(card: dict) -> dict:
    """Preserve saved history while removing blocked links from a response copy."""
    if "main_link" not in card:
        return card
    main = card.get("main_link") or {"source": "", "url": ""}
    known_blocked = blocked(main.get("url")) or any(
        blocked(link.get("url")) for link in card.get("also_on", []))
    other = [link for link in card.get("also_on", []) if link.get("url")
             and not blocked(link["url"]) and not (known_blocked and opaque(link["url"]))]
    if blocked(main.get("url")) or (known_blocked and opaque(main.get("url"))):
        main = other.pop(0) if other else {"source": "", "url": ""}
    return {**card, "main_link": main, "also_on": other,
            "application_link_unavailable": not main["url"] and (
                known_blocked or card.get("application_link_unavailable", False)),
            "application_destination_unverified": opaque(main["url"])}


def filter_snapshot(snapshot: dict) -> None:
    jobs = (snapshot.get("result") or {}).get("jobs")
    if not jobs:
        return
    removed = []
    for section in ("cards", "date_unknown"):
        if section not in jobs:
            continue
        kept = []
        for card in jobs.get(section, []):
            cleaned = clean_card(card)
            if cleaned.get("application_link_unavailable"):
                removed.append(card)
            else:
                kept.append(cleaned)
        jobs[section] = kept
    for section in ("hidden", "ruled_out_by_conditions"):
        if section in jobs:
            jobs[section] = [clean_card(card) for card in jobs[section]]
    if removed:
        counts = jobs.setdefault("counts", {})
        counts["shown"] = len(jobs["cards"]) + len(jobs["date_unknown"])
        counts["left_out"] = [*counts.get("left_out", []),
                              {"reason": EXCLUSION_REASON, "count": len(removed)}]
        jobs["new_count"] = sum(c.get("is_new", False)
                                for c in jobs["cards"] + jobs["date_unknown"])
        snapshot.setdefault("notes", []).append(
            "CV-Library links were removed. Jobs without another saved application link "
            "are left out; the original saved search is preserved."
        )
