"""Job sitemaps: recruiters' and employers' own sites that list every job page for search engines
(sitemaps.org), each page carrying the standard job data (schema.org JobPosting), checked
2026-10-03 (SOURCES.md, "Job sitemaps with JobPosting pages").

A board is the address of the site's job sitemap. Jobcu reads it (one request; a sitemap index
leads to its job sitemaps), keeps the job pages changed since the window began when the sitemap
gives dates, and opens only those whose address spells words matching the search words
("/jobs/27724/graduate-electronics-engineer"), newest first. Each page's JobPosting data gives
the title, the full ad, the exact posting date, the town and country, the company and the job
type. Pages are remembered for a few days (`jobstore`), so later searches don't open them again.
A job listed in several languages counts once, in the searched countries' ad language. Jobs new
on the list since its last reading whose address misses the search words go to the person's AI
by the title their address spells; a page is opened only for a title it keeps (`load_details`).

Only sites whose terms allow it are in the directory: a recruiter's own copy of an ad that Adzuna
shows as a 500-character summary gives the full ad for scoring (search 11: 204 of 349 cards were
Adzuna summaries, Redline Group's about 20 of them).
"""

import dataclasses
import gzip
import re
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from urllib.parse import unquote, urljoin, urlsplit

from jobcu import jobpage, listmemory
from jobcu import places as place_list
from jobcu.countries import ALPHA3, COUNTRIES, WORLD_CODES
from jobcu.freshness import freshness, parse_iso
from jobcu.jobposting import JobPosting, find_job_posting
from jobcu.placenames import OTHER, countries_in
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.budget import BudgetExhausted
from jobcu.sources.careers import CareerSystemSource, Employer, Survey, job_countries
from jobcu.sources.matching import matches_terms

# Job pages opened per site in one search, newest first: enough for every fresh match on the
# sites checked, and a cap when a site gives no dates.
MAX_PAGES = 60
# Pages looked at to tell which countries a site's jobs are in (the directory check).
SURVEY_PAGES = 20
# Job sitemaps a sitemap index may lead to: a Phenom career site splits a few thousand jobs over
# nine (careers.rtx.com, 2026-11-24).
MAX_SITEMAPS = 12

_URL = re.compile(r"<url>\s*<loc>\s*([^<\s]+)\s*</loc>(?:\s*<lastmod>\s*([^<\s]+)\s*</lastmod>)?",
                  re.S)
_INDEX = re.compile(r"<sitemap>\s*<loc>\s*([^<\s]+)\s*</loc>", re.S)
_JOB_WORDS = re.compile(r"job|stelle|vacanc|position|career|karriere|vacature|offre", re.I)
# An address of one job rather than of a careers page about working there: only such pages are
# remembered on the list and their titles screened unopened.
_JOB_PAGE = re.compile(r"job|stelle|vacanc|position|vacature|offre", re.I)
_LONG_AGO = datetime.min.replace(tzinfo=UTC)


