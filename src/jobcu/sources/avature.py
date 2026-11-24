"""Avature career sites (Siemens, Siemens Energy), checked 2026-11-24.

An Avature site lists its jobs on ordinary pages, a few at a time
(`...?jobRecordsPerPage=..&jobOffset=..`): each item links to the job's own page
(`.../JobDetail/530405` or `.../FolderDetail/{title}/299670`) under its title, and some sites add
the place. Sites list a country in their own way: Siemens filters one list by a country option
(`?42386[]=812132`), Siemens Energy has a page per country (`SearchJobsGermany`). The directory
therefore gives the list's address for each country (`Employer.lists`), and the board is the site
and portal ("jobs.siemens.com/en_US/externaljobs"). Their robots.txt allows these pages; their
sitemaps list only the site's own pages.

A job's page has the posting day ("Posted since 23-Nov-2026"), the places ("Planegg - - Germany"),
the job type, the work mode and the ad as Avature's label and value fields, and some sites add the
standard job data (JobPosting). The lists give no dates, so a search reads each searched country's
list whole, notes when each job is first seen (`listmemory`), opens the pages of the titles that
match the search words (at most PAGES_PER_LIST a list, new ones first; a page read once is
remembered) and gives the titles they miss to the person's AI only when they are new since the
list's last reading, like SuccessFactors sites.

Siemens' terms of use don't allow automated reading ("text or data mining"), so the source is read
only for a person who switches it on in Settings, accepting that (sources.TERMS_NOTES).
"""

import dataclasses
import html
import re
from collections.abc import Iterator
from datetime import datetime
from urllib.parse import parse_qsl, urlsplit

from lxml import html as lxml_html
from lxml.etree import ParserError

from jobcu import listmemory
from jobcu import places as place_list
from jobcu.countries import COUNTRIES
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
from jobcu.sources.matching import matches_terms
from jobcu.text import html_to_text

# Pages of one country's list read in a search: Siemens shows six jobs a page and listed 382 in
# Germany (2026-11-24), Siemens Energy twenty a page.
MAX_LIST_PAGES = 100
# Job pages opened from one country's list in a search, jobs new on the list first. A page read
# once is remembered, so a first search opens the rest over the next ones.
PAGES_PER_LIST = 30

_ITEM = re.compile(r'<article[^>]*class="[^"]*article--result[^"]*"[^>]*>(.*?)</article>', re.S)
_LINK = re.compile(r'href="(https?://[^"]+/(?:JobDetail|FolderDetail)/(?:[^"/?]+/)?(\d+))"')
_TITLE = re.compile(r"<h3[^>]*>\s*<a[^>]*>(.*?)</a>", re.S)
_SUBTITLE = re.compile(r'class="[^"]*article__header__text__subtitle[^"]*"[^>]*>(.*?)</div>', re.S)
_TOTAL = re.compile(r"(\d[\d,.]*)\s*results\b", re.I)
_DATE_FORMATS = ("%d-%b-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y")


