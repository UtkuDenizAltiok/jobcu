"""Job sitemaps: recruiters' and employers' own sites that list every job page for search engines
(sitemaps.org), each page carrying the standard job data (schema.org JobPosting), checked
2026-10-03 (SOURCES.md, "Job sitemaps with JobPosting pages").

A board is the address of the site's job sitemap. Jobcu reads it (one request; a sitemap index
leads to its job sitemaps), keeps the job pages changed since the window began when the sitemap
gives dates, and opens only those whose address spells words matching the search words
("/jobs/27724/graduate-electronics-engineer"), newest first. Each page's JobPosting data gives
the title, the full ad, the exact posting date, the town and country, the company and the job
type. Pages are remembered for a few days (`jobstore`), so later searches don't open them again.

Only sites whose terms allow it are in the directory: a recruiter's own copy of an ad that Adzuna
shows as a 500-character summary gives the full ad for scoring (search 11: 204 of 349 cards were
Adzuna summaries, Redline Group's about 20 of them).
"""

import gzip
import re
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from urllib.parse import unquote, urlsplit

from jobcu.countries import COUNTRIES
from jobcu.freshness import parse_iso
from jobcu.jobposting import find_job_posting
from jobcu.placenames import OTHER, countries_in
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import CareerSystemSource, Employer
from jobcu.sources.matching import matches_terms

# Job pages opened per site in one search, newest first: enough for every fresh match on the
# sites checked, and a cap when a site gives no dates.
MAX_PAGES = 60
# Pages looked at to tell which countries a site's jobs are in (the directory check).
SURVEY_PAGES = 20
# Job sitemaps a sitemap index may lead to.
MAX_SITEMAPS = 5

_URL = re.compile(r"<url>\s*<loc>\s*([^<\s]+)\s*</loc>(?:\s*<lastmod>\s*([^<\s]+)\s*</lastmod>)?",
                  re.S)
_INDEX = re.compile(r"<sitemap>\s*<loc>\s*([^<\s]+)\s*</loc>", re.S)
_JOB_WORDS = re.compile(r"job|stelle|vacanc|position|career|karriere|vacature|offre", re.I)
_LONG_AGO = datetime.min.replace(tzinfo=UTC)


class SitemapSource(CareerSystemSource):
    id = "sitemap"
    name = "Recruiters' and employers' own sites"
    system = "sitemap"
    parallel = 4  # every site has its own address

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        entries = self._entries(employer.board, ctx)
        since = start - timedelta(days=1) if start else None
        languages = {"en"}
        for code in countries or ():
            languages.update(COUNTRIES[code].ad_languages)
        opened = 0
        for address, changed in entries:
            if opened >= (MAX_PAGES if terms is not None else SURVEY_PAGES):
                return
            if since is not None and changed is not None and changed < since:
                continue
            if terms is not None and not matches_terms(terms, languages, words_of(address)):
                continue
            opened += 1
            job = self._from_page(address, employer, ctx)
            if job is not None:
                yield job

    def readable(self, employer: Employer, ctx: SourceContext) -> bool:
        """One job page must carry JobPosting data with its posting date."""
        for job in self.list_jobs(employer, ctx):
            return job.posted_at is not None
        return False

    def _entries(self, board: str, ctx: SourceContext) -> list[tuple[str, datetime | None]]:
        """The sitemap's job pages with their last change, newest first (undated ones last)."""
        if not self.allowed(board, ctx):
            raise SourceError(f"{self.name}: {urlsplit(board).hostname} asks automated tools "
                              "not to read its job list.")
        text = self._read(board, ctx)
        children = _INDEX.findall(text)
        if children:
            jobs = [child for child in children if _JOB_WORDS.search(urlsplit(child).path)]
            text = " ".join(self._read(child, ctx) for child in (jobs or children)[:MAX_SITEMAPS]
                            if self.allowed(child, ctx))
        entries = [(unescape(address), parse_iso(changed) if changed else None)
                   for address, changed in _URL.findall(text)]
        entries = [(address, changed) for address, changed in entries
                   if _JOB_WORDS.search(urlsplit(address).path)]
        return sorted(dict(entries).items(),
                      key=lambda entry: (entry[1] is not None, entry[1] or _LONG_AGO),
                      reverse=True)

    def _read(self, address: str, ctx: SourceContext) -> str:
        body = self.get(address, ctx).content
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return body.decode("utf-8", "replace")

    def _from_page(self, address: str, employer: Employer, ctx: SourceContext) -> FoundJob | None:
        """The job from memory or from its page's JobPosting data; None without such data."""
        # Imported here: the job memory itself imports the sources (through dedupe).
        from jobcu import jobstore

        stub = FoundJob(source=self.id, source_job_id=address, url=address, title="")
        known = jobstore.remembered_ad(stub)
        if known is not None and known.title:
            return known
        if not self.allowed(address, ctx):
            return None
        try:
            page = self.get(address, ctx, cache=False).text
        except (SourceError, BudgetExhausted):
            return None
        job = to_found_job(address, page, employer)
        if job is not None:
            jobstore.remember_ad(job)
        return job


def to_found_job(address: str, page: str, employer: Employer) -> FoundJob | None:
    posting = find_job_posting(page)
    if posting is None or not posting.title:
        return None
    return FoundJob(
        source=SitemapSource.id,
        source_job_id=address,
        url=address,
        title=posting.title,
        company=posting.company or employer.name,
        location_text=posting.location_text,
        country=country_code(posting.country),
        posted_at=posting.date_posted,
        date_precision=("exact" if posting.date_has_time else "day") if posting.date_posted
        else "unknown",
        description=posting.description,
        description_is_complete=bool(posting.description),
        job_types=posting.job_types,
        work_mode="remote" if posting.remote else None,
        employer_url=address,
        closes_at=posting.valid_through,
    )


def country_code(written: str | None) -> str | None:
    """A supported country's code from what JobPosting data says ("GB", "UK", "Deutschland")."""
    if not written:
        return None
    code = written.strip().upper()
    if code == "UK":
        code = "GB"
    if code in COUNTRIES:
        return code
    found = countries_in(written) - {OTHER}
    return next(iter(found)) if len(found) == 1 else None


def words_of(address: str) -> str:
    """The words a job page's address spells, for matching the search words before opening it."""
    return " ".join(re.split(r"[/_\-.?=&+%]+", unquote(urlsplit(address).path)))


def unescape(address: str) -> str:
    return address.replace("&amp;", "&")