class SitemapSource(CareerSystemSource):
    id = "sitemap"
    # 2: retain separate original JobPosting requirements. 3: a JobPosting country outside the
    # supported ones marks the job abroad (remembered before as no country written).
    detail_cache_version = 3
    name = "Recruiters' and employers' own sites"
    system = "sitemap"
    parallel = 4  # every site has its own address

    def list_jobs(self, employer: Employer, ctx: SourceContext, *, countries=None, start=None,
                  terms=None) -> Iterator[FoundJob]:
        since = start - timedelta(days=1) if start else None
        # The searched countries' ad languages first, then English: the page a job is
        # advertised on in its own country says best which languages it needs.
        wanted = [language for code in countries or () for language in COUNTRIES[code].ad_languages]
        wanted = list(dict.fromkeys([*wanted, "en"]))
        entries = self._listing(employer, ctx, wanted)
        if terms is None:  # the directory check: the newest pages, whatever they are
            dated = [entry.changed for entry in entries if entry.changed is not None]
            if len(entries) > SURVEY_PAGES and (not dated or max(dated) - min(dated)
                                                < timedelta(days=1)):
                # Where the dates can't order the list (none, or all from the day the sitemap
                # was written), pages spread over the whole list: in its own order the first
                # ones can all be in one place. Mercedes-Benz's sitemap dates every page to the
                # seconds it was written in and lists its jobs alphabetically; its first twenty
                # named no German job (2026-11-25).
                step = len(entries) / SURVEY_PAGES
                entries = [entries[int((n + 0.5) * step)] for n in range(SURVEY_PAGES)]
            opened = 0
            for entry in entries:
                if opened >= SURVEY_PAGES:
                    return
                if self.allowed(entry.address, ctx):
                    opened += 1
                    if (job := self._from_page(entry.address, employer, ctx)) is not None:
                        yield self._placed(_listed_place(job, entry, employer), entry.place)
                    elif (bare := self._title_only(entry, {}, None)) is not None:
                        yield bare
            return
        # The whole list, matching or not: a job new on it since its last reading is dated by
        # its first sight (listmemory), whatever language its address is in this time.
        sights = listmemory.note(self.id, employer.board,
                                 [entry.key for entry in entries if entry.job])
        if start is not None:
            # Pages new on the list since the window began come first, then those listed
            # before it (older than the window: wanted only as older copies). Where a sitemap
            # dates every page to the moment it was written (Mercedes-Benz's, 2026-11-25), its
            # dates can't put new pages first, and MAX_PAGES would take the first ones in the
            # list's own order (the alphabet).
            entries = sorted(entries, key=lambda entry: _listed_before(sights.get(entry.key),
                                                                       start))
        opened, unread = 0, []
        for entry in entries:
            if not entry.titled:
                # An address that names no title (BMW's, Porsche's): the page is opened only for
                # a job new on the list since its last reading, which its first sight dates; it
                # gives the title, and one the search words miss goes to the person's AI like
                # other career sites' titles (`keep_job`).
                if (opened >= MAX_PAGES
                        or (sight := self._fresh_sight(entry, sights, start)) is None
                        or not self.allowed(entry.address, ctx)):
                    continue
                opened += 1
                if (job := self._from_page(entry.address, employer, ctx)) is not None:
                    yield _dated(job, *sight)
                continue
            if not matches_terms(terms, set(wanted), entry.title or words_of(entry.address)):
                # Titles the search words miss go to the person's AI like other career sites'
                # (a page is opened only for a title it keeps, `load_details`); only jobs new
                # since the list's last reading, as on SuccessFactors. Rheinmetall's
                # "Entwicklungsingenieur Elektrotechnik" and "Elektrischer Entwickler" spell
                # none of an electronics engineer's search words (2026-11-25).
                if (new := self._new_title(entry, sights, start, ctx)) is not None:
                    unread.append(_with_job_pages(new, employer))
                continue
            if opened >= MAX_PAGES or (since is not None and entry.changed is not None
                                       and entry.changed < since):
                continue
            # A page the site's robots.txt closes is never opened, nor counted among the pages
            # a search opens (Rheinmetall closes 11 of the 13 languages its sitemap lists).
            if not self.allowed(entry.address, ctx):
                continue
            opened += 1
            job = self._from_page(entry.address, employer, ctx)
            if job is not None:
                yield self._placed(_listed_day(_listed_place(job, entry, employer), entry, sights,
                                               start), entry.place)
            elif (bare := self._title_only(entry, sights, start)) is not None:
                yield bare
        yield from unread

    def _placed(self, job: FoundJob, place: str | None) -> FoundJob:
        """The job with the place its site's list gives it, where the list states one
        (listpages.py); a sitemap states none."""
        return job

    def _title_only(self, entry: "Listed", sights: dict, start: datetime | None
                    ) -> FoundJob | None:
        """A listed page that carries no job data, as the list gives it; a sitemap's page
        without job data is no job (a careers page about working there), so none."""
        return None

    def _listing(self, employer: Employer, ctx: SourceContext, languages: list[str]
                 ) -> list["Listed"]:
        """The site's listed pages, newest first, one per job. Where the addresses of a site's
        job pages speak of no job ("/de/pcb-layout-design-engineer-248186-mer000469f",
        Mercedes-Benz's, 2026-11-25), the directory gives their pattern (`Employer.jobs`, as for
        list pages): only addresses it finds are job pages, and its first group, when it has
        one, names the job in every language and is no part of its title."""
        pattern = re.compile(employer.jobs) if employer.jobs else None
        titled = pattern is None or employer.titles
        return [Listed(address, changed, key=job_key(address, pattern),
                       title=(title_of(address, pattern) or None) if pattern and titled else None,
                       job=pattern is not None or bool(_JOB_PAGE.search(urlsplit(address).path)),
                       titled=titled)
                for address, changed in one_address_per_job(
                    self._entries(employer.board, ctx, pattern), languages, pattern)]

    def _new_title(self, entry: "Listed", sights: dict, start: datetime | None,
                   ctx: SourceContext) -> FoundJob | None:
        """A job page new on the list since its last reading, dated to its first sight and
        named by the title the list gives or its address spells; None for any other page."""
        if not entry.job or not (title := entry.title or title_of(entry.address)):
            return None
        if (sight := self._fresh_sight(entry, sights, start)) is None:
            return None
        posted, precision = sight
        if entry.posted is not None:
            posted = entry.posted  # the employer's own day beats Jobcu's first sight
        if not self.allowed(entry.address, ctx):
            return None
        return FoundJob(source=self.id, source_job_id=entry.address, url=entry.address,
                        title=title, location_text=entry.around, posted_at=posted,
                        date_precision=precision, employer_url=entry.address,
                        source_context={"listed_place": entry.place} if entry.place else {})

    @staticmethod
    def _fresh_sight(entry: "Listed", sights: dict, start: datetime | None
                     ) -> tuple[datetime, str] | None:
        """The day a job new on the list since its last reading was posted, as its first sight
        proves it (`listmemory.posted`), when that is inside the window; else None."""
        posted, precision = listmemory.posted(sights.get(entry.key), start)
        if precision != "day" or (start is not None
                                  and freshness(posted, precision, start) != "fresh"):
            return None
        return posted, precision

    def load_details(self, job: FoundJob, ctx: SourceContext) -> FoundJob:
        """A job listed by its address only (a title the search words missed): its page's
        title, place, ad and date; where the page gives no date, its first sight stands."""
        full = self._from_page(job.url, Employer(job.company or "", self.system, "", (),
                                                 jobs=job.source_context.get("job_pages")), ctx)
        if full is None:
            return job
        if full.posted_at is None:
            full = dataclasses.replace(full, posted_at=job.posted_at,
                                       date_precision=job.date_precision)
        if place := job.source_context.get("listed_place"):
            placed = self._placed(full, place)
            # The list's place was already found to be in a country searched; a page that
            # says otherwise doesn't move the job abroad now.
            full = placed if placed.country != OTHER else dataclasses.replace(
                full, location_text=job.location_text, country=job.country)
        return full

    def readable(self, employer: Employer, ctx: SourceContext) -> bool:
        """One job page must carry JobPosting data with its posting date, or, where the
        directory names the site's job pages, an ad its text gives (the list's first sight
        dates such jobs)."""
        for job in self.list_jobs(employer, ctx):
            return job.posted_at is not None or bool(employer.jobs and job.description)
        return False

    def survey(self, employer: Employer, ctx: SourceContext) -> Survey:
        """The countries of the newest pages (SURVEY_PAGES), and those only the ends of the
        other job pages' addresses name: a sample, so their towns aren't recorded as all the
        towns the site's jobs are in."""
        survey = super().survey(employer, ctx)
        survey.sample = True
        # The newest pages of a large site can all be abroad: ams OSRAM's twenty newest of 271
        # named no German job while 19 addresses end in Regensburg, Munich or Garching
        # (2026-11-26), so searches in Germany would have skipped it. The list is the one
        # already read (the client keeps its answer): no more requests.
        named: Counter = Counter()
        pattern = re.compile(employer.jobs) if employer.jobs else None
        for entry in self._listing(employer, ctx, ["en"]):
            if entry.job:
                named.update(self._listed_countries(entry, pattern))
        for code, count in named.items():
            if code not in survey.counts:
                survey.counts[code] = count
        return survey

    def _listed_countries(self, entry: "Listed", pattern: re.Pattern | None) -> set[str]:
        """The countries a listed job names without its page being opened: the end of its
        address, where many sites write the job's town (`address_countries`)."""
        return address_countries(entry.address, pattern) if entry.titled else set()

    def _entries(self, board: str, ctx: SourceContext, pattern: re.Pattern | None = None
                 ) -> list[tuple[str, datetime | None]]:
        return job_pages(self, board, ctx, pattern)

    def _from_page(self, address: str, employer: Employer, ctx: SourceContext) -> FoundJob | None:
        """The job from memory or from its page's JobPosting data; None without such data."""
        # Imported here: the job memory itself imports the sources (through dedupe).
        from jobcu import jobstore

        stub = FoundJob(source=self.id, source_job_id=address, url=address, title="")
        known = jobstore.remembered_ad(
            stub, reader_version=self.detail_cache_version)
        if known is not None and known.title:
            return _in_own_country(known, employer)
        if not self.allowed(address, ctx):
            return None
        try:
            response = self.get(address, ctx, cache=False)
        except (SourceError, BudgetExhausted):
            return None
        job = to_found_job(address, response.text, employer, source=self.id)
        if job is None and (frame := own_frame(response.text, str(response.url))) is not None:
            # A page that shows its ad in a frame of its own site, as a browser does: an iCIMS
            # career site's job page carries no job data, the frame it embeds
            # ("/jobs/6336/manufacturing-engineer/job?in_iframe=1") the whole ad with its
            # JobPosting data (TT Electronics', 2026-11-26). The job keeps its page's address.
            try:
                if self.allowed(frame, ctx):
                    job = to_found_job(address, self.get(frame, ctx, cache=False).text, employer,
                                       source=self.id)
            except (SourceError, BudgetExhausted):
                pass
        # A page without job data is read as text only where the directory names the site's job
        # pages, and only if the address still names one after redirects (Diehl's job pages lead
        # back to its list).
        if job is None and employer.jobs and re.search(employer.jobs, str(response.url)):
            job = page_job(address, response.text, employer, source=self.id)
        if job is not None:
            jobstore.remember_ad(job, reader_version=self.detail_cache_version)
        return _in_own_country(job, employer) if job is not None else None


