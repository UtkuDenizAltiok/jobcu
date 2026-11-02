"""FreeHire: a free, open-source catalogue of job ads read from employers' own career systems
(Workday, SuccessFactors, Softgarden, SmartRecruiters, JOIN, Personio, rexx, coveto and about 200
more) and from some job boards, with a public search API that needs no key. Checked 2026-11-02.

- `GET /api/v1/agent/jobs/search` answers a word search with every ad's full text. Up to five
  alternatives fit in one request ("A OR B"); `title:` looks at the title only.
- Its terms (28 October 2026) allow the API without a plan for "your own job search ... or a tool
  you run for yourself"; robots.txt allows /api/ and asks robots to use it rather than the pages.
  It allows 120 requests a minute (its X-RateLimit headers).
- Dates: `posted_at` is the date the ad's source states, which some boards restate on every visit;
  `created_at` is when FreeHire first saw the ad, which nobody can restate. A job counts from the
  earlier of the two, so an old vacancy with a fresh date stays old, and an ad FreeHire itself
  marks as refreshed is left out. FreeHire lists ads up to about two days after their date (81
  ads on 2026-11-02: half within 7.5 hours, the latest after 42), so Jobcu asks for what it first
  saw within the window plus that lag.
- Copies FreeHire took from other job boards (Adzuna, Reed, EURES, XING, ...) carry that board's
  link and maybe only part of the ad. FreeHire's facets say which of its sources are employers'
  own systems; only their copies count as the complete ad on the employer's own page.

On 2026-11-02 a hardware engineering search's titles found 34 FreeHire ads in two days that
Jobcu had searched; 22 had reached Jobcu through no other source, about a third of them relevant.
"""

import html
import logging
import re
from collections.abc import Iterator
from datetime import datetime

import httpx

from jobcu.countries import COUNTRIES
from jobcu.freshness import (
    days_back,
    earliest_possible,
    freshness,
    parse_closing,
    parse_iso,
    window_start,
)
from jobcu.keywords import SearchTerm
from jobcu.placenames import OTHER, countries_in
from jobcu.sources.base import (
    DatePrecision,
    FoundJob,
    JobQuery,
    JobSource,
    SourceContext,
    SourceError,
)
from jobcu.sources.budget import BudgetExhausted, Limits, RequestBudget
from jobcu.sources.matching import broadest_titles, matches_places
from jobcu.text import html_to_text, normalise

log = logging.getLogger(__name__)

API = "https://freehire.me/api/v1"
PAGE_SIZE = 50
ALTERNATIVES = 5  # FreeHire refuses more "OR" alternatives in one search
MAX_RESULTS = 10_000  # it refuses pages beyond this
LAG_HOURS = 48
# A search asks once for each group of titles and field words, so this is ample; the cap keeps a
# long window's broad words from reading thousands of ads.
LIMITS = Limits(per_search=80)
_WORK_MODES = {"remote": "remote", "hybrid": "hybrid", "onsite": "on_site"}
# Some career systems give their own address instead of the employer's name
# ("jobs.example-group.com"): that names no company.
_HOST_NAME = re.compile(r"(?:[\w-]+\.)+[a-z]{2,}", re.IGNORECASE)
_GENDER = re.compile(r"\((?:[mwdfxi]\s*/\s*){1,3}[mwdfxi]\)", re.IGNORECASE)


