"""SmartRecruiters career pages (Continental, Aumovio, Renesas and others), checked 2026-11-24.

A company's public career page, `https://careers.smartrecruiters.com/{Company}`, lists every open
job grouped by place ("Regensburg, Germany: 12 jobs"), the groups in alphabetical order, the first
page of groups in the page and the others at `/{Company}/api/groups?page=N` (`data-groups-pages`
says how many). Each job has its title and its page, `https://jobs.smartrecruiters.com/{Company}/
{id}-{title}`, which carries the standard job data as page markup (schema.org JobPosting): the
exact posting time, the place, the employment type and the full ad. SmartRecruiters' own interface
(`api.smartrecruiters.com`) asks every robot but LinkedIn's not to read it, so it isn't used; the
career and job pages have no robots rules. A company whose page leads to its own site (Bosch's to
jobs.bosch.com, which closes its job pages to robots) isn't followed there.

The lists give no dates, so a search reads a company's whole list, notes when each job is first
seen (`listmemory`), opens the pages of the titles in a searched country that match the search
words (at most PAGES_PER_COMPANY, new ones first; a page read once is remembered) and gives the
titles the words miss to the person's AI only when they are new since the list's last reading.

SmartRecruiters' terms for job seekers don't allow "automatic means to access content or data from
other users", so the source is read only for a person who switches it on in Settings, accepting
that (sources.TERMS_NOTES).
"""

import dataclasses
import html
import re
from collections.abc import Iterator

from jobcu import listmemory
from jobcu import places as place_list
from jobcu.countries import COUNTRIES
from jobcu.freshness import freshness
from jobcu.placenames import OTHER, countries_in
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import CareerSystemSource, Employer, Survey, job_types_from_text
from jobcu.sources.matching import matches_terms
from jobcu.sources.successfactors import date_posted, read_page
from jobcu.text import html_to_text

LIST = "https://careers.smartrecruiters.com/{board}"
MORE = "https://careers.smartrecruiters.com/{board}/api/groups?page={page}"
# Pages of groups read for one company: Continental had 34 (2026-11-24).
MAX_GROUP_PAGES = 80
# Job pages opened for one company in a search, jobs new on the list first. A page read once is
# remembered, so a first search opens the rest over the next ones.
PAGES_PER_COMPANY = 30

_GROUP = re.compile(r'<section[^>]*class="[^"]*openings-section[^"]*"[^>]*>(.*?)</section>', re.S)
_GROUP_TITLE = re.compile(r'<h3[^>]*class="[^"]*opening-title[^"]*"[^>]*>(.*?)</h3>', re.S)
_JOB = re.compile(r'<a href="(https://jobs\.smartrecruiters\.com/[^"/]+/(\d+)[^"]*)"[^>]*>'
                  r'.*?<h4[^>]*>(.*?)</h4>', re.S)
_PAGES = re.compile(r'data-groups-pages="(\d+)"')
_COUNTRY = re.compile(r'itemprop="addressCountry"\s+content="([^"]*)"')
_TYPE = re.compile(r'itemprop="employmentType"[^>]*>([^<]*)<')


