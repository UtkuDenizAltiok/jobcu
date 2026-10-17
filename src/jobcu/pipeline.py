"""The job-finding part of a search: collecting from sources, duplicates, filters, full ads,
scoring and the result cards. search.py runs these steps and reports progress."""

import dataclasses
import json
import logging
import math
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timedelta

from jobcu import applications, jobstore, travel
from jobcu import places as place_list
from jobcu.countries import COUNTRIES
from jobcu.dedupe import SOURCE_KIND_RANK, JobGroup, group_duplicates
from jobcu.filters import REASONS, condition_fit
from jobcu.freshness import earliest_possible, freshness, parse_iso, window_start
from jobcu.jobstore import JobState
from jobcu.location import LocationPlan
from jobcu.placenames import countries_in
from jobcu.scoring import LEGACY_ONLINE_NOTE, ONLINE_NOTE, PARTS, ROLE_REVIEW_NOTE
from jobcu.sources import all_sources
from jobcu.sources.base import (
    FoundJob,
    JobQuery,
    JobSource,
    SourceContext,
    SourceError,
    SourceReport,
)
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.http import Blocked, PoliteClient, RequestStopped
from jobcu.text import normalise

log = logging.getLogger(__name__)


class Collected:
    def __init__(self, jobs, reports, sources):
        self.jobs: list[FoundJob] = jobs
        self.reports: list[SourceReport] = reports
        self.sources: dict[str, JobSource] = sources

    @property
    def ads_found(self) -> int:
        """The ads found fresh: older copies only help to date the others."""
        return sum(1 for job in self.jobs if not job.older_copy)


def collect(query: JobQuery, http: PoliteClient, keys, disabled: list[str], run) -> Collected:
    """Ask every source at the same time. A failing source never stops the others."""
    sources = all_sources()
    reports: list[SourceReport] = []
    active: list[tuple[JobSource, SourceReport]] = []
    for source in sources:
        report = SourceReport(source.id, source.name)
        reports.append(report)
        if source.id in disabled:
            report.status, report.message = "skipped", "Switched off in Settings."
        elif not source.covers(query):
            report.status, report.message = "skipped", "Doesn't cover the countries searched."
        elif reason := source.unavailable_reason(keys):
            report.status, report.message = "unavailable", reason
        else:
            active.append((source, report))

    found: dict[str, list[FoundJob]] = {}

    def progress() -> None:
        run.update("sources", "running", " · ".join(f"{r.name}: {r.jobs_found}" for _, r in active))

    def run_one(source: JobSource, report: SourceReport) -> None:
        ctx = SourceContext(http, keys, report, lambda: run.stop_requested, run.note)
        jobs: list[FoundJob] = []
        try:
            for job in source.search(query, ctx):
                jobs.append(job)
                if not job.older_copy:
                    report.jobs_found += 1
                    if report.jobs_found % 10 == 0:
                        progress()
        except RequestStopped:
            report.status = "partial" if jobs else "skipped"
            report.message = "Stopped before more requests were sent."
        except Blocked:
            report.status = "unavailable"
            report.message = "Refused Jobcu's requests right now, so it was skipped."
        except SourceError as exc:
            report.status, report.message = "failed", str(exc)
        except Exception:
            log.exception("Source %s failed", source.id)
            report.status, report.message = "failed", "Had an unexpected problem."
        report.jobs_found = sum(1 for job in jobs if not job.older_copy)
        found[source.id] = jobs
        progress()

    if active:
        with ThreadPoolExecutor(max_workers=len(active), thread_name_prefix="source") as pool:
            list(pool.map(lambda pair: run_one(*pair), active))
    jobs = [job for source, _ in active for job in found.get(source.id, [])]
    return Collected(jobs, reports, {s.id: s for s in sources})


def collected_again(reports: list[dict]) -> Collected:
    """An earlier search's sources, to read more full ads after that search has ended."""
    sources = all_sources()
    return Collected([], [SourceReport(**report) for report in reports],
                     {source.id: source for source in sources})


