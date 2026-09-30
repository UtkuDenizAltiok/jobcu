"""Softgarden career sites, common with German mid-sized employers and hotel groups (PULS, the
employer finder's suggestions), checked 2026-09-30.

A company's list page, `https://{company}.softgarden.io/de/vacancies`, is plain HTML: every job
is a block `<div class="matchElement" id="job_id_{id}">` with its posting day ("01.09.26"), its
title linking to `../job/{id}/{words}`, the audience ("Berufserfahrene", "Student/in"), the
category and the towns. The job's own page carries the standard job data (schema.org
JobPosting): the full ad, the exact posting time, the place and the company. robots.txt closes
the API, widgets and application pages, and leaves the list and job pages open.

A board is the company's Softgarden name, or its full host.
"""

import dataclasses
import html
import re
from collections.abc import Iterator
from datetime import date

from jobcu.freshness import day_at_utc
from jobcu.jobposting import find_job_posting
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import CareerSystemSource, Employer, work_mode_from_text
from jobcu.text import tidy

_BLOCK = re.compile(r'<div class="matchElement[^"]*" id="job_id_(\d+)"(.*?)(?=<div class="'
                    r'matchElement[^"]*" id="job_id_|\Z)', re.S)
_DATE = re.compile(r'class="matchValue date">\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})\s*<')
_TITLE = re.compile(r'<a href="(?:\.\./)?(job/\d+/[^"]*)"[^>]*>(.*?)</a>', re.S)
_AUDIENCE = re.compile(r'class="matchValue audience">(.*?)</div>', re.S)
_TOWN = re.compile(r'class="location-view-item">(.*?)</span>', re.S)
_STUDENT = re.compile(r"student|praktik|intern|azubi|ausbildung|schüler|trainee", re.I)


class SoftgardenSource(CareerSystemSource):
    id = "softgarden"
    name = "Company career sites (Softgarden)"
    system = "softgarden"
    parallel = 4  # every employer has its own address

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        address = f"https://{host(employer.board)}/de/vacancies"
        if not self.allowed(address, ctx):
            raise SourceError(f"{employer.name} asks automated tools not to read its job list.")
        page = self.get(address, ctx, cache=False).text
        yield from parse_list(page, employer)

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        if not self.allowed(job.url, ctx):
            return job
        try:
            page = self.get(job.url, ctx, cache=False).text
        except (SourceError, BudgetExhausted):
            return job
        posting = find_job_posting(page)
        if posting is None or not posting.description:
            return job
        return dataclasses.replace(
            job,
            description=posting.description,
            description_is_complete=True,
            posted_at=posting.date_posted or job.posted_at,
            date_precision=("exact" if posting.date_has_time else "day")
            if posting.date_posted else job.date_precision,
            location_text=job.location_text or posting.location_text,
            job_types=posting.job_types or job.job_types,
            closes_at=posting.valid_through or job.closes_at,
        )


def host(board: str) -> str:
    return board if "." in board else f"{board}.softgarden.io"


def parse_list(page: str, employer: Employer) -> list[FoundJob]:
    """The jobs on a Softgarden list page, with their posting day and towns."""
    jobs = []
    for job_id, block in _BLOCK.findall(page or ""):
        title_match = _TITLE.search(block)
        if title_match is None:
            continue
        title = tidy(html.unescape(re.sub(r"<[^>]+>", " ", title_match.group(2))))
        day = _day(_DATE.search(block))
        towns = [tidy(html.unescape(town)) for town in _TOWN.findall(block) if town.strip()]
        audience = tidy(html.unescape((_AUDIENCE.search(block) or [None, ""])[1]))
        path = html.unescape(title_match.group(1)).split("?")[0]
        jobs.append(FoundJob(
            source="softgarden",
            source_job_id=f"{employer.board}/{job_id}",
            url=f"https://{host(employer.board)}/{path}",
            title=title,
            company=employer.name,
            location_text=", ".join(dict.fromkeys(towns)) or None,
            posted_at=day_at_utc(day) if day else None,
            date_precision="day" if day else "unknown",
            job_types=["internship_or_working_student"] if _STUDENT.search(audience) else [],
            work_mode=work_mode_from_text(" ".join(towns)),
        ))
    return jobs


def _day(match: re.Match | None) -> date | None:
    if match is None:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year + 2000 if year < 100 else year, month, day)
    except ValueError:
        return None