@dataclasses.dataclass(frozen=True)
class Listed:
    """One job page a site lists: its address and last change (a sitemap's), the title the
    list gives it (a list page's link text), a key that stays the same whichever language's page
    is listed, and the text around its link (a list page's: often its town)."""

    address: str
    changed: datetime | None = None
    title: str | None = None
    key: str = ""
    around: str | None = None
    job: bool = True  # a job's page rather than a careers page about working there
    place: str | None = None  # the place the list's own data gives the job ("Paderborn")
    posted: datetime | None = None  # the day the list says the job was published
    titled: bool = True  # whether the address spells the job's title (BMW's names a number)


def to_found_job(address: str, page: str, employer: Employer,
                 source: str = "sitemap") -> FoundJob | None:
    posting = find_job_posting(page)
    if posting is None or not posting.title:
        return None
    return FoundJob(
        source=source,
        source_job_id=address,
        url=address,
        title=posting.title,
        company=posting.company or employer.name,
        location_text=posting.location_text,
        country=posting_country(posting),
        posted_at=posting.date_posted,
        date_precision=("exact" if posting.date_has_time else "day") if posting.date_posted
        else "unknown",
        description=posting.description,
        description_is_complete=posting.description_is_complete,
        job_types=posting.job_types,
        work_mode="remote" if posting.remote else None,
        employer_url=address,
        closes_at=posting.valid_through,
    )


