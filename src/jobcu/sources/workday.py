"""Workday career sites (used by many large employers). Checked 2026-09-17.

Workday has no documented public API. Each company's career site (e.g.
`https://analogdevices.wd1.myworkdayjobs.com/External`) loads its jobs from
`POST /wday/cxs/{tenant}/{site}/jobs` with `{"appliedFacets": {}, "limit": 20, "offset": 0,
"searchText": ""}`. The answer lists 20 jobs at a time, newest first, with the title, place
text and a relative date ("Posted Today", "Posted 3 Days Ago", "Posted 30+ Days Ago"), plus
filters such as the job's country with an ID each. A job's full ad and exact day come from
`GET /wday/cxs/{tenant}/{site}{externalPath}`.

Because the address isn't documented, Jobcu checks each site's robots.txt first and skips the
company if it disallows these addresses.

Since November 2026 Workday's wd1 and wd5 servers answer robots.txt, and at times the ads too, with
a human check, which Jobcu never passes; once one address has sent them a lot, they answer its job
lists the same way for a while (2026-11-25). So every company on one server shares that server's
polite pace, and a server that refuses three companies in a row isn't asked again in that search
(`http.server_of`). Some employers publish every vacancy on their own career site too, under the
same vacancy number ("R5049393" on Workday and in
`careers.gevernova.com/automation-engineer/job/R5049393`). For those the directory names that
site's job sitemap (`Employer.ads`), and an ad Workday won't serve is read from the employer's
page with the same number and title.
"""

import dataclasses
import re
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlsplit

from rapidfuzz import fuzz

from jobcu import places as place_list
from jobcu.freshness import day_at_utc, freshness
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
from jobcu.sources.http import Blocked
from jobcu.sources.sitemaps import country_code, job_pages
from jobcu.text import html_to_text

PAGE_SIZE = 20
MAX_PAGES_PER_COUNTRY = 25
HEADERS = {"Accept": "application/json", "Accept-Language": "en-US"}
_POSTED = re.compile(r"posted\s+(today|yesterday|(\d+)\+?\s+days?\s+ago)", re.IGNORECASE)
# A vacancy number as Workday lists show it ("R5045614", "R-01376627", "JR000678", "01883090"):
# at most four letters, then at least five digits, so it can't be mistaken for another number.
_NUMBER = re.compile(r"^[A-Za-z]{0,4}-?\d{5,}$")
# An address under a language's own path ("/fr/..."): an employer's site can list one vacancy
# once per language, and the version without one (usually English) is read first.
_LANGUAGE_PATH = re.compile(r"^/[a-z]{2}(?:-[a-z]{2})?/", re.IGNORECASE)
# How alike the employer's page title must be (0-100, every word of the shorter title found in
# the longer): a page with the same number and another title is not taken.
SAME_TITLE = 80


@dataclasses.dataclass(frozen=True)
class Site:
    host: str
    tenant: str
    site: str

    @property
    def api(self) -> str:
        return f"https://{self.host}/wday/cxs/{self.tenant}/{self.site}"


