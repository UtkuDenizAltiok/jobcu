"""The job-finding part of a search: collecting from sources, duplicates, filters, full ads,
scoring and the result cards. search.py runs these steps and reports progress."""

import dataclasses
import logging
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timedelta

from jobcu import applications, jobstore, travel
from jobcu import places as place_list
from jobcu.countries import COUNTRIES
from jobcu.dedupe import SOURCE_KIND_RANK, JobGroup, group_duplicates
from jobcu.filters import condition_fit
from jobcu.freshness import earliest_possible, freshness, window_start
from jobcu.jobstore import JobState
from jobcu.location import LocationPlan
from jobcu.placenames import countries_in
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
    for index in dict.fromkeys(indexes):
        if run.stop_requested:
            return
        group = groups[index]
        # A completeness flag without text is not usable evidence.
        group.copies = [dataclasses.replace(c, description_is_complete=False)
                        if c.description_is_complete and not _complete_ad(c) else c
                        for c in group.copies]
        if _complete_ad(group.best_description_copy):
            continue
        order = sorted(range(len(group.copies)), key=lambda i: SOURCE_KIND_RANK.get(
            group.source_kinds.get(group.copies[i].source,
                                   getattr(collected.sources.get(group.copies[i].source),
                                           "kind", "aggregator")), 3))
        for copy_index in order:
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
                group.copies[copy_index] = known
                remembered += 1
                break
        if _complete_ad(group.best_description_copy):
            continue
        options, seen = [], set()
        for copy_index in order:
            copy = group.copies[copy_index]
            identity = (copy.source, copy.source_job_id,
                        None if copy.source_job_id else copy.url)
            source, report = collected.sources.get(copy.source), reports.get(copy.source)
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
                    full = source.load_details(dataclasses.replace(
                        copy, job_types=list(copy.job_types)), ctx)
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
                if complete or not pending[index]:
                    done[0] += 1
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
        pending = {i: options for i, options in pending.items()
                   if options and not _complete_ad(groups[i].best_description_copy)}


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
            "label": (f"Jobcu doesn't know where \"{where}\" is, so {conditions} couldn't be "
                      "checked" if where else
                      f"{source_names.get(main.source, main.source)} doesn't say which town "
                      f"this job is in, nor does its text, so {conditions} couldn't be checked"),
            "status": "unclear", "source": None, "detail": None, "whole_sentence": True,
        })
    start = window_start(started_at, posted_within_hours)
    state = state or JobState()
    # An old ad posted again looks fresh; Jobcu's memory knows when it first showed this job.
    earliest = earliest_possible(group.posted_at, group.date_precision)
    reposted = bool(first_seen_at and earliest and first_seen_at < earliest - timedelta(days=1))
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
        "parts": scored["parts"] if scored else None,
        # Blockers that hold the score below what its parts add up to (scoring.py).
        "limits": (scored or {}).get("limits", []),
        "score_notes": (scored or {}).get("notes", []),
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
    if read and (not stated or (len(stated) > 1 and read in stated)):
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
    """Highest score first; newer first when scores are equal."""
    return sorted(
        cards,
        key=lambda c: (
            c["score"] is None,
            -(c["score"] or 0),
            -(_timestamp(c["posted_at"])),
        ),
    )


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
