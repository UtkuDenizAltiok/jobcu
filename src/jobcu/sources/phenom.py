"""Phenom career sites (ABB, Siemens Healthineers, Thermo Fisher, RTX and others), checked
2026-11-24.

A Phenom career site (`careers.abb/global/en/search-results`) answers its own search page at
`POST https://{host}/widgets` with `{"ddoKey": "refineSearch", "selected_fields": {"country":
["Germany"]}, "from": 0, "size": 50, ...}`: the jobs of the chosen countries, each with its title,
places, posting day and number, and how many jobs each country has (`aggregations`). A job's page,
`https://{host}/{site}/{language}/job/{number}`, carries the standard job data (JobPosting) with the
full ad. Their robots.txt closes only `px-widgets`, the apply pages and tracking. The board is the
site's address and section, "careers.abb/global/en": the section's language and region are part of
every request (`lang` "en_global", `country` "global").

The lists give each job's posting day, so a search reads the searched countries' lists whole (ABB
had 129 jobs in Germany: three requests) and opens a page only for a job still in the running
(`load_details`).

ABB's website terms don't allow scraping without its written permission, so the source is read only
for a person who switches it on in Settings, accepting that (sources.TERMS_NOTES).
"""

import dataclasses
from collections.abc import Iterator
from datetime import date

from jobcu.freshness import day_at_utc
from jobcu.jobposting import find_job_posting
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
from jobcu.text import html_to_text

PAGE_SIZE = 50
# Pages of one country's list in a search: Thermo Fisher had 176 jobs in the UK (four pages).
MAX_PAGES_PER_COUNTRY = 20
HEADERS = {"Accept": "application/json"}


@dataclasses.dataclass(frozen=True)
class Site:
    host: str
    section: str  # "global/en"

    @property
    def body(self) -> dict:
        region, language = self.section.split("/", 1)
        return {"lang": f"{language}_{region}", "country": region, "deviceType": "desktop",
                "pageName": "search-results", "ddoKey": "refineSearch", "sortBy": "",
                "subsearch": "", "jobs": True, "counts": True, "clearAll": False,
                "jdsource": "facets", "isSliderEnable": False, "siteType": "external",
                "keywords": "", "global": True, "locationData": {}}


def parse_board(board: str) -> Site:
    """"careers.abb/global/en" → its host and section."""
    host, _, section = board.strip("/").partition("/")
    if not host or section.count("/") != 1:
        raise SourceError(f"Not a Phenom career site address: {board}")
    return Site(host, section)


class PhenomSource(CareerSystemSource):
    id = "phenom"
    name = "Company career sites (Phenom)"
    system = "phenom"
    parallel = 4  # every employer has its own host
    # A list gives a job's places and an ad's opening; its page has the full ad.
    details_supply_locations = True

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        site = parse_board(employer.board)
        values = self._country_values(site, ctx)
        wanted = countries if countries is not None else sorted(values)
        seen: set[str] = set()
        for code in wanted:
            if not values.get(code):
                continue
            for page in range(MAX_PAGES_PER_COUNTRY):
                answer = self._ask(site, ctx, {"country": values[code]}, page * PAGE_SIZE)
                jobs = answer.get("data", {}).get("jobs") or []
                for item in jobs:
                    job = to_found_job(item, site, employer, code)
                    if job is not None and job.source_job_id not in seen:
                        seen.add(job.source_job_id)
                        yield job
                if len(jobs) < PAGE_SIZE or (page + 1) * PAGE_SIZE >= int(
                        answer.get("totalHits") or 0):
                    break

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        """The site's own count of jobs per country."""
        site = parse_board(employer.board)
        survey = Survey()
        for value, count in self._aggregation(site, ctx).items():
            codes = countries_in(value) - {OTHER}
            survey.counts[next(iter(codes)) if len(codes) == 1 else OTHER] += int(count or 0)
        return survey

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        """The full ad from the job's page; the list's day stands unless the page's is earlier."""
        if not self.allowed(job.url, ctx):
            return job
        try:
            posting = find_job_posting(self.get(job.url, ctx).text)
        except (SourceError, BudgetExhausted):
            return job
        if posting is None or not (posting.description or "").strip():
            return job
        posted, precision = job.posted_at, job.date_precision
        if posting.date_posted and (posted is None or posting.date_posted < posted):
            posted, precision = posting.date_posted, "day"
        return dataclasses.replace(
            job,
            description=posting.description,
            description_is_complete=posting.description_is_complete,
            location_text=job.location_text or posting.location_text,
            posted_at=posted,
            date_precision=precision,
            job_types=job.job_types or posting.job_types,
            closes_at=posting.valid_through or job.closes_at,
        )

    def _country_values(self, site: Site, ctx: SourceContext) -> dict[str, list[str]]:
        """The site's own names for each supported country ("Germany", "Deutschland")."""
        values: dict[str, list[str]] = {}
        for value in self._aggregation(site, ctx):
            codes = countries_in(value) - {OTHER}
            if len(codes) == 1:
                values.setdefault(next(iter(codes)), []).append(value)
        return values

    def _aggregation(self, site: Site, ctx: SourceContext) -> dict[str, int]:
        answer = self._ask(site, ctx, {}, 0, size=1)
        for aggregation in answer.get("data", {}).get("aggregations") or []:
            if aggregation.get("field") == "country":
                return dict(aggregation.get("value") or {})
        return {}

    def _ask(self, site: Site, ctx: SourceContext, selected: dict, offset: int,
             size: int = PAGE_SIZE) -> dict:
        address = f"https://{site.host}/widgets"
        if not self.allowed(address, ctx):
            raise SourceError(f"{site.host} asks automated tools not to read its job list.")
        body = {**site.body, "selected_fields": selected, "all_fields": ["country"],
                "from": offset, "size": size}
        answer = self.get_json(address, ctx, method="POST", json=body, headers=HEADERS)
        search = (answer or {}).get("refineSearch") if isinstance(answer, dict) else None
        if not isinstance(search, dict):
            raise SourceError(f"{self.name} didn't answer with a job list.")
        return search


def to_found_job(item: dict, site: Site, employer: Employer, country: str) -> FoundJob | None:
    number, title = str(item.get("jobId") or "").strip(), (item.get("title") or "").strip()
    if not number or not title:
        return None
    places = [place for place in (item.get("multi_location") or [item.get("location")])
              if isinstance(place, str) and place.strip()]
    try:
        day = date.fromisoformat(str(item.get("postedDate") or "")[:10])
    except ValueError:
        day = None
    url = f"https://{site.host}/{site.section}/job/{number}"
    return FoundJob(
        source=PhenomSource.id,
        source_job_id=url,
        url=url,
        title=title,
        company=employer.name,
        location_text="; ".join(dict.fromkeys(places)) or None,
        country=country,
        posted_at=day_at_utc(day) if day else None,
        date_precision="day" if day else "unknown",
        description=html_to_text(item.get("descriptionTeaser") or ""),
        job_types=job_types_from_text(" ".join(
            str(item.get(key) or "") for key in ("type", "jobType", "contractType"))),
        work_mode=work_mode_from_text(" ".join(
            str(item.get(key) or "") for key in ("remote", "workplaceType", "location"))),
        employer_url=url,
    )