class AvatureSource(CareerSystemSource):
    id = "avature"
    name = "Company career sites (Avature)"
    system = "avature"
    parallel = 2  # every employer has its own host

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        wanted = [code for code in (countries or employer.lists) if code in employer.lists]
        for code in wanted:
            listed = self._list(employer, code, ctx)
            if terms is None:
                yield from listed  # the directory check: titles and places, no pages opened
                continue
            languages = {"en", *COUNTRIES[code].ad_languages}
            sights = listmemory.note(self.id, f"{employer.board}#{code}",
                                     [job.source_job_id for job in listed])
            matched, new_unmatched = [], []
            for job in listed:
                posted, precision = listmemory.posted(sights.get(job.source_job_id), start)
                job = dataclasses.replace(job, posted_at=posted, date_precision=precision)
                if matches_terms(terms, languages, job.title):
                    matched.append(job)
                elif precision == "day" and (
                        start is None or freshness(posted, precision, start) == "fresh"):
                    # Titles the search words miss go to the person's AI, only when new on the
                    # list: every open job's title each search would be hundreds, nearly all old.
                    new_unmatched.append(job)
            # Jobs new on the list first, then the rest in the list's order.
            matched.sort(key=lambda job: job.date_precision != "day")
            opened = 0
            for job in matched:
                known = self._remembered(job)
                if known is None:
                    if opened >= PAGES_PER_LIST:
                        continue
                    opened += 1
                    known = self._from_page(job, ctx)
                if known is not None:
                    yield known
            yield from new_unmatched

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        """How many jobs each country's list says it has, and the towns its first page names."""
        survey = Survey()
        for code, address in employer.lists.items():
            if not self.allowed(address, ctx):
                raise SourceError(f"{urlsplit(address).hostname} asks automated tools not to "
                                  "read its job list.")
            page = self._page_text(address, ctx)
            listed = items(page, employer, code)
            total = _TOTAL.search(page)
            count = int(re.sub(r"[,.]", "", total.group(1))) if total else len(listed)
            if not count or (count <= len(listed) and all(job.country is None for job in listed)):
                continue  # nothing there, or only jobs "in multiple locations" on every list
            survey.counts[code] += count
            for job in listed:
                town = place_list.locate(job.location_text, code) if job.location_text else None
                if town is not None:
                    survey.towns.setdefault(code, set()).add(town.name)
        return survey

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        """A job listed by its title only (one the search words missed): its page's places, ad
        and day. Where the page gives no day, its first sight on the list stands."""
        return self._from_page(job, ctx) or job

    def _list(self, employer: Employer, code: str, ctx: SourceContext) -> list[FoundJob]:
        """One country's whole list, page by page, as the site shows it."""
        address = employer.lists[code]
        if not self.allowed(address, ctx):
            raise SourceError(f"{urlsplit(address).hostname} asks automated tools not to read "
                              "its job list.")
        listed: dict[str, FoundJob] = {}
        url, read = address, set()
        for _ in range(MAX_LIST_PAGES):
            read.add(url)
            page = self.get(url, ctx).text
            new = [job for job in items(page, employer, code) if job.source_job_id not in listed]
            listed.update((job.source_job_id, job) for job in new)
            url = next_page(page, url)
            if not new or url is None or url in read:
                break
        return list(listed.values())

    def _page_text(self, address: str, ctx: SourceContext) -> str:
        return self.get(address, ctx).text

    def _remembered(self, job: FoundJob) -> FoundJob | None:
        # Imported here: the job memory itself imports the sources (through dedupe).
        from jobcu import jobstore

        known = jobstore.remembered_ad(job, reader_version=self.detail_cache_version)
        if known is None or not known.description_is_complete:
            return None
        if known.posted_at is None:
            known = dataclasses.replace(known, posted_at=job.posted_at,
                                        date_precision=job.date_precision)
        return dataclasses.replace(known, title_unmatched=False, older_copy=False)

    def _from_page(self, job: FoundJob, ctx: SourceContext) -> FoundJob | None:
        """The job with its page's places, ad and day; None if the page can't be read."""
        from jobcu import jobstore

        if not self.allowed(job.url, ctx):
            return None
        try:
            page = self.get(job.url, ctx, cache=False).text
        except (SourceError, BudgetExhausted):
            return None
        found = read_page(page)
        if not found.description:
            return None
        full = dataclasses.replace(
            job,
            description=found.description,
            description_is_complete=True,
            location_text=found.places or job.location_text,
            posted_at=day_at_utc(found.posted.date()) if found.posted else job.posted_at,
            date_precision="day" if found.posted else job.date_precision,
            job_types=found.job_types or job.job_types,
            work_mode=found.work_mode or job.work_mode,
            closes_at=found.closes or job.closes_at,
        )
        jobstore.remember_ad(full, reader_version=self.detail_cache_version)
        return full


def items(page: str, employer: Employer, country: str) -> list[FoundJob]:
    """The jobs one list page shows: address, title and, where the site shows it, the place."""
    jobs = []
    for item in _ITEM.findall(page):
        link, title = _LINK.search(item), _TITLE.search(item)
        if link is None or title is None or not html_to_text(title.group(1)).strip():
            continue
        place, code = None, country
        if subtitle := _SUBTITLE.search(item):
            # "Planegg , Bavaria , Germany • Job ID: 530405 • Sales": the place comes first.
            text = html.unescape(html_to_text(subtitle.group(1))).split("•")[0]
            text = re.sub(r"\s*,\s*", ", ", re.sub(r"\s+", " ", text)).strip(" ,")
            if re.search(r"\bmultiple locations\b", text, re.I):
                # Such a job is on every country's list (Siemens' Iceland list had four, in
                # Brazil and Japan): its page's places tell its country.
                code = None
            elif text and not re.search(r"\bjob id\b", text, re.I):
                place = text
        url = link.group(1).replace("&amp;", "&")
        jobs.append(FoundJob(
            source=AvatureSource.id, source_job_id=url, url=url,
            title=html.unescape(html_to_text(title.group(1))).strip(), company=employer.name,
            location_text=place, country=code, employer_url=url,
        ))
    return jobs



_PAGE_LINK = re.compile(r'href="([^"]*[?&](?:amp;)?(?:job|folder)Offset=(\d+)[^"]*)"')


