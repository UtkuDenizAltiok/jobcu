"""Jibe career sites (Schneider Electric, AMD), checked 2026-11-24.

A Jibe career site (`careers.se.com`) answers its own job search at `GET https://{host}/api/jobs`
with `location` (a country's name), `page`, `limit` (up to 100), `sortBy=posted_date` and
`descending=true`: the newest jobs first, each with its title, places, posting day, employment type
and the full ad (`description`, `qualifications`, `responsibilities`), and how many jobs match
(`totalCount`). A job's page is `https://{host}/jobs/{slug}`. Their robots.txt closes nothing of
this; the sitemap's job addresses carry no titles or dates, so it isn't used. The application form
is on another system (Schneider's and AMD's on iCIMS hosts whose robots.txt closes them): never
visited during a search.

A search reads each searched country's list newest first and stops at the first page of jobs
older than the window, like Workday lists, so nothing else is opened.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from urllib.parse import quote

from jobcu.countries import COUNTRIES
from jobcu.freshness import day_at_utc, freshness, parse_iso
from jobcu.jobposting import append_sections
from jobcu.placenames import countries_in
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.careers import (
    CareerSystemSource,
    Employer,
    Survey,
    job_types_from_text,
    work_mode_from_text,
)
from jobcu.text import html_to_text

PAGE_SIZE = 100
# Pages of one country's list in a search: newest first, so one or two cover a few days.
MAX_PAGES_PER_COUNTRY = 10
HEADERS = {"Accept": "application/json"}


class JibeSource(CareerSystemSource):
    id = "jibe"
    name = "Company career sites (Jibe)"
    system = "jibe"
    parallel = 4  # every employer has its own host

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        seen: set[str] = set()
        for code in countries if countries is not None else sorted(employer.countries):
            for page in range(1, MAX_PAGES_PER_COUNTRY + 1):
                answer = self._page(employer.board, code, page, ctx)
                items = [item.get("data") or item for item in answer.get("jobs") or []]
                too_old = 0
                for item in items:
                    job = to_found_job(item, employer, code)
                    if job is None:
                        continue
                    if start and freshness(job.posted_at, job.date_precision, start) == "too_old":
                        too_old += 1
                    if job.source_job_id not in seen:
                        seen.add(job.source_job_id)
                        yield job
                # Newest first: a page of only older jobs means the rest is older too.
                if (len(items) < PAGE_SIZE or (start and too_old == len(items))
                        or page * PAGE_SIZE >= int(answer.get("totalCount") or 0)):
                    break

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        """How many jobs each supported country's list has (one small request each)."""
        survey = Survey()
        for code in COUNTRIES:
            answer = self._page(employer.board, code, 1, ctx, limit=1)
            if count := int(answer.get("totalCount") or 0):
                survey.counts[code] += count
        return survey

    def _page(self, host: str, code: str, page: int, ctx: SourceContext,
              limit: int = PAGE_SIZE) -> dict:
        address = (f"https://{host}/api/jobs?location={quote(COUNTRIES[code].name)}&page={page}"
                   f"&limit={limit}&sortBy=posted_date&descending=true")
        if not self.allowed(address, ctx):
            raise SourceError(f"{host} asks automated tools not to read its job list.")
        answer = self.get_json(address, ctx, headers=HEADERS)
        if not isinstance(answer, dict):
            raise SourceError(f"{self.name} didn't answer with a job list.")
        return answer


def posted(item: dict) -> tuple[datetime | None, str]:
    """The posting day: "November 23, 2026" (Schneider) or "2026-11-20T16:15:00+0000" (AMD)."""
    text = str(item.get("posted_date") or "").strip()
    try:
        return day_at_utc(datetime.strptime(text, "%B %d, %Y").date()), "day"
    except ValueError:
        pass
    when = parse_iso(text.replace("+0000", "+00:00")) if text else None
    return (when.astimezone(UTC), "exact") if when else (None, "unknown")


def to_found_job(item: dict, employer: Employer, code: str) -> FoundJob | None:
    slug, title = str(item.get("slug") or item.get("req_id") or "").strip(), (
        item.get("title") or "").strip()
    if not slug or not title:
        return None
    place = (item.get("full_location") or item.get("short_location") or ", ".join(
        part for part in (item.get("city"), item.get("state"), item.get("country")) if part))
    own = str(item.get("country_code") or "").upper()
    # A job in several countries is on each one's list: the searched one is its country when
    # its places name it.
    country = code if own == code or code in countries_in(place) else (
        own if own in COUNTRIES else None)
    day, precision = posted(item)
    description = append_sections(html_to_text(item.get("description") or ""), [
        ("Responsibilities", [html_to_text(item.get("responsibilities") or "")]),
        ("Qualifications", [html_to_text(item.get("qualifications") or "")])])
    url = f"https://{employer.board}/jobs/{quote(slug)}"
    return FoundJob(
        source=JibeSource.id,
        source_job_id=url,
        url=url,
        title=title,
        company=employer.name,
        location_text=place or None,
        country=country,
        posted_at=day,
        date_precision=precision,
        description=description,
        description_is_complete=bool(description.strip()),
        job_types=job_types_from_text(str(item.get("employment_type") or "").replace("_", " ")),
        work_mode=work_mode_from_text(str(item.get("location_type") or "")),
        employer_url=url,
    )