def page_job(address: str, page: str, employer: Employer, source: str = "sitemap"
             ) -> FoundJob | None:
    """A job page without job data, read as text (`jobpage.read`): its title, its place and
    the ad. It gives no posting day; the list's first sight dates it."""
    if (ad := jobpage.read(page)) is None:
        return None
    return FoundJob(source=source, source_job_id=address, url=address, title=ad.title,
                    company=ad.company or employer.name or None, location_text=ad.place,
                    country=ad.country,
                    description=ad.text, description_is_complete=True, employer_url=address)


def _in_own_country(job: FoundJob, employer: Employer) -> FoundJob:
    """A job of a page the directory names, without a country, placed in the one of the
    employer's countries whose town or village its place names. A small town's name alone
    doesn't tell the country (a village abroad may share it), but the employer hires only in
    its own countries: Porsche's "Weissach", "Zuffenhausen" and "Bensberg" are in Germany
    (2026-11-25). Applied to a remembered job too, which a directory check may have read
    without the employer's countries."""
    if job.country or not job.location_text or not employer.jobs:
        return job
    found = {code for code in employer.countries if code in COUNTRIES
             and place_list.locate(job.location_text, code) is not None}
    return dataclasses.replace(job, country=found.pop()) if len(found) == 1 else job


def _listed_place(job: FoundJob, entry: "Listed", employer: Employer) -> FoundJob:
    """A job whose page names no place takes the text its list shows beside its link, as a
    title-only job does (UKAEA's pages leave their "Site Location" empty; its list names
    "UKAEA Culham, Oxfordshire" or "Rotherham, United Kingdom", 2026-11-25). The country comes
    only from what that text or the employer's own countries resolve; the text is never taken
    to mean abroad (it may be a department's name)."""
    if job.location_text or not entry.around or entry.place:
        return job
    found = job_countries(dataclasses.replace(job, country=None,
                                                      location_text=entry.around)) - {OTHER}
    country = job.country or (next(iter(found)) if len(found) == 1 else None)
    return _in_own_country(dataclasses.replace(job, location_text=entry.around, country=country),
                           employer)


