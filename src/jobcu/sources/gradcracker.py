"""Gradcracker (gradcracker.com): graduate jobs in engineering and technology in the UK, checked
2026-11-25.

There's no feed. The board lists its jobs per discipline and area, one list per kind:
`/search/electronic-electrical/electronic-electrical-graduate-jobs` (then `?page=2` and on), 80
jobs a page as cards (`<article data-search-result="{number}">`) with the title, the job's page
(`/hub/{employer}/{name}/graduate-job/{number}/{title}`), the employer, the place, salary,
deadline and start. Its sitemap names every list. A job's page has the full ad
(`div.body-content`) and the same facts (`div[data-type=overview]`). robots.txt allows these pages
(it closes the keyword search, outgoing links and downloads).

Pages give no posting date, only a deadline. So a search reads whole the graduate lists of the
areas its search words name ("Power Electronics Engineer" names "electronic-electrical"; a nurse's
words name none, so nothing is read there), and a job is dated by its first sight on them
(`listmemory`): from the second search a day apart, a job new on a list counts as posted that day,
and only such jobs are passed on, so "Posted within" stays exact and a list's first reading adds
no undated jobs. A job's page is opened only for a job still in the running (`load_details`).

Its legal page doesn't allow scraping (it allows copies "for reading or browsing" and for personal
use), so it is read only for a person who switches it on in Settings (sources.TERMS_NOTES). No
legal action by Gradcracker against readers was found (2026-11-25). A search reads the lists of
the areas named, never the board.
"""

import dataclasses
import re
from collections.abc import Iterator
from datetime import UTC, datetime

import httpx
from lxml import html as lxml_html
from lxml.etree import ParserError

from jobcu import listmemory
from jobcu.freshness import freshness, window_start
from jobcu.placenames import OTHER, countries_in
from jobcu.sources.base import FoundJob, JobQuery, JobSource, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted, Limits, RequestBudget
from jobcu.sources.http import Blocked, RobotsRules
from jobcu.sources.matching import matches_places, matches_terms
from jobcu.text import html_to_text, normalise, tidy

SITE = "https://www.gradcracker.com"
PAGE_SIZE = 80
# Pages of one list in a search: the electronic and electrical graduate list had 7 (2026-11-25).
MAX_PAGES = 12
# Lists read in a search: the areas the search words name best.
MAX_LISTS = 4
LIMITS = Limits(per_search=60)
# A graduate list of an area: "/search/{discipline}/{area}-graduate-jobs", without the lists of
# one town ("-in-bristol") or of jobs abroad ("-rest-of-the-world").
_LIST = re.compile(rf"^{re.escape(SITE)}/search/([a-z-]+)/([a-z-]+?)-graduate-jobs$")
# Words of a job title that name no field: "Graduate Electronics Engineer" names electronics.
_NO_FIELD = frozenset({
    "and", "of", "the", "for", "in", "with", "to", "a", "an", "or", "jobs", "job",
    "engineer", "engineers", "engineering", "graduate", "graduates", "junior", "senior", "lead",
    "principal", "trainee", "intern", "internship", "manager", "specialist", "technician",
    "assistant", "officer", "design", "designer", "development", "developer", "programme",
    "program", "scheme", "entry", "level", "early", "career", "careers", "staff", "associate"})
_DEADLINE = re.compile(r"([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})")


class GradcrackerSource(JobSource):
    id = "gradcracker"
    name = "Gradcracker"
    kind = "job_board"
    # Its lists are the UK's, with a few jobs in Ireland among them.
    countries = frozenset({"GB", "IE"})
    # A list gives the place; the job's page has the full ad.
    details_supply_locations = True

    def search(self, query: JobQuery, ctx: SourceContext) -> Iterator[FoundJob]:
        self._budget = RequestBudget(self.id, self.name, LIMITS)
        start = window_start(query.started_at, query.posted_within_hours)
        try:
            robots = self._robots(ctx)
            lists = chosen_lists(self._lists(ctx), query)
            if not lists:
                return
            first_sights: dict[str, listmemory.Sight] = {}
            cards: dict[str, FoundJob] = {}
            for address in lists:
                if ctx.should_stop():
                    return
                if not robots.allows(address):
                    continue
                listed = self._read_list(address, ctx)
                for job_id, sight in listmemory.note(self.id, address, list(listed),
                                                     now=query.started_at).items():
                    known = first_sights.get(job_id)
                    if known is None or sight.first_seen_at < known.first_seen_at:
                        first_sights[job_id] = sight
                cards.update(listed)
        except BudgetExhausted as exc:
            ctx.report.status, ctx.report.message = "partial", exc.message
            return
        languages = {"en"}
        for job_id, job in cards.items():
            posted, precision = listmemory.posted(first_sights.get(job_id), start)
            # Only a job its first sight proves new: the lists give no dates, and every open
            # job each search would be hundreds, nearly all old.
            if precision != "day" or freshness(posted, precision, start) != "fresh":
                continue
            if job.country not in query.countries or not matches_places(
                    query.places, job.country, job.location_text):
                continue
            yield dataclasses.replace(
                job, posted_at=posted, date_precision=precision,
                title_unmatched=not matches_terms(query.terms, languages, job.title))

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        try:
            response = ctx.http.get(job.url)
        except (httpx.HTTPError, Blocked):
            return job
        if response.status_code != 200:
            return job
        page = read_job_page(response.text)
        if not page.get("description"):
            return job
        return dataclasses.replace(
            job,
            description=page["description"],
            description_is_complete=True,
            location_text=page.get("Location") or job.location_text,
            salary_text=page.get("Salary") or job.salary_text,
            closes_at=deadline(page.get("Deadline")) or job.closes_at,
        )

    def _robots(self, ctx: SourceContext) -> RobotsRules:
        try:
            response = ctx.http.get(f"{SITE}/robots.txt", blocks_host=False)
        except (httpx.HTTPError, Blocked):
            return RobotsRules(disallow_all=True)
        if response.status_code == 200:
            return RobotsRules(response.text)
        return RobotsRules(allow_all=400 <= response.status_code < 500)

    def _lists(self, ctx: SourceContext) -> list[str]:
        """Every graduate list of an area that the sitemap names."""
        text = self._get(f"{SITE}/sitemap.xml", ctx)
        return [address for address in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
                if _LIST.match(address)]

    def _read_list(self, address: str, ctx: SourceContext) -> dict[str, FoundJob]:
        """One list, all its pages: each job's number and what its card says."""
        jobs: dict[str, FoundJob] = {}
        for page in range(1, MAX_PAGES + 1):
            cards = parse_cards(self._get(address + (f"?page={page}" if page > 1 else ""), ctx))
            new = {job.source_job_id: job for job in cards if job.source_job_id not in jobs}
            jobs.update(new)
            if len(cards) < PAGE_SIZE or not new:
                break
        return jobs

    def _get(self, address: str, ctx: SourceContext) -> str:
        self._budget.spend()
        ctx.report.requests += 1
        try:
            response = ctx.http.get(address)
        except httpx.HTTPError as exc:
            raise SourceError("Gradcracker couldn't be reached.") from exc
        if response.status_code == 429:
            raise BudgetExhausted("Gradcracker: asked Jobcu to slow down for now.")
        if response.status_code != 200:
            raise SourceError(f"Gradcracker answered with a problem (code {response.status_code}).")
        return response.text