def make_groups(collected: Collected) -> list[JobGroup]:
    """The different jobs. A career site's older copy stays in a group only to give it its
    earliest date when another source found the job fresh; a group of older copies alone is no
    job of this search. Different employer requisitions stay separate; an older copy with the
    exact same source ID still establishes the original date."""
    kinds = {source_id: source.kind for source_id, source in collected.sources.items()}
    groups = group_duplicates(collected.jobs, kinds)
    kept: list[JobGroup] = []
    position: dict[int, int] = {}
    for index, group in enumerate(groups):
        fresh_sources = {copy.source for copy in group.copies if not copy.older_copy}
        if not fresh_sources:
            continue
        fresh_ids = {(copy.source, copy.source_job_id) for copy in group.copies
                     if not copy.older_copy and copy.source_job_id}
        copies = [copy for copy in group.copies
                  if not copy.older_copy or copy.source not in fresh_sources
                  or (copy.source_job_id and (copy.source, copy.source_job_id) in fresh_ids)]
        position[index] = len(kept)
        kept.append(group if len(copies) == len(group.copies)
                    else dataclasses.replace(group, copies=copies))
    return [dataclasses.replace(group, possible_duplicate_of=position.get(
        group.possible_duplicate_of)) for group in kept]


def _complete_ad(job: FoundJob) -> bool:
    return bool(job.description_is_complete and (job.description or "").strip())


def load_full_ads(groups, indexes, collected: Collected, http, keys, run) -> None:
    """Reuse full text across matched copies, then try available readers until one succeeds.

    Scores are never reused. Each source stays serial, independent sources run together,
    and failed/empty/incomplete responses leave the job available with its existing evidence.
    """
    reports = {r.source: r for r in collected.reports}
    pending: dict[int, list[int]] = {}
    remembered = 0

    def date_reader(copy):
        return ((copy.posted_at is None or copy.closes_at is None)
                and getattr(collected.sources.get(copy.source), "details_supply_dates", False))

    for index in dict.fromkeys(indexes):
        if run.stop_requested:
            return
        group = groups[index]
        # A completeness flag without text is not usable evidence.
        group.copies = [dataclasses.replace(c, description_is_complete=False)
                        if c.description_is_complete and not _complete_ad(c) else c
                        for c in group.copies]
        if (_complete_ad(group.best_description_copy)
                and not any(date_reader(copy) for copy in group.copies)):
            continue
        order = sorted(range(len(group.copies)), key=lambda i: SOURCE_KIND_RANK.get(
            group.source_kinds.get(group.copies[i].source,
                                   getattr(collected.sources.get(group.copies[i].source),
                                           "kind", "aggregator")), 3))
        metadata_checked = set()
        for copy_index in order:
            if (_complete_ad(group.best_description_copy)
                    and not date_reader(group.copies[copy_index])):
                continue
            try:
                copy = group.copies[copy_index]
                reader = collected.sources.get(copy.source)
                known = jobstore.remembered_ad(
                    copy, reader_version=getattr(reader, "detail_cache_version", 1)
                )
            except Exception:
                log.exception("Reading remembered full-ad evidence failed")
                continue
            if known is not None and _complete_ad(known):
                if date_reader(copy):
                    metadata_checked.add(copy_index)
                if _complete_ad(copy):
                    # Fresh list text outranks cached text from the same requisition.
                    known = dataclasses.replace(
                        copy, posted_at=copy.posted_at or known.posted_at,
                        date_precision=(copy.date_precision if copy.posted_at
                                        else known.date_precision),
                        closes_at=copy.closes_at or known.closes_at,
                    )
                group.copies[copy_index] = known
                remembered += 1
        if (_complete_ad(group.best_description_copy) and not any(
                date_reader(copy) and i not in metadata_checked
                for i, copy in enumerate(group.copies))):
            continue
        options, seen = [], set()
        for copy_index in order:
            copy = group.copies[copy_index]
            identity = (copy.source, copy.source_job_id,
                        None if copy.source_job_id else copy.url)
            source, report = collected.sources.get(copy.source), reports.get(copy.source)
            if (_complete_ad(group.best_description_copy)
                    and (not date_reader(copy) or copy_index in metadata_checked)):
                continue
            if (identity in seen or source is None or report is None
                    or type(source).load_details is JobSource.load_details
                    or report.status in {"skipped", "unavailable"}
                    or source.unavailable_reason(keys)):
                continue
            seen.add(identity)
            options.append(copy_index)
        if options:
            pending[index] = options
    total = len(pending)
    known_note = f", {remembered} already known" if remembered else ""
    if not total:
        run.update("details", "done", f"Nothing more to read{known_note}")
        return
    lock = threading.Lock()
    stopped = threading.Event()
    exhausted: set[str] = set()
    done, tried = [0], [0]
    completed = set()

    def run_source(source_id: str, items: list[tuple[int, int]]) -> None:
        source = collected.sources[source_id]
        ctx = SourceContext(http, keys, reports[source_id],
                            lambda: run.stop_requested or stopped.is_set(), run.note)
        for index, copy_index in items:
            if ctx.should_stop():
                return
            copy = groups[index].copies[copy_index]
            if source_id not in exhausted:
                try:
                    # Adapters may mutate their argument. Failed or mismatched responses
                    # must not mutate the retained copy or change its remembered identity.
                    requested = dataclasses.replace(copy, job_types=list(copy.job_types))
                    full = source.load_details(requested, ctx)
                    if ((full.source, full.source_job_id) != (copy.source, copy.source_job_id)
                            or (not copy.source_job_id and full.url != copy.url)):
                        raise SourceError("The full-ad response did not match the requested copy.")
                    if (not (full.description or "").strip()
                            or (not full.description_is_complete
                                and len(full.description) < len(copy.description))):
                        full = dataclasses.replace(full, description=copy.description,
                                                   description_is_complete=False)
                    groups[index].copies[copy_index] = full
                    try:
                        if not (date_reader(copy) and full is requested):
                            # A reader returning its unchanged argument after failure does not
                            # establish a successful metadata check, even with complete list text.
                            jobstore.remember_ad(full, reader_version=source.detail_cache_version)
                    except Exception:
                        log.exception("Keeping full-ad evidence for later searches failed")
                except RequestStopped:
                    stopped.set()
                    return
                except BudgetExhausted as exc:
                    exhausted.add(source_id)
                    reports[source_id].status, reports[source_id].message = "partial", exc.message
                except (Blocked, SourceError):
                    log.info("Full-ad reader %s could not supply this copy", source_id)
                except Exception:
                    log.exception("Reading a full ad from %s failed", source_id)
            complete = _complete_ad(groups[index].best_description_copy)
            with lock:
                tried[0] += 1
                if not pending[index] or (complete and not any(
                        date_reader(groups[index].copies[n]) for n in pending[index])):
                    completed.add(index)
                    done[0] = len(completed)
                if tried[0] % 5 == 0 or done[0] == total:
                    run.update("details", "running", f"{done[0]} of {total} jobs checked for full "
                               f"ads, {tried[0]} copies checked{known_note}")

    while pending and not run.stop_requested and not stopped.is_set():
        work: dict[str, list[tuple[int, int]]] = {}
        for index, options in pending.items():
            copy_index = options.pop(0)
            work.setdefault(groups[index].copies[copy_index].source, []).append((index, copy_index))
        with ThreadPoolExecutor(max_workers=len(work), thread_name_prefix="details") as pool:
            list(pool.map(lambda pair: run_source(*pair), work.items()))
        pending = {i: options for i, options in pending.items() if options and (
            not _complete_ad(groups[i].best_description_copy)
            or any(date_reader(groups[i].copies[n]) for n in options))}