def _listed_day(job: FoundJob, entry: "Listed", sights: dict, start: datetime | None
                ) -> FoundJob:
    """A job whose page gives no posting day dated by its list: the day the list gives it, else
    its first sight on the list (`listmemory.posted`: the day a job new since the last reading
    appeared, or a time before the window for one listed before it). UKAEA's job pages carry no
    job data and its list gives no days (2026-11-25); without this such a job matching the search
    words stayed "Posting date unknown" however new it was."""
    if job.posted_at is not None:
        return job
    if entry.posted is not None:
        return dataclasses.replace(job, posted_at=entry.posted, date_precision="day")
    posted, precision = listmemory.posted(sights.get(entry.key), start)
    return dataclasses.replace(job, posted_at=posted, date_precision=precision) if posted else job


def _dated(job: FoundJob, posted: datetime, precision: str) -> FoundJob:
    """The job dated by its first sight on its list where its page gives no day."""
    if job.posted_at is not None:
        return job
    return dataclasses.replace(job, posted_at=posted, date_precision=precision)


def _with_job_pages(job: FoundJob, employer: Employer) -> FoundJob:
    """A job listed by its address only remembers the pattern of its site's job pages, so its
    page can be read as text later (`load_details`)."""
    if employer.jobs:
        job.source_context = {**job.source_context, "job_pages": employer.jobs}
    return job