def parse_board(board: str) -> Site:
    """"https://acme.wd3.myworkdayjobs.com/en-US/Careers" → host, tenant "acme", site
    "Careers"."""
    parts = urlsplit(board if "//" in board else f"https://{board}")
    host = parts.hostname or ""
    segments = [s for s in parts.path.split("/") if s and not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", s)]
    if not host or not segments:
        raise SourceError(f"Not a Workday career site address: {board}")
    return Site(host=host, tenant=host.split(".")[0], site=segments[0])


def posted_day(text: str | None, today: date) -> date | None:
    match = _POSTED.search(text or "")
    if not match:
        return None
    word = match.group(1).lower()
    if word == "today":
        return today
    if word == "yesterday":
        return today - timedelta(days=1)
    return today - timedelta(days=int(match.group(2)))


class WorkdaySource(CareerSystemSource):
    id = "workday"
    name = "Company career sites (Workday)"
    system = "workday"
    parallel = 4
    details_supply_locations = True
    # Earlier cached bodies discarded the workplaces supplied in the same response.
    detail_cache_version = 2

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        site = parse_board(employer.board)
        self._check_robots(site, ctx)
        today = datetime.now(UTC).date()
        first = self._page(site, {}, 0, ctx)
        facets = country_facets(first)
        parameter = _country_facet(first.get("facets"))[0]
        wanted: list[tuple[str | None, list[str]]] = [(None, [])]
        if countries is not None and facets:
            wanted = [(code, [facet_id for facet_id, codes in facets.items() if code in codes])
                      for code in countries]
            wanted = [(code, ids) for code, ids in wanted if ids]
        seen: set[str] = set()
        for code, ids in wanted:
            for page in range(MAX_PAGES_PER_COUNTRY):
                data = first if not ids and page == 0 else self._page(
                    site, {parameter: ids} if ids else {}, page * PAGE_SIZE, ctx)
                postings = data.get("jobPostings") or []
                too_old = new = 0
                for item in postings:
                    # MSD's list held a record with neither (search 12): no job, a blank card.
                    if not (item.get("title") or "").strip() or not item.get("externalPath"):
                        continue
                    job = to_found_job(item, site, employer, code, today)
                    if start and freshness(job.posted_at, job.date_precision, start) == "too_old":
                        too_old += 1
                    if job.source_job_id in seen:
                        continue
                    seen.add(job.source_job_id)
                    new += 1
                    yield job
                # Lists come newest first; a page of only older jobs means the rest is older.
                # Some sites answer every later page with the same jobs (the same titles 25
                # times, 2026-09-24 night): a page with nothing new ends the list too.
                if len(postings) < PAGE_SIZE or (start and too_old == len(postings)) or not new:
                    break

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        """Workday's own filters already say how many jobs are in each country and town."""
        site = parse_board(employer.board)
        self._check_robots(site, ctx)
        answer = self._page(site, {}, 0, ctx)
        values = _country_facet(answer.get("facets"))[1]
        if not values:  # a site without a country filter: look at the jobs themselves
            return super().survey(employer, ctx)
        survey = Survey()
        for value in values:
            codes = {c for c in countries_in(value.get("descriptor")) if c != OTHER}
            for code in codes or {OTHER}:
                survey.counts[code] += int(value.get("count") or 0)
        for name, entries in _all_facets(answer.get("facets")):
            if "location" not in name.lower():
                continue
            for value in entries:  # "Germany, Munich" and the like
                for code in countries_in(value.get("descriptor")) - {OTHER}:
                    town = place_list.locate(value.get("descriptor"), code)
                    if town is not None:
                        survey.towns.setdefault(code, set()).add(town.name)
        return survey

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        try:
            info = self.get_json(job.source_job_id, ctx, headers=HEADERS).get(
                "jobPostingInfo") or {}
        except Blocked:
            # The ad behind a human check (never passed): the employer's own site may show it.
            if (own := self._from_own_site(job, ctx)) is None:
                raise
            return own
        except BudgetExhausted:
            return job
        except (SourceError, ValueError):
            return self._from_own_site(job, ctx) or job
        if not info:
            return self._from_own_site(job, ctx) or job
        description = html_to_text(info.get("jobDescription"))
        additional = info.get("additionalLocations")
        locations = [info.get("location"), *(additional if isinstance(additional, list) else [])]
        location = "; ".join(dict.fromkeys(
            value.strip() for value in locations if isinstance(value, str) and value.strip()))
        try:
            posted = day_at_utc(date.fromisoformat(info.get("startDate") or ""))
        except ValueError:
            posted = job.posted_at
        return dataclasses.replace(
            job,
            description=description or job.description,
            description_is_complete=bool(description) or job.description_is_complete,
            location_text=location or job.location_text,
            posted_at=posted,
            job_types=job_types_from_text(info.get("timeType")) or job.job_types,
            work_mode=work_mode_from_text(info.get("remoteType")) or job.work_mode,
        )

    def _from_own_site(self, job: FoundJob, ctx: SourceContext) -> FoundJob | None:
        """The same vacancy's ad on the employer's own career site (`Employer.ads`): the page its
        job sitemap names with the vacancy's number, when that page's job data has the job's
        title and a full ad. None when there is no such page."""
        # Imported here: the duplicate rules import the sources.
        from jobcu.dedupe import normal_title

        address, number = job.source_context.get("ads"), job.source_context.get("number")
        if not address or not number:
            return None
        named = re.compile(rf"(?<![a-z0-9]){re.escape(number.lower())}(?![0-9])")
        pages = [page for page in self._own_pages(address, ctx)
                 if named.search(urlsplit(page).path.lower())]
        pages.sort(key=lambda page: bool(_LANGUAGE_PATH.match(urlsplit(page).path)))
        for page in pages[:2]:
            try:
                if not self.allowed(page, ctx):
                    return None
                posting = find_job_posting(self.get(page, ctx).text)
            except (SourceError, BudgetExhausted, Blocked):
                return None
            if (posting is None or not (posting.description or "").strip()
                    or fuzz.token_set_ratio(normal_title(posting.title),
                                            normal_title(job.title)) < SAME_TITLE):
                continue
            posted, precision = job.posted_at, job.date_precision
            if posting.date_posted and (posted is None or posting.date_posted < posted):
                # An earlier date shows the job is older; a later one can be the page's update.
                posted = posting.date_posted
                precision = "exact" if posting.date_has_time else "day"
            return dataclasses.replace(
                job,
                description=posting.description,
                description_is_complete=posting.description_is_complete,
                location_text=posting.location_text or job.location_text,
                country=job.country or country_code(posting.country),
                posted_at=posted,
                date_precision=precision,
                job_types=posting.job_types or job.job_types,
                work_mode="remote" if posting.remote else job.work_mode,
                closes_at=posting.valid_through or job.closes_at,
            )
        return None

    def _own_pages(self, address: str, ctx: SourceContext) -> list[str]:
        """The job pages an employer's own sitemap lists, read once a search."""
        read: dict[str, list[str]] = self.__dict__.setdefault("_own_pages_read", {})
        if address not in read:
            try:
                read[address] = [page for page, _ in job_pages(self, address, ctx)]
            except (SourceError, BudgetExhausted, Blocked):
                read[address] = []
        return read[address]

    finds_by_title = True

    def find_by_title(self, employer: Employer, title: str, ctx: SourceContext
                      ) -> list[FoundJob]:
        """One page of the site's own search for the title (the list's `searchText`, the box on
        the career site). The country comes from the full ad's places (load_details)."""
        site = parse_board(employer.board)
        self._check_robots(site, ctx)
        today = datetime.now(UTC).date()
        data = self._page(site, {}, 0, ctx, search=title)
        return [to_found_job(item, site, employer, None, today)
                for item in data.get("jobPostings") or []
                if (item.get("title") or "").strip() and item.get("externalPath")]

    def _page(self, site: Site, facets: dict, offset: int, ctx: SourceContext,
              search: str = "") -> dict:
        body = {"appliedFacets": facets, "limit": PAGE_SIZE, "offset": offset,
                "searchText": search}
        return self.get_json(f"{site.api}/jobs", ctx, method="POST", json=body, headers=HEADERS)

    def _check_robots(self, site: Site, ctx: SourceContext) -> None:
        if not self.allowed(f"{site.api}/jobs", ctx):
            raise SourceError(f"{site.host} asks automated tools not to read its job list.")


def _all_facets(facets: list) -> Iterator[tuple[str, list[dict]]]:
    for facet in facets or []:
        values = facet.get("values") or []
        if values and isinstance(values[0], dict) and "facetParameter" in values[0]:
            yield from _all_facets(values)
        elif values:
            yield facet.get("facetParameter") or "", values


def _country_facet(facets: list) -> tuple[str, list[dict]]:
    """The site's filter that stands for countries, and its values.

    Career sites name it differently ("locationCountry", "locationHierarchy1" with country
    names, or "locations" with "Ireland, Limerick"), so Jobcu picks the location filter whose
    entries name a country most clearly, preferring the one with the fewest entries (the
    country level rather than every office).
    """
    best: tuple[float, int, str, list[dict]] | None = None
    for parameter, values in _all_facets(facets):
        if "location" not in parameter.lower() and "country" not in parameter.lower():
            continue
        named = sum(1 for value in values if len(countries_in(value.get("descriptor"))) == 1)
        share = named / len(values)
        if share < 0.6:
            continue
        rank = (-share, len(values), 0 if "country" in parameter.lower() else 1)
        if best is None or rank < best[0]:
            best = (rank, parameter, values)
    if best is None:
        return "", []
    return best[1], best[2]


def country_facets(data: dict) -> dict[str, set[str]]:
    """The country filter's IDs and the supported countries they stand for."""
    return {value["id"]: {c for c in countries_in(value.get("descriptor")) if c != OTHER}
            for value in _country_facet(data.get("facets"))[1] if value.get("id")}


def vacancy_number(item: dict) -> str | None:
    """The vacancy number a Workday list shows (its first "bulletField" on the sites checked),
    else the one its address ends with ("..._R5045614-2", the vacancy's second posting)."""
    for value in item.get("bulletFields") or []:
        if isinstance(value, str) and _NUMBER.match(value.strip()):
            return value.strip()
    tail = re.sub(r"-\d{1,2}$", "", (item.get("externalPath") or "").rsplit("_", 1)[-1])
    return tail if _NUMBER.match(tail) else None


def to_found_job(item: dict, site: Site, employer: Employer, country: str | None,
                 today: date) -> FoundJob:
    path = item.get("externalPath") or ""
    day = posted_day(item.get("postedOn"), today)
    location = item.get("locationsText")
    if location and re.fullmatch(r"\d+ Locations?", location):
        location = None  # "5 Locations": the country filter tells the country
    number = vacancy_number(item) if employer.ads else None
    return FoundJob(
        source="workday",
        source_job_id=f"{site.api}{path}",
        url=f"https://{site.host}/{site.site}{path}",
        title=(item.get("title") or "").strip(),
        company=employer.name,
        location_text=location,
        country=country,
        posted_at=day_at_utc(day) if day else None,
        date_precision="day" if day else "unknown",
        work_mode=work_mode_from_text(location),
        # Where the ad can be read when Workday won't serve it (_from_own_site).
        source_context={"number": number, "ads": employer.ads} if number else {},
    )