def next_page(page: str, current: str) -> str | None:
    """The address of the list's next page, as the page's own page links give it (Siemens names
    its offset `folderOffset`, Siemens Energy `jobOffset`); None after the last page."""
    here = urlsplit(current)
    offset = next((int(value) for key, value in parse_qsl(here.query)
                   if key in ("folderOffset", "jobOffset") and value.isdigit()), 0)
    later = []
    for link, value in _PAGE_LINK.findall(page):
        address = html.unescape(link)
        if urlsplit(address).path.rstrip("/") == here.path.rstrip("/") and int(value) > offset:
            later.append((int(value), address))
    return min(later)[1] if later else None


@dataclasses.dataclass
class AvaturePage:
    description: str = ""
    places: str | None = None
    posted: datetime | None = None
    job_types: list = dataclasses.field(default_factory=list)
    work_mode: str | None = None
    closes: datetime | None = None


def read_page(page: str) -> AvaturePage:
    """A job page's ad, places, day, job type and work mode, from Avature's label and value fields
    (an unlabelled field holds the ad) and the standard job data (JobPosting) where the site adds
    it: Siemens Energy's gives only the title and the posting day."""
    found = _fields(page)
    posting = find_job_posting(page)
    if posting is not None:
        found.description = found.description or (posting.description or "").strip()
        found.places = found.places or posting.location_text
        found.posted = found.posted or posting.date_posted
        found.job_types = found.job_types or posting.job_types
        found.work_mode = found.work_mode or ("remote" if posting.remote else None)
        found.closes = posting.valid_through
    found.places = found.places or _leading_place(found.description)
    return found


# Siemens Energy's ads begin with their place, country first: "Location", "Germany", "Bayern",
# "Erlangen", each on its own line, then the ad's first heading.
_PLACE_HEADING = re.compile(r"(?:locations?|standorte?)", re.IGNORECASE)


def _leading_place(ad: str) -> str | None:
    """The place an ad names in its first lines under a "Location" heading, town first
    ("Erlangen, Bayern, Germany"); None unless the line after the heading is a country."""
    lines = [line.strip() for line in (ad or "").splitlines() if line.strip()][:4]
    if len(lines) < 2 or not _PLACE_HEADING.fullmatch(lines[0]):
        return None
    if not countries_in(lines[1]) - {OTHER}:
        return None
    parts = [lines[1]]
    for line in lines[2:4]:  # region and town: short names, not the next heading or a sentence
        if len(line.split()) > 3 or line.endswith((".", ":", "?", "!")):
            break
        parts.append(line)
    return ", ".join(reversed(parts))


def _fields(page: str) -> AvaturePage:
    try:
        doc = lxml_html.fromstring(page)
    except (ParserError, ValueError):
        return AvaturePage()
    found = AvaturePage()
    ad, types = [], []
    for field in doc.xpath('//div[contains(concat(" ", normalize-space(@class), " "), '
                           '" article__content__view__field ")]'):
        label = " ".join(field.xpath('.//div[contains(@class, "field__label")]//text()')).strip()
        values = field.xpath('.//div[contains(@class, "field__value")]')
        if not values:
            continue
        value = values[0]
        text = " ".join(" ".join(value.itertext()).split())
        name = label.lower()
        if not label:
            ad.append(html_to_text(lxml_html.tostring(value, encoding="unicode")))
        elif re.match(r"posted|date posted|posting date|publi|veröffentlicht", name):
            found.posted = _day(text)
        elif re.search(r"location|standort|place", name):
            found.places = _places(value)
        elif re.search(r"work mode|remote|arbeitsmodell", name):
            found.work_mode = work_mode_from_text(text)
        elif re.search(r"job type|employment type|full / part time|contract|vertragsart", name):
            types.append(text)
    found.description = "\n\n".join(part.strip() for part in ad if part.strip())
    found.job_types = job_types_from_text(" ".join(types))
    return found


def _day(text: str) -> datetime | None:
    for form in _DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), form)
        except ValueError:
            continue
    return None


def _places(value) -> str | None:
    """"Planegg - - Germany" and "Stuttgart - Baden-Wuerttemberg - Germany", one a line, as
    "Planegg, Germany; Stuttgart, Baden-Wuerttemberg, Germany"."""
    lines = []
    for line in "\n".join(value.itertext()).splitlines():
        # A dash between spaces separates the parts; one inside a name ("Baden-Wuerttemberg")
        # doesn't.
        parts = [part.strip() for part in re.split(r"\s+-\s*|\s*-\s+", line) if part.strip()]
        if parts:
            lines.append(", ".join(parts))
    return "; ".join(dict.fromkeys(lines)) or None

