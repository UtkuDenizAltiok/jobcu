"""Greenhouse career sites through the public Job Board API (no key for GET).
Current contract/access evidence: docs/SOURCES.md, Greenhouse temporal evidence.

`GET /v1/boards/{board}/jobs?content=true` lists jobs with original full text, location and
first publication when supplied. An update is not publication. The existing detail endpoint
remains a fallback for missing text and temporal metadata.
"""

import dataclasses
import html
from collections.abc import Iterator
from datetime import datetime

from jobcu.freshness import day_at_utc, parse_closing, parse_iso
from jobcu.sources.base import DatePrecision, FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import CareerSystemSource, Employer, work_mode_from_text
from jobcu.text import html_to_text

API = "https://boards-api.greenhouse.io/v1/boards"


class GreenhouseSource(CareerSystemSource):
    id = "greenhouse"
    name = "Company career sites (Greenhouse)"
    system = "greenhouse"
    detail_cache_version = 2  # older caches can contain an update as their posting date
    details_supply_dates = True

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        data = self.get_json(f"{API}/{employer.board}/jobs", ctx, params={"content": "true"})
        for item in data.get("jobs") or []:
            yield to_found_job(item, employer)

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        board = job.source_job_id.split("/", 1)[0]
        job_id = job.source_job_id.split("/", 1)[-1]
        try:
            item = self.get_json(f"{API}/{board}/jobs/{job_id}", ctx)
        except (SourceError, BudgetExhausted, ValueError):
            return job
        description = html_to_text(html.unescape(item.get("content") or ""))
        posted, precision = _publication(item)
        offices = "; ".join(o.get("location") or o.get("name") or ""
                            for o in item.get("offices") or [])
        return dataclasses.replace(
            job,
            description=description or job.description,
            description_is_complete=bool(description) or job.description_is_complete,
            work_mode=job.work_mode or work_mode_from_text(job.location_text or offices),
            posted_at=posted or job.posted_at,
            date_precision=precision if posted else job.date_precision,
            closes_at=_deadline(item) or job.closes_at,
        )


def to_found_job(item: dict, employer: Employer) -> FoundJob:
    posted, precision = _publication(item)
    location = (item.get("location") or {}).get("name")
    description = html_to_text(html.unescape(item.get("content") or ""))
    return FoundJob(
        source="greenhouse",
        source_job_id=f"{employer.board}/{item.get('id')}",
        url=item.get("absolute_url") or "",
        title=(item.get("title") or "").strip(),
        company=employer.name,
        location_text=location,
        posted_at=posted,
        date_precision=precision,
        closes_at=_deadline(item),
        work_mode=work_mode_from_text(location),
        description=description,
        description_is_complete=bool(description),
    )


def _publication(item: dict) -> tuple[datetime | None, DatePrecision]:
    value = item.get("first_published")
    if not isinstance(value, str):
        return None, "unknown"
    value = value.strip()
    posted = parse_iso(value)
    if posted is None:
        return None, "unknown"
    if len(value) in (8, 10):
        return day_at_utc(posted.date()), "day"
    return posted, "exact"


def _deadline(item: dict) -> datetime | None:
    value = item.get("application_deadline")
    return parse_closing(value) if isinstance(value, str) else None