def newest_first(groups: list[JobGroup], indexes: list[int]) -> list[int]:
    def key(index: int):
        posted = groups[index].posted_at
        return (posted is None, -(posted.timestamp() if posted else 0))

    return sorted(indexes, key=key)


def readable_place(job: FoundJob) -> str | None:
    """The job's place as its job site wrote it, with the town added when that's only a
    postcode ("CB22 4QR" → "CB22 4QR, near Whittlesford")."""
    text = job.location_text
    town = place_list.postcode_town(text, job.country) if text else None
    if town is None or normalise(town.name) in normalise(text):
        return text
    return f"{text}, near {town.name}"


def unchecked_location_conditions(group: JobGroup, plan: LocationPlan) -> list[str]:
    """Hard location conditions must pass before scoring; unknown is not a pass.

    An unread condition is still a request the person made. Turning a condition off is
    explicit; failure to interpret or research it cannot silently remove the scoring gate.
    """
    return [*plan.not_checked_yet, *(c.understood_as for c in plan.conditions
            if not c.switched_off and c.kind != "about_job"
            and (c.status == "not_checked" or condition_fit(c, group) != "yes"))]


def location_gate_view(snapshot: dict) -> None:
    """Apply today's admission rule to a response copy, without rewriting saved history.

    Older searches paid for scores despite explicitly unchecked hard location conditions.
    Those assessments must not appear as qualifying matches under the new admission rule.
    The recorded checks, not a guessed journey or a fresh provider request, decide this view.
    """
    result = snapshot.get("result") or {}
    jobs, plan = result.get("jobs"), result.get("location") or {}
    if not jobs:
        return
    hard = [c for c in plan.get("conditions", [])
            if not c.get("switched_off") and c.get("kind") != "about_job"]
    unread = bool(plan.get("not_checked_yet")) or any(
        c.get("status") == "not_checked" for c in hard)
    if not hard and not unread:
        return
    pending = list(jobs.get("location_unchecked", []))
    for section in ("cards", "date_unknown"):
        kept = []
        for card in jobs.get(section, []):
            unknown = unread or any(c.get("status") == "unclear"
                                    for c in card.get("location_checks", []))
            if unknown:
                pending.append({**card, "location_pending": True, "score": None, "parts": None,
                                "limits": [], "deductions": [], "reasons": []})
            else:
                kept.append(card)
        jobs[section] = kept
    jobs["location_unchecked"] = pending
    jobs.setdefault("counts", {})["location_unchecked"] = len(pending)