def field_words(text: str) -> set[str]:
    """The words of a title or an area that name a field, each also without a plural "s"."""
    words = set(normalise(text).replace("-", " ").split()) - _NO_FIELD
    return words | {word[:-1] for word in words if len(word) > 4 and word.endswith("s")}


def chosen_lists(addresses: list[str], query: JobQuery) -> list[str]:
    """The graduate lists of the areas the English search words name, those named by the most
    words first, at most MAX_LISTS."""
    wanted = set().union(*(field_words(term.text) for term in query.terms
                           if term.language == "en")) if query.terms else set()
    scored = []
    for address in dict.fromkeys(addresses):
        area = _LIST.match(address).group(2)
        if hits := len(field_words(area) & wanted):
            scored.append((-hits, address))
    return [address for _, address in sorted(scored)[:MAX_LISTS]]


def parse_cards(markup: str) -> list[FoundJob]:
    """The jobs a list page shows, each as its card says."""
    try:
        doc = lxml_html.document_fromstring(markup or "<html></html>")
    except (ParserError, ValueError):
        return []
    jobs = []
    for card in doc.xpath("//article[@data-search-result]"):
        links = card.xpath(".//h2//a[@href]")
        if not links:
            continue
        facts = {tidy(row.xpath("string(dt)")): tidy(row.xpath("string(dd)"))
                 for row in card.xpath(".//dl/div")}
        employer = card.xpath(".//figure//img/@alt")
        location = facts.get("Location") or None
        jobs.append(FoundJob(
            source=GradcrackerSource.id,
            source_job_id=card.get("data-search-result"),
            url=links[0].get("href"),
            title=tidy(links[0].text_content()),
            company=tidy(employer[0]) if employer else None,
            location_text=location,
            country=country_of(location),
            salary_text=facts.get("Salary") or None,
            closes_at=deadline(facts.get("Deadline")),
        ))
    return jobs


def country_of(location: str | None) -> str:
    """A UK list's job is in the UK unless its place names another country ("Geneva
    (Switzerland)", a CERN post on the electronic and electrical list)."""
    named = countries_in(location) - {OTHER} if location else set()
    if not named or "GB" in named:
        return "GB"
    return sorted(named)[0] if len(named) == 1 else OTHER


def deadline(text: str | None) -> datetime | None:
    """"November 29th, 2026" as the end of that day; "Ongoing" is none."""
    match = _DEADLINE.search(text or "")
    if not match:
        return None
    try:
        day = datetime.strptime(" ".join(match.groups()), "%B %d %Y")
    except ValueError:
        return None
    return day.replace(hour=23, minute=59, tzinfo=UTC)


def read_job_page(markup: str) -> dict[str, str]:
    """A job page's facts ("Deadline", "Salary", "Location", ...) and its ad ("description")."""
    try:
        doc = lxml_html.document_fromstring(markup or "<html></html>")
    except (ParserError, ValueError):
        return {}
    facts = {}
    for item in doc.xpath("//div[@data-type='overview']//li"):
        label = item.xpath("string(./div[1])")
        value = tidy(item.text_content())[len(tidy(label)):].strip()
        if tidy(label) and value:
            facts[tidy(label)] = value
    body = doc.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' body-content ')]")
    if body:
        facts["description"] = html_to_text(lxml_html.tostring(body[0], encoding="unicode"))
    return facts