class SmartRecruitersSource(CareerSystemSource):
    id = "smartrecruiters"
    name = "Company career sites (SmartRecruiters)"
    system = "smartrecruiters"

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        listed = self._list(employer, ctx)
        if terms is None:
            yield from listed  # the directory check: titles and places, no pages opened
            return
        sights = listmemory.note(self.id, employer.board, [job.source_job_id for job in listed])
        matched, new_unmatched = [], []
        for job in listed:
            if countries and job.country not in countries:
                continue
            languages = {"en", *(COUNTRIES[job.country].ad_languages if job.country else ())}
            posted, precision = listmemory.posted(sights.get(job.source_job_id), start)
            job = dataclasses.replace(job, posted_at=posted, date_precision=precision)
            if matches_terms(terms, languages, job.title):
                matched.append(job)
            elif precision == "day" and (
                    start is None or freshness(posted, precision, start) == "fresh"):
                # Titles the search words miss go to the person's AI, only when new on the
                # list: every open job's title each search would be hundreds, nearly all old.
                new_unmatched.append(job)
        matched.sort(key=lambda job: job.date_precision != "day")  # new on the list first
        opened = 0
        for job in matched:
            known = self._remembered(job)
            if known is None:
                if opened >= PAGES_PER_COMPANY:
                    continue
                opened += 1
                known = self._from_page(job, ctx)
            if known is not None:
                yield known
        yield from new_unmatched

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        survey = Survey()
        for job in self._list(employer, ctx):
            code = job.country or OTHER
            town = place_list.locate(job.location_text, code) if code in COUNTRIES else None
            survey.add(code, town.name if town else None)
        return survey

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        """A job listed by its title only (one the search words missed): its page's place, ad
        and posting time."""
        return self._from_page(job, ctx) or job

    def _list(self, employer: Employer, ctx: SourceContext) -> list[FoundJob]:
        """Every listed job once, with its group's place: one in several places is kept with the
        first place in a supported country."""
        address = LIST.format(board=employer.board)
        if not self.allowed(address, ctx):
            raise SourceError(f"{employer.name}'s career page asks automated tools not to read "
                              "it.")
        # A company whose page leads to its own site isn't followed there (its robots.txt may
        # close it: Bosch's does); any answer but the page itself stops this company.
        response = self.get(address, ctx, follow_redirects=False)
        pages = _PAGES.search(response.text)
        texts = [response.text]
        for page in range(1, min(int(pages.group(1)) if pages else 1, MAX_GROUP_PAGES)):
            texts.append(self.get(MORE.format(board=employer.board, page=page), ctx).text)
        listed: dict[str, FoundJob] = {}
        for text in texts:
            for job in groups(text, employer):
                known = listed.get(job.source_job_id)
                if known is None or (known.country in (None, OTHER)
                                     and job.country not in (None, OTHER)):
                    listed[job.source_job_id] = job
        return [dataclasses.replace(job, country=None) if job.country == OTHER else job
                for job in listed.values()]

    def _remembered(self, job: FoundJob) -> FoundJob | None:
        # Imported here: the job memory itself imports the sources (through dedupe).
        from jobcu import jobstore

        known = jobstore.remembered_ad(job, reader_version=self.detail_cache_version)
        if known is None or not known.description_is_complete:
            return None
        return dataclasses.replace(known, title_unmatched=False, older_copy=False)

    def _from_page(self, job: FoundJob, ctx: SourceContext) -> FoundJob | None:
        """The job with its page's place, ad and posting time; None if it can't be read."""
        from jobcu import jobstore

        if not self.allowed(job.url, ctx):
            return None
        try:
            page = self.get(job.url, ctx, cache=False).text
        except (SourceError, BudgetExhausted):
            return None
        found = read_page(page)
        if not found.get("has_description"):
            return None
        posted = date_posted(page)
        country = _COUNTRY.search(page)
        town = found.get("places") or found.get("place")
        place = ", ".join(part for part in (town, country and country.group(1)) if part)
        # A job listed in several places has its main one on its page: kept only when it is in
        # the country the job was listed for here (Renesas listed an Edinburgh job under
        # 's-Hertogenbosch too).
        if job.country and job.country not in countries_in(place):
            place = ""
        # Some companies put a street in the town field ("Continentalstraße 3-5"): the list's
        # town stands then.
        if place and job.location_text and place_list.locate(place, job.country or "") is None:
            place = ""
        kind = _TYPE.search(page)
        full = dataclasses.replace(
            job,
            title=found.get("title") or job.title,
            description=found.get("description") or "",
            description_is_complete=True,
            location_text=place or job.location_text,
            posted_at=posted or job.posted_at,
            date_precision="exact" if posted else job.date_precision,
            job_types=job_types_from_text(html.unescape(kind.group(1))) if kind else job.job_types,
        )
        jobstore.remember_ad(full, reader_version=self.detail_cache_version)
        return full


def groups(text: str, employer: Employer) -> list[FoundJob]:
    """The jobs of one page of groups, each with its group's place ("Regensburg, Germany")."""
    jobs = []
    for group in _GROUP.findall(text):
        title = _GROUP_TITLE.search(group)
        place = html.unescape(html_to_text(title.group(1))).strip() if title else ""
        codes = countries_in(place)
        code = next(iter(codes)) if len(codes) == 1 else OTHER if codes else None
        for url, _, name in _JOB.findall(group):
            jobs.append(FoundJob(
                source=SmartRecruitersSource.id, source_job_id=html.unescape(url),
                url=html.unescape(url), title=html.unescape(html_to_text(name)).strip(),
                company=employer.name, location_text=place or None, country=code,
                employer_url=html.unescape(url)))
    return jobs