def history_view(snapshot: dict) -> None:
    """Reflect confirmed copy links and repost age without rewriting saved assessments."""
    jobs = (snapshot.get("result") or {}).get("jobs")
    if not jobs:
        return
    sections = [s for s in ("cards", "date_unknown", "location_unchecked") if s in jobs]
    cards = [card for section in sections for card in jobs[section]]
    if not cards:
        return
    canonical = jobstore.canonical_ids([c["job_id"] for c in cards])
    seen = jobstore.first_seen(list(canonical.values()))
    started = parse_iso(snapshot.get("started_at"))
    hours = (snapshot.get("form") or {}).get("posted_within_hours")
    start = window_start(started, hours) if started and hours else None
    groups = {}
    for section in sections:
        for card in jobs[section]:
            groups.setdefault(canonical[card["job_id"]], []).append((section, card))
    if (len(groups) == len(cards) and all(canonical[c["job_id"]] == c["job_id"] for c in cards)
            and not any(start and seen.get(root) and seen[root] < start for root in groups)
            and not any(c.get("is_new") and started and seen.get(c["job_id"])
                        and seen[c["job_id"]] < started for c in cards)):
        return
    for section in sections:
        jobs[section] = []
    reposts, combined = 0, 0
    for root, entries in groups.items():
        first = seen.get(root)
        combined += len(entries) - 1
        if start and first and first < start:
            reposts += 1
            continue
        section, original = min(entries, key=lambda pair: (
            applications.opaque((pair[1].get("main_link") or {}).get("url")),
            pair[1].get("summary_only", True), pair[1]["job_id"] != root))
        card = {**original, "job_id": root}
        if started and first and first < started:
            card["is_new"] = False
        if len(entries) > 1:
            links = []
            main = card.get("main_link") or {}
            urls = {main.get("url")}
            for _, copy in entries:
                for link in [copy.get("main_link") or {}, *copy.get("also_on", [])]:
                    if link.get("url") and link["url"] not in urls:
                        urls.add(link["url"])
                        links.append(link)
            card["also_on"] = links
            assessments = {json.dumps([c.get("score"), c.get("parts"), c.get("limits")],
                                      sort_keys=True) for _, c in entries}
            if len(assessments) > 1:
                note = ("These copies were assessed separately. A new assessment is needed "
                        "for one consistent match score.")
                card.update(score=None, parts=None, limits=[], deductions=[], reasons=[],
                            score_notes=[*card.get("score_notes", []), note],
                            score_checks=[*card.get("score_checks", []),
                                          {"text": note, "status": "unclear"}])
        jobs[section].append(card)
    counts = jobs.setdefault("counts", {})
    visible = [c for section in sections for c in jobs[section]]
    counts["shown"] = len(visible)
    if "location_unchecked" in jobs:
        counts["location_unchecked"] = len(jobs["location_unchecked"])
    jobs["new_count"] = sum(bool(c.get("is_new")) for c in visible)
    if reposts:
        left_out = Counter()
        for item in counts.get("left_out", []):
            left_out[item["reason"]] += item["count"]
        left_out[REASONS["repost"]] += reposts
        counts["left_out"] = [{"reason": reason, "count": count}
                              for reason, count in left_out.items()]
    if combined:
        counts["historical_copies_combined"] = (
            counts.get("historical_copies_combined", 0) + combined)