class FreeHireSource(JobSource):
    id = "freehire"
    name = "FreeHire"
    kind = "aggregator"
    date_lag_hours = LAG_HOURS

    def search(self, query: JobQuery, ctx: SourceContext) -> Iterator[FoundJob]:
        searches = plan_searches(query.terms, query.countries)
        if not searches:
            return
        budget = RequestBudget(self.id, self.name, LIMITS)
        # Ads listed late still count while Jobcu never showed them (filters.py); older ones
        # only show that a copy found fresh elsewhere is a repost.
        start = window_start(query.started_at, query.posted_within_hours + LAG_HOURS)
        seen: set[str] = set()
        try:
            originals = self._original_sources(budget, ctx)
            for number, search in enumerate(searches):
                if ctx.should_stop():
                    return
                # A fair part of what is left, so one broad word can't use up the rest.
                left = (LIMITS.per_search or 0) - budget.used_this_search
                pages = max(1, left // (len(searches) - number))
                for job in self._run(search, query, budget, ctx, pages, originals):
                    if job.source_job_id in seen:
                        continue
                    seen.add(job.source_job_id)
                    if not matches_places(query.places, job.country, job.location_text):
                        continue
                    job.older_copy = freshness(
                        job.posted_at, job.date_precision, start) == "too_old"
                    yield job
        except BudgetExhausted as exc:
            ctx.report.status = "partial"
            ctx.report.message = exc.message

    def _run(self, search: dict, query: JobQuery, budget: RequestBudget, ctx: SourceContext,
             pages: int, originals: frozenset[str]) -> Iterator[FoundJob]:
        days = days_back(query.posted_within_hours + LAG_HOURS)
        for page in range(pages):
            if ctx.should_stop():
                return
            offset = page * PAGE_SIZE
            if offset + PAGE_SIZE > MAX_RESULTS:
                return
            params = {**search, "countries": [code.lower() for code in query.countries],
                      "open_within_days": days, "limit": PAGE_SIZE, "offset": offset}
            body = self._get("/agent/jobs/search", params, budget, ctx)
            items = body.get("data")
            if not isinstance(items, list):
                raise SourceError("FreeHire didn't answer with a job list.")
            for item in items:
                if isinstance(item, dict) and (
                        job := to_found_job(item, query.countries, originals)):
                    yield job
            total = (body.get("meta") or {}).get("total")
            if len(items) < PAGE_SIZE or (isinstance(total, int) and offset + PAGE_SIZE >= total):
                return

    def _original_sources(self, budget: RequestBudget, ctx: SourceContext) -> frozenset[str]:
        """The sources FreeHire reads from employers' own systems. Without this answer every ad
        counts as a job board's copy: found all the same, only not trusted as complete."""
        try:
            body = self._get("/jobs/facets", {"source_type": ["ats", "company"]}, budget, ctx)
            names = ((body.get("data") or {}).get("facets") or {}).get("source") or {}
        except SourceError as exc:
            log.warning("FreeHire's source list wasn't read: %s", exc)
            return frozenset()
        return frozenset(name for name in names if isinstance(name, str))

    def _get(self, path: str, params: dict, budget: RequestBudget, ctx: SourceContext) -> dict:
        budget.spend()
        ctx.report.requests += 1
        try:
            response = ctx.http.get(API + path, params=params)
        except httpx.HTTPError as exc:
            raise SourceError("FreeHire couldn't be reached.") from exc
        if response.status_code == 429:
            raise BudgetExhausted("FreeHire asked Jobcu to slow down for now.")
        if response.status_code != 200:
            raise SourceError(f"FreeHire answered with a problem (code {response.status_code}).")
        try:
            body = response.json()
        except ValueError as exc:
            raise SourceError("FreeHire didn't answer with a job list.") from exc
        if not isinstance(body, dict):
            raise SourceError("FreeHire didn't answer with a job list.")
        return body


def plan_searches(terms: list[SearchTerm], countries: list[str]) -> list[dict]:
    """The FreeHire requests for one search: job titles in the title, most precise first, then
    field words in the title or ad text, five of each to a request."""
    languages = {"en"}
    for code in countries:
        if code in COUNTRIES:
            languages.update(COUNTRIES[code].ad_languages)
    relevant = [t for t in terms if t.language in languages]
    titles = broadest_titles([_phrase(t.text) for t in relevant if t.kind == "job_title"])
    first_spelling: dict[str, str] = {}
    for t in relevant:
        if t.kind == "field_or_skill" and normalise(text := _phrase(t.text)):
            first_spelling.setdefault(normalise(text), text)
    skills = list(first_spelling.values())
    searches = [{"q": " OR ".join(f'title:"{title}"' for title in titles[i:i + ALTERNATIVES])}
                for i in range(0, len(titles), ALTERNATIVES)]
    searches += [{"q": " OR ".join(f'"{skill}"' for skill in skills[i:i + ALTERNATIVES]),
                  "q_fields": "title,description"}
                 for i in range(0, len(skills), ALTERNATIVES)]
    return searches


def _phrase(text: str) -> str:
    """A search word as one quoted alternative, without FreeHire's own operators."""
    words = (word.lstrip("-") for word in re.sub(r'["()]|\bOR\b', " ", text).split())
    return " ".join(word for word in words if word)


def to_found_job(item: dict, searched: list[str], originals: frozenset[str]) -> FoundJob | None:
    identity = _text(item.get("public_slug"))
    title = html.unescape(_text(item.get("title")))
    url = _text(item.get("url"))
    if not identity or not title or not url.startswith(("https://", "http://")):
        return None
    reality = item.get("reality") if isinstance(item.get("reality"), dict) else {}
    if reality.get("fake_freshness") is True:
        return None  # FreeHire saw this vacancy before under its earlier date
    location = _text(item.get("location"))
    cities = [c for c in item.get("cities") or [] if isinstance(c, str) and c.strip()]
    location = location or ", ".join(cities)
    country = _country(location, item.get("countries"), searched)
    if country is None:
        return None
    posted, precision = _first_date(item)
    source = _text(item.get("source"))
    original = source in originals
    if source == "eures" and country == "DE":
        title = _without_occupation(title)
    company = html.unescape(_text(item.get("company")))
    return FoundJob(
        source="freehire",
        source_job_id=identity,
        url=url,
        title=title,
        company=None if not company or _HOST_NAME.fullmatch(company) else company,
        location_text=location or None,
        country=country,
        posted_at=posted,
        date_precision=precision,
        description=html_to_text(_text(item.get("description"))),
        description_is_complete=original and bool(_text(item.get("description"))),
        work_mode=_WORK_MODES.get(_text(item.get("work_mode"))),
        employer_url=url if original else None,
        closes_at=parse_closing(_text(item.get("application_deadline"))),
    )


def _without_occupation(title: str) -> str:
    """EURES adds the Bundesagentur's occupation to German titles ("Senior Engineer (m/w/d)
    (Ingenieur/in - Elektrotechnik)", all 100 of a day's sample on 2026-11-02). It isn't the
    employer's title, and kept, the copy never matched the agency's own ad: two cards for one
    job. A gender marker at the end is the title's own and stays."""
    if not title.endswith(")"):
        return title
    depth = 0
    for position in range(len(title) - 1, -1, -1):
        if title[position] == ")":
            depth += 1
        elif title[position] == "(":
            depth -= 1
            if depth == 0:
                if _GENDER.fullmatch(title[position:]):
                    return title
                return title[:position].rstrip() or title
    return title


def _first_date(item: dict) -> tuple[datetime | None, DatePrecision]:
    """The earlier of the date the ad states and the moment FreeHire first saw it."""
    stamp = _text(item.get("posted_at"))
    stated = parse_iso(stamp)
    if stated is None:
        # FreeHire's first sight alone can't date an ad that it found long after its posting.
        return None, "unknown"
    precision: DatePrecision = (
        "day" if len(stamp) == 10 or stated.hour == stated.minute == stated.second == 0
        else "exact")
    seen = parse_iso(_text(item.get("created_at")))
    if seen is not None and seen < earliest_possible(stated, precision):
        return seen, "exact"
    return stated, precision


def _country(location: str, listed, searched: list[str]) -> str | None:
    """The searched country the ad names in its place, else the one FreeHire lists for it."""
    named = countries_in(location) - {OTHER}
    codes = {c.upper() for c in listed if isinstance(c, str)} if isinstance(listed, list) else set()
    return (next((code for code in searched if code in named), None)
            or next((code for code in searched if code in codes), None))


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""
