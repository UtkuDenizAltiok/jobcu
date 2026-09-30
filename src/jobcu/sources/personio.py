"""Personio career sites, common with German mid-sized employers and start-ups (eMoSys, the
employer finder's suggestions), checked 2026-09-30.

`GET https://{company}.jobs.personio.de/search.json` lists every open job with its title, offices,
employment type ("Festanstellung"), schedule ("Vollzeit") and department, but no date and no
ad. The job's own page, `https://{company}.jobs.personio.de/job/{id}`, is plain HTML with the full
ad and carries `published_at` in its page data. The career sites have no robots.txt (404); Jobcu
asks each time. The old XML feed (`/xml`) is switched off by some companies (eMoSys: 404).

So Jobcu reads the list, opens only the pages of jobs whose title matches the search words (as
for SuccessFactors), and remembers each page's ad and date for a few days (`jobstore`), so later
searches don't open it again. A board is the company's Personio name, or the full host for
companies on `jobs.personio.com`.
"""

import dataclasses
import re
from collections.abc import Iterator

from jobcu.countries import COUNTRIES
from jobcu.freshness import parse_iso
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import (
    CareerSystemSource,
    Employer,
    job_types_from_text,
    work_mode_from_text,
)
from jobcu.sources.matching import matches_terms
from jobcu.text import html_to_text, tidy

_PUBLISHED = re.compile(r'\\?"published_at\\?":\\?"([0-9T:.+Z-]{10,32})')
_CREATED = re.compile(r'\\?"created_at\\?":\\?"([0-9T:.+Z-]{10,32})')
_SCRIPTS = re.compile(r"<script\b.*?</script>|<style\b.*?</style>", re.S | re.I)
# Personio's German words for the kinds of job, in the list's employment_type and schedule.
_GERMAN_TYPES = {"festanstellung": "permanent", "befristet": "fixed term",
                 "vollzeit": "full time", "teilzeit": "part time", "praktikum": "internship",
                 "werkstudent": "working student", "ausbildung": "apprentice",
                 "freelance": "freelance"}


class PersonioSource(CareerSystemSource):
    id = "personio"
    name = "Company career sites (Personio)"
    system = "personio"
    parallel = 4  # every employer has its own address

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        address = f"https://{host(employer.board)}/search.json"
        if not self.allowed(address, ctx):
            raise SourceError(f"{employer.name} asks automated tools not to read its job list.")
        data = self.get_json(address, ctx)
        languages = {"en"}
        for code in countries or ():
            languages.update(COUNTRIES[code].ad_languages)
        for item in data if isinstance(data, list) else []:
            job = to_found_job(item, employer)
            if job is None:
                continue
            if terms is None:
                yield job  # the directory check: every job, no pages opened
            elif matches_terms(terms, languages, job.title):
                full = self._from_page(job, ctx)
                if full is not None:
                    yield full

    def readable(self, employer: Employer, ctx: SourceContext) -> bool:
        """One job page must show its publication date."""
        for job in self.list_jobs(employer, ctx):
            full = self._from_page(job, ctx)
            return full is not None and full.posted_at is not None
        return False

    def _from_page(self, job: FoundJob, ctx: SourceContext) -> FoundJob | None:
        """The job with its ad and publication time, from memory or from its own page."""
        # Imported here: the job memory itself imports the sources (through dedupe).
        from jobcu import jobstore

        known = jobstore.remembered_ad(job)
        if known is not None and known.posted_at:
            return known
        if not self.allowed(job.url, ctx):
            return None
        try:
            page = self.get(job.url, ctx, cache=False).text
        except (SourceError, BudgetExhausted):
            return None
        full = read_page(job, page)
        jobstore.remember_ad(full)
        return full


def host(board: str) -> str:
    return board if "." in board else f"{board}.jobs.personio.de"


def to_found_job(item: dict, employer: Employer) -> FoundJob | None:
    job_id, title = item.get("id"), tidy(item.get("name") or "")
    if not job_id or not title:
        return None
    offices = [tidy(o) for o in (item.get("offices") or [item.get("office")]) if o]
    kinds = " ".join(_GERMAN_TYPES.get(word.casefold(), word) for word in
                     (item.get("employment_type") or "", item.get("schedule") or "") if word)
    return FoundJob(
        source="personio",
        source_job_id=f"{employer.board}/{job_id}",
        url=f"https://{host(employer.board)}/job/{job_id}",
        title=title,
        company=employer.name,
        location_text=", ".join(dict.fromkeys(offices)) or None,
        date_precision="unknown",
        job_types=job_types_from_text(kinds),
        work_mode=work_mode_from_text(" ".join(offices)),
    )


def read_page(job: FoundJob, page: str) -> FoundJob:
    """The ad's text and publication time from a job page."""
    match = _PUBLISHED.search(page) or _CREATED.search(page)
    posted = parse_iso(match.group(1)) if match else None
    text = html_to_text(_SCRIPTS.sub(" ", page))
    # The page starts with the site's menu; the ad starts at its title.
    at = text.find(job.title)
    description = tidy(text[at + len(job.title):] if at >= 0 else text)
    return dataclasses.replace(
        job,
        posted_at=posted,
        date_precision="exact" if posted else "unknown",
        description=description,
        description_is_complete=bool(description),
    )