def build_card(
    group: JobGroup,
    *,
    job_id: int,
    is_new: bool,
    state: JobState | None,
    scored: dict | None,
    plan: LocationPlan,
    source_names: dict[str, str],
    possible_duplicate_of: int | None,
    started_at,
    posted_within_hours: int,
    ruled_out: bool = False,
    first_seen_at: datetime | None = None,
    reported_links: set[str] | None = None,
    location_pending: bool = False,
) -> dict:
    main = group.main
    best = group.best_description_copy
    stated_types = sorted({t for c in group.copies for t in c.job_types})
    job_types = job_types_of(group, scored)
    work_mode = next((c.work_mode for c in group.copies if c.work_mode), None) or (
        scored or {}
    ).get("work_mode")
    reported_links = applications.reported_urls() if reported_links is None else reported_links
    main_link, also_on = applications.links(group, source_names, reported_links)
    country = main.country or next((c.country for c in group.copies if c.country), None)
    checks = []
    if ruled_out:
        pass  # the country is fine for these: a condition about places left them out
    elif country and country in plan.countries:
        checks.append({
            "label": f"In {COUNTRIES[country].name}" if country in COUNTRIES else country,
            "status": "verified",
            "source": source_names.get(main.source, main.source),
        })
    elif not country:
        checks.append({"label": "Location unclear", "status": "unclear", "source": None})
    # What the conditions the person wrote say about this job. When its town
    # isn't known, one line says so instead of one "couldn't be checked" per condition.
    town_known = travel.job_point(group) is not None
    unanswered = 0
    for condition in plan.conditions:
        if not condition.filters:
            if location_pending and not condition.switched_off and condition.kind != "about_job":
                checks.append({"label": condition.understood_as, "status": "unclear",
                               "source": None, "note": condition.note})
            continue
        answer = condition_fit(condition, group)
        # A job left out by a condition only shows what left it out.
        if ruled_out and answer != "no":
            continue
        if answer == "unknown" and not town_known:
            unanswered += 1
            continue
        found = travel.detail(condition, group)
        measured_by = found[1] if found else None
        status = {"yes": "verified", "unknown": "unclear"}.get(answer, "fails")
        reference = condition.reference_status if condition.kind == "near" else "applied"
        if answer == "yes":
            if reference == "not_checked":
                status = "unclear"
            elif reference == "estimate" or measured_by == "AI estimate" or (
                condition.kind != "near" and condition.status == "estimate"
            ):
                status = "estimate"
        checks.append({
            "label": condition.understood_as,
            "status": status,
            "source": _checked_by(condition, measured_by),
            "detail": found[0] if found else None,
            "note": (condition.note or (
                "Reference-place facts couldn't be checked." if reference == "not_checked"
                else "Reference-place facts are uncertain; please check."
            )) if reference != "applied" else "",
        })
    if unanswered and not ruled_out:
        where = next((c.location_text for c in group.copies
                      if c.location_text and not countries_in(c.location_text)), None)
        conditions = "your condition about places" if unanswered == 1 else (
            "your conditions about places")
        checks.append({
            "label": ("The source and ad name different workplaces; location eligibility "
                      "needs confirmation" if travel.workplace_conflict(group) else
                      f"Jobcu doesn't know where \"{where}\" is, so {conditions} couldn't be "
                      "checked" if where else
                      f"{source_names.get(main.source, main.source)} doesn't say which town "
                      f"this job is in, nor does its text, so {conditions} couldn't be checked"),
            "status": "unclear", "source": None, "detail": None, "whole_sentence": True,
        })
    if location_pending:
        checks.extend({"label": text, "status": "unclear", "source": None}
                      for text in plan.not_checked_yet)
    start = window_start(started_at, posted_within_hours)
    state = state or JobState()
    # An old ad posted again looks fresh; Jobcu's memory knows when it first showed this job.
    earliest = earliest_possible(group.posted_at, group.date_precision)
    reposted = bool(first_seen_at and earliest and first_seen_at < earliest - timedelta(days=1))
    if location_pending:
        scored = None  # retained legacy assessments are not current qualifying matches
    return {
        "job_id": job_id,
        "is_new": is_new,
        "state": asdict(state),
        "title": main.title,
        "company": main.company,
        # A town Jobcu found when the job sites gave only a country: in the ad's text
        # (relevance.py) or online (jobplace.py).
        "location": ", ".join(travel.found_places(group)) or readable_place(main),
        "location_from_ad_text": bool(group.place_from_text),
        "location_found_online": bool(group.place_from_web),
        "country": country,
        "work_mode": work_mode,
        "job_types": job_types,
        "job_types_from_ad_text": job_types != stated_types and bool(job_types),
        "posted_at": group.posted_at.isoformat() if group.posted_at else None,
        "date_precision": group.date_precision,
        "date_known": freshness(group.posted_at, group.date_precision, start) != "unknown",
        "first_seen_at": first_seen_at.isoformat() if reposted else None,
        "closes_at": group.closes_at.isoformat() if group.closes_at else None,
        "score": scored["score"] if scored else None,
        "location_pending": location_pending,
        "parts": scored["parts"] if scored else None,
        # Blockers that hold the score below what its parts add up to (scoring.py).
        "limits": (scored or {}).get("limits", []),
        "deductions": (scored or {}).get("deductions", []),
        "score_notes": (scored or {}).get("notes", []),
        "score_checks": [{"text": ONLINE_NOTE if note == LEGACY_ONLINE_NOTE else note,
                          "status": "info" if note in {ONLINE_NOTE, LEGACY_ONLINE_NOTE}
                          or note.startswith(ROLE_REVIEW_NOTE)
                          else "unclear"}
                         for note in (scored or {}).get("notes", [])],
        "reasons": scored["reasons"] if scored else [],
        "required_languages": scored["required_languages"] if scored else [],
        "main_link": main_link,
        "also_on": also_on,
        "application_link_unavailable": applications.unavailable(group, reported_links),
        "application_destination_unverified": applications.opaque(main_link["url"]),
        "possible_duplicate_of": possible_duplicate_of,
        "summary_only": not best.description_is_complete,
        "salary": best.salary_text or main.salary_text,
        "location_checks": checks,
    }


