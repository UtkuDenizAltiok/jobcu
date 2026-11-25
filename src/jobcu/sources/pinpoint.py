"""Pinpoint career sites (`{company}.pinpointhq.com`), checked 2026-11-25 (SOURCES.md).

A company's public job feed, `https://{company}.pinpointhq.com/postings.json` (or the same address
on the company's own career site that Pinpoint serves: Sagentia's), lists every
published job with its title, place, type, workplace, closing time and the full ad (description,
responsibilities, skills, benefits): what the company's career page itself shows. robots.txt
closes only account and admin areas. The feed gives no posting date; each job's page carries the
standard job data (schema.org JobPosting) with the exact posting time and the country. So a search
reads the feed (one request), notes when each job is first seen (`listmemory`), opens the pages of
the jobs whose titles match the search words for their posting time (a page read once is
remembered) and gives titles the words miss to the person's AI when the job is new on the list
since its last reading. LiveLink Aerospace (Havant, UK) was the first employer in electronics seen
on it.
"""

import dataclasses
from collections.abc import Iterator
from datetime import datetime

from jobcu import listmemory
from jobcu import places as place_list
from jobcu.countries import COUNTRIES
from jobcu.freshness import freshness, parse_iso
from jobcu.placenames import OTHER, countries_in
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import (
    CareerSystemSource,
    Employer,
    Survey,
    job_types_from_text,
    work_mode_from_text,
)
from jobcu.sources.matching import matches_terms
from jobcu.sources.sitemaps import to_found_job
from jobcu.text import html_to_text

FEED = "https://{host}/postings.json"
# Job pages opened per company and search for their posting time, new ones first; Pinpoint's
# companies are small (LiveLink Aerospace listed two jobs).
PAGES_PER_COMPANY = 30
# The parts of the ad, in the order the career page shows them, with the feed's own headings.
_SECTIONS = (("key_responsibilities", "key_responsibilities_header"),
             ("skills_knowledge_expertise", "skills_knowledge_expertise_header"),
             ("benefits", "benefits_header"))


class PinpointSource(CareerSystemSource):
    id = "pinpoint"
    name = "Company career sites (Pinpoint)"
    system = "pinpoint"
    # The feed lists every job wherever it is, in one answer.
    asks_every_employer = True

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        listed = self._list(employer, ctx)
        if terms is None:
            yield from listed  # the directory check: titles and places, no pages opened
            return
        sights = listmemory.note(self.id, employer.board, [job.source_job_id for job in listed])
        matched, new_unmatched = [], []
        for job in listed:
            if countries and job.country and job.country not in countries:
                continue
            languages = {"en", *(COUNTRIES[job.country].ad_languages if job.country else ())}
            posted, precision = listmemory.posted(sights.get(job.source_job_id), start)
            job = dataclasses.replace(job, posted_at=posted, date_precision=precision)
            if matches_terms(terms, languages, job.title):
                matched.append(job)
            elif precision == "day" and (
                    start is None or freshness(posted, precision, start) == "fresh"):
                new_unmatched.append(job)  # its ad is there: the AI's title check decides
        matched.sort(key=lambda job: job.date_precision != "day")  # new on the list first
        opened = 0
        for job in matched:
            known = self._remembered(job)
            if known is None and opened < PAGES_PER_COMPANY:
                opened += 1
                known = self._from_page(job, ctx)
            # Without its page the job keeps the feed's ad and the date its first sight gives.
            yield known or job
        yield from new_unmatched

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        survey = Survey()
        for job in self._list(employer, ctx):
            code = job.country or "unknown"
            town = place_list.locate(job.location_text, code) if code in COUNTRIES else None
            survey.add(code, town.name if town else None)
        return survey

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        """A job the title check kept: its page's exact posting time and country."""
        return self._remembered(job) or self._from_page(job, ctx) or job

    def _list(self, employer: Employer, ctx: SourceContext) -> list[FoundJob]:
        address = FEED.format(host=host_of(employer.board))
        if not self.allowed(address, ctx):
            raise SourceError(f"{employer.name}'s career site asks automated tools not to read "
                              "its job list.")
        try:
            postings = self.get(address, ctx).json().get("data") or []
        except ValueError as exc:
            raise SourceError(f"{employer.name}'s job list couldn't be read.") from exc
        return [job for posting in postings
                if isinstance(posting, dict) and (job := to_job(posting, employer)) is not None]

    def _remembered(self, job: FoundJob) -> FoundJob | None:
        # Imported here: the job memory itself imports the sources (through dedupe).
        from jobcu import jobstore

        known = jobstore.remembered_ad(job, reader_version=self.detail_cache_version)
        if known is None or known.posted_at is None:
            return None
        return dataclasses.replace(known, title_unmatched=False, older_copy=False)

    def _from_page(self, job: FoundJob, ctx: SourceContext) -> FoundJob | None:
        """The job with its page's exact posting time and country; the feed's ad stays (it is
        the whole ad, with its headings)."""
        from jobcu import jobstore

        if not self.allowed(job.url, ctx):
            return None
        try:
            page = self.get(job.url, ctx, cache=False).text
        except (SourceError, BudgetExhausted):
            return None
        posting = to_found_job(job.url, page, Employer(job.company or "", self.system, "", ()),
                               source=self.id)
        if posting is None or posting.posted_at is None:
            return None
        full = dataclasses.replace(
            job, posted_at=posting.posted_at, date_precision=posting.date_precision,
            country=job.country or posting.country,
            location_text=job.location_text or posting.location_text)
        jobstore.remember_ad(full, reader_version=self.detail_cache_version)
        return full


def host_of(board: str) -> str:
    """A board is the company's name on Pinpoint ("livelink") or, for a career site on the
    company's own address that Pinpoint serves, that address ("careers.sagentia.com")."""
    return board if "." in board else f"{board}.pinpointhq.com"


def to_job(posting: dict, employer: Employer) -> FoundJob | None:
    title = (posting.get("title") or "").strip()
    url = posting.get("url") or ""
    if not title or not url.startswith("https://"):
        return None
    location = posting.get("location") if isinstance(posting.get("location"), dict) else {}
    town = location.get("city") or location.get("name")
    place = ", ".join(dict.fromkeys(
        str(part).strip() for part in (town, location.get("province"),
                                       location.get("postal_code")) if part))
    remote = posting.get("workplace_type") == "remote"
    closes = parse_iso(posting.get("deadline_at") or "")
    return FoundJob(
        source=PinpointSource.id, source_job_id=url, url=url, title=title,
        company=employer.name, location_text=place or None, country=_country(place),
        description=_ad(posting), description_is_complete=True,
        job_types=job_types_from_text(posting.get("employment_type_text")
                                      or posting.get("employment_type")),
        work_mode="remote" if remote else work_mode_from_text(posting.get("workplace_type_text")),
        employer_url=url, closes_at=closes if isinstance(closes, datetime) else None)


def _country(place: str) -> str | None:
    """The country a feed's place names: by a UK postcode or an Eircode, or by name."""
    if not place:
        return None
    if (town := place_list.postcode_town(place)) is not None:
        return town.country
    found = countries_in(place) - {OTHER}
    return next(iter(found)) if len(found) == 1 else None


def _ad(posting: dict) -> str:
    parts = [html_to_text(posting.get("description"))]
    for body, heading in _SECTIONS:
        if text := html_to_text(posting.get(body)):
            parts.append(f"{(posting.get(heading) or '').strip()}\n{text}".strip())
    return "\n\n".join(part for part in parts if part)