def job_pages(source: CareerSystemSource, board: str, ctx: SourceContext,
              pattern: re.Pattern | None = None) -> list[tuple[str, datetime | None]]:
    """A job sitemap's job pages with their last change, newest first (undated ones last); a
    sitemap index leads to its job sitemaps. Read through `source`: its robots check, request
    budget and report (the Workday reader looks an ad up on the employer's own site this way).
    Job pages are the addresses that speak of jobs, or those `pattern` finds where the
    directory gives the site's own pattern."""
    if not source.allowed(board, ctx):
        raise SourceError(f"{source.name}: {urlsplit(board).hostname} asks automated tools "
                          "not to read its job list.")
    text = _read(source, board, ctx)
    children = _INDEX.findall(text)
    if children:
        jobs = [child for child in children if _JOB_WORDS.search(urlsplit(child).path)]
        text = " ".join(_read(source, child, ctx) for child in (jobs or children)[:MAX_SITEMAPS]
                        if source.allowed(child, ctx))
    entries = [(unescape(address), parse_iso(changed) if changed else None)
               for address, changed in _URL.findall(text)]
    entries = [(address, changed) for address, changed in entries
               if (pattern.search(address) if pattern is not None
                   else _JOB_WORDS.search(urlsplit(address).path))]
    return sorted(dict(entries).items(),
                  key=lambda entry: (entry[1] is not None, entry[1] or _LONG_AGO),
                  reverse=True)


# A language (and maybe a region) as an address's first part: "/de/", "/en-gb/", "/pt_br/",
# "/enUS/". The region without a mark is in capitals, so "/jobs/" is no language.
_LANGUAGE_PART = re.compile(r"^/((?i:[a-z]{2}))(?:(?i:[_-][a-z]{2,4})|[A-Z]{2})?(?=/)")


def _named(address: str, pattern: re.Pattern | None) -> re.Match | None:
    """Where the directory's pattern of a site's job pages names the job (its first group: the
    vacancy's own code, the same in every language), the match that names it."""
    if pattern is None or not pattern.groups:
        return None
    match = pattern.search(address)
    return match if match is not None and match.group(1) else None


def one_address_per_job(entries: list[tuple[str, datetime | None]], languages: list[str],
                        pattern: re.Pattern | None = None) -> list[tuple[str, datetime | None]]:
    """One address for each job a sitemap lists under several languages ("/de/job/x/1",
    "/en/job/x/1"...; Rheinmetall's lists each of its 1,423 jobs in 13): the page in the first
    of `languages` it has, else the first listed, at the place of its newest listing. Without
    this a search opened the same job once per language. `entries` come newest first. Where
    `pattern` names the job, that name says which addresses are the same job: Mercedes-Benz
    numbers each language's page apart and keeps one code for the vacancy
    ("/de/ai-data-analytics-233242-bei00000us", "/en/ai-data-analytics-233238-bei00000us")."""
    chosen: dict[tuple[str, str], list] = {}
    for address, changed in entries:
        parts = urlsplit(address)
        rank = 0
        rest = parts.path
        if (language := _LANGUAGE_PART.match(parts.path)) is not None:
            code = language.group(1).lower()
            rank = languages.index(code) if code in languages else len(languages)
            rest = parts.path[language.end():]
        named = _named(address, pattern)
        key = (parts.netloc.lower(), f"#{named.group(1)}" if named else f"{rest}?{parts.query}")
        if key not in chosen:
            chosen[key] = [rank, address, changed]
        elif rank < chosen[key][0]:
            chosen[key][:2] = [rank, address]
    return [(address, changed) for _rank, address, changed in chosen.values()]


def _read(source: CareerSystemSource, address: str, ctx: SourceContext) -> str:
    body = source.get(address, ctx).content
    if body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    return body.decode("utf-8", "replace")


def country_code(written: str | None) -> str | None:
    """A supported country's code from what JobPosting data says ("GB", "UK", "Deutschland",
    "DEU"); None for anything else."""
    if not written:
        return None
    code = written.strip().upper()
    if code == "UK":
        code = "GB"
    if code in COUNTRIES:
        return code
    if code in ALPHA3:
        return ALPHA3[code]
    found = countries_in(written) - {OTHER}
    return next(iter(found)) if len(found) == 1 else None


def abroad(written: str) -> bool:
    """Whether what JobPosting data writes as a country names one outside the supported ones
    ("US", "USA", "Mexico"), rather than a supported one or no country ("EMEA", "Remote")."""
    if country_code(written) is not None:
        return False
    return written.strip().upper() in WORLD_CODES or countries_in(written) == {OTHER}