def job_types_of(group: JobGroup, scored: dict | None) -> list[str]:
    """The job's types: what its job sites say, unless they leave it open between several
    ("contract" on Adzuna can be fixed-term, freelance or part-time) and the ad text says which
    one it is. When no site says, the ad text decides alone."""
    stated = sorted({t for c in group.copies for t in c.job_types})
    read = (scored or {}).get("job_type")
    # These two hints describe a full-time schedule with an unspecified contract.
    # Student work can also be full-time; the ad may refine this broad schedule.
    student = (read == "internship_or_working_student"
               and set(stated) == {"full_time_permanent", "fixed_term"})
    if read and read != "unclear" and (
            not stated or (len(stated) > 1 and (read in stated or student))):
        return [read]
    return stated


def _checked_by(condition, measured_by: str | None = None) -> str:
    if measured_by == "Not checked":
        return measured_by
    if measured_by == "AI estimate":
        return "AI estimate"
    if measured_by == "Google Maps":
        return "Google Maps"
    if condition.changed_by_you:
        return "Changed by you"
    if condition.status == "estimate" and measured_by is None:
        return "AI estimate"
    if condition.kind in ("town_size", "near"):
        return "Worked out by Jobcu"
    return "Checked on the web"


def sort_cards(cards: list[dict]) -> list[dict]:
    """Highest score, then strongest weakest fit area, then newer evidence."""
    return sorted(
        cards,
        key=lambda c: (
            c["score"] is None,
            -(c["score"] or 0),
            -_weakest_fit(c),
            -(_timestamp(c["posted_at"])),
        ),
    )


def _weakest_fit(card: dict) -> float:
    parts = card.get("parts") or {}
    if not all(type(parts.get(name)) in {int, float} and math.isfinite(parts[name])
               for name in PARTS):
        return 0  # incomplete legacy breakdown: keep the existing date tie-break
    return min(parts[name] / maximum for name, maximum in PARTS.items())


def _timestamp(iso: str | None) -> float:
    from jobcu.freshness import parse_iso

    parsed = parse_iso(iso)
    return parsed.timestamp() if parsed else 0.0


def unique_counts(groups: list[JobGroup], shown: list[int]) -> Counter:
    """Jobs found only by one source, per source."""
    counts: Counter = Counter()
    for index in shown:
        sources = {copy.source for copy in groups[index].copies}
        if len(sources) == 1:
            counts[next(iter(sources))] += 1
    return counts