def posting_country(posting: JobPosting) -> str | None:
    """A job's country from its JobPosting addresses: the first supported country they name;
    OTHER when each names a country outside them (a job abroad, which no search here shows);
    else None. Before, a country outside them counted as none written: TT Electronics' job in
    Olathe, Kansas ("addressCountry": "US") was then placed in the UK, the one country its
    directory entry names (2026-11-26)."""
    written = posting.countries or ([posting.country] if posting.country else [])
    for one in written:
        if (code := country_code(one)) is not None:
            return code
    return OTHER if written and all(abroad(one) for one in written) else None


def words_of(address: str) -> str:
    """The words a job page's address spells, for matching the search words before opening it."""
    return " ".join(re.split(r"[/_\-.?=&+%]+", unquote(urlsplit(address).path)))


def job_key(address: str, pattern: re.Pattern | None = None) -> str:
    """A job page's address without its language part, or the job's name where the directory's
    pattern gives one: the same job whichever language's page a search picks
    (`one_address_per_job`)."""
    parts = urlsplit(address)
    if (named := _named(address, pattern)) is not None:
        return f"{parts.netloc.lower()}#{named.group(1)}"
    language = _LANGUAGE_PART.match(parts.path)
    path = parts.path[language.end():] if language else parts.path
    return f"{parts.netloc.lower()}{path}" + (f"?{parts.query}" if parts.query else "")


# A gender note in a title's address ("m_w_d", "m-f-d", "w-m-d", "all-genders").
_GENDER = re.compile(r"\b(?:[mwfdx] ){1,3}[mwfdx]\b|\ball genders?\b", re.IGNORECASE)


def title_of(address: str, pattern: re.Pattern | None = None) -> str:
    """The title a job page's address spells, from its longest wordy part
    ("/de/job/elektrischer_entwickler__m_w_d_/1191311" -> "elektrischer entwickler"), without
    the job's code where the directory's pattern names it ("-248186-mer000469f")."""
    if (named := _named(address, pattern)) is not None:
        address = address[:named.start(1)] + address[named.end(1):]
    parts = [part for part in unquote(urlsplit(address).path).split("/") if part]
    wordy = max(parts, key=lambda part: len(re.findall(r"[^\W\d_]", part)), default="")
    words = " ".join(word for word in re.split(r"[_\-.+%\s()\[\],]+", wordy)
                     if word and not word.isdigit())
    return " ".join(_GENDER.sub(" ", words).split())


def address_countries(address: str, pattern: re.Pattern | None = None) -> set[str]:
    """The countries the end of a job page's address names, where the site writes the job's
    town after its title ("/en/job/Design-Engineer-d_m_f-Regensburg/24800": DE; OTHER for a
    place outside the supported countries): its last word, else its last two or three, never
    the whole title. Only for the directory check: a wrong country there costs one reading of
    the list."""
    words = title_of(address, pattern).split()
    for size in (1, 2, 3):
        if len(words) > size and (found := countries_in(" ".join(words[-size:]))):
            return found
    return set()


def unescape(address: str) -> str:
    return address.replace("&amp;", "&")


_FRAME = re.compile(r"<iframe\b[^>]*?\bsrc\s*=\s*([\"'])(.*?)\1", re.IGNORECASE | re.DOTALL)


def own_frame(page: str, address: str) -> str | None:
    """The address of the first frame a page embeds from its own site (the same host), where
    some career systems show the ad; None if it embeds none (frames of video or analytics
    services are other sites)."""
    host = urlsplit(address).hostname
    for match in _FRAME.finditer(page):
        frame = urljoin(address, unescape(match.group(2).strip()))
        if (frame.startswith(("https://", "http://")) and urlsplit(frame).hostname == host
                and frame != address):
            return frame
    return None


def _listed_before(sight: "listmemory.Sight | None", start: datetime) -> bool:
    """Whether the list had the job before the search's window began (an older job)."""
    return sight is not None and sight.first_seen_at < start
