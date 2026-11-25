"""Employers' own job lists published as web pages, whose job pages carry the standard job data
(schema.org JobPosting) for search engines' job listings. Many employers run an application
system Jobcu has no reader for (rexx, MHM eRecruiting, a site of their own) and still publish such
pages, so one reader serves them all. Checked 2026-11-25 (SOURCES.md): dSPACE's job finder (its 62
jobs in the page's own data), Würth Elektronik's rexx site (100 jobs a page) and Pfisterer's list of
its MHM job pages; each job page had the full ad, the posting day, the town and the country.

A board is the list page's address, and the directory gives the pattern of the employer's job
pages' addresses (`Employer.jobs`, a regular expression whose first group, when it has one, names
the job: `jid=(\\d+)`). Jobcu reads the list page and the further pages it links to for paging (the
same address with a page in the query: `?start=100`), and finds every job page's address in it,
whether in a link or in the page's own data, with the title the list gives (the link's text, or
the "title" beside the address in the data; else the words of the address) and the text around it,
which often names the town. From there it works like a job sitemap (sitemaps.py): titles matching
the search words have their page read; titles new on the list since its last reading go to the
person's AI, and a page is read only for a title it keeps; the list's first sight dates a job
whose page gives no date. Session numbers in addresses (rexx's `sid=`) are left out, so a job keeps
one address.
"""

import dataclasses
import html
import re
from datetime import date, datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from lxml import html as lxml_html
from lxml.etree import ParserError

from jobcu import listmemory
from jobcu import places as place_list
from jobcu.countries import COUNTRIES
from jobcu.freshness import day_at_utc
from jobcu.placenames import OTHER
from jobcu.sources import careers
from jobcu.sources.base import FoundJob, SourceContext, SourceError
from jobcu.sources.careers import Employer
from jobcu.sources.sitemaps import Listed, SitemapSource, title_of
from jobcu.text import normalise

# List pages read per employer and search: Würth Elektronik's 180 jobs fill two.
MAX_LIST_PAGES = 10
# Query parameters that name a visitor's session, not the page.
_SESSION = re.compile(r"^(?:sid|jsessionid|phpsessid|sessionid|session|cfid|cftoken)$", re.I)
# Query parameters that page through a list ("start=100", "page=2", umantis' "tc1152481=p2").
_PAGING = re.compile(r"^(?:start|page|p|pg|offset|seite|from|skip|tc\d+)$", re.I)
_ANCHOR = re.compile(r"<a\b([^>]*)>(.*?)</a\s*>", re.I | re.S)
_HREF = re.compile(r"\bhref\s*=\s*([\"'])(.*?)\1", re.I | re.S)
# A link that is only an icon names its job in these (Pfisterer's arrow links).
_LABEL = re.compile(r"\b(?:aria-label|title)\s*=\s*([\"'])(.*?)\1", re.I | re.S)
# "(opens in a new tab)" and the like at the end of such a label.
_NEW_TAB = re.compile(r"\s*\([^()]*\b(?:opens?|öffnet|new|neue[mn]?)\b[^()]*\)\s*$", re.I)
# An address in the page's own data ("href":"/jobs/..."), as dSPACE's job finder gives it.
_DATA_LINK = re.compile(r"[\"'](?:href|url|link|jobUrl)[\"']\s*:\s*[\"']([^\"'<>\s]+)[\"']", re.I)
# An address in an element's data attribute: umantis lists name their next page only in
# `data-pagination-next-href` (Diehl's, 2026-11-25).
_ATTR_LINK = re.compile(r"\bdata-[\w-]*href\s*=\s*([\"'])(.*?)\1", re.I | re.S)
_DATA_TITLE = re.compile(r"\"(?:title|jobTitle|name)\"\s*:\s*\"([^\"]{3,200})\"")
_DATA_PLACE = re.compile(r"\"(?:location|city|place|town|ort|standort)\"\s*:\s*\"([^\"]{2,120})\"",
                         re.I)
_TAG = re.compile(r"<[^>]+>")
# Text kept beside a link: enough for "Waldzimmern" or "Berlin, München, Waldenburg", and for
# umantis' town after the job's number, type, contract and department (about 200 characters).
AROUND = 300
# The longest data record read for a job's title and place (dSPACE's are about 400 characters).
RECORD = 3000


class ListPageSource(SitemapSource):
    id = "listpage"
    name = "Employers' own job pages"
    system = "listpage"
    parallel = 4  # every employer has its own address

    def _listing(self, employer: Employer, ctx: SourceContext, languages: list[str]
                 ) -> list[Listed]:
        if not employer.jobs:
            raise SourceError(f"{employer.name}: the directory doesn't say which links are jobs.")
        pattern = re.compile(employer.jobs)
        if not self.allowed(employer.board, ctx):
            raise SourceError(f"{employer.name} asks automated tools not to read its job list.")
        found: dict[str, Listed] = {}
        pages, seen = [employer.board], {without_session(employer.board)}
        while pages and len(seen) <= MAX_LIST_PAGES:
            address = pages.pop(0)
            response = self.get(address, ctx, cache=False)
            jobs, more = listed_jobs(response.text, str(response.url), pattern)
            new = [job for job in jobs if job.key not in found]
            found.update((job.key, job) for job in new)
            if found and not new:
                continue  # the same jobs again ("?start=0" is the first page): no further pages
            for page in more:
                if (key := without_session(page)) not in seen and self.allowed(page, ctx):
                    seen.add(key)
                    pages.append(page)
        return list(found.values())

    def _placed(self, job: FoundJob, place: str | None) -> FoundJob:
        """The job at the place its list gives it. dSPACE's job pages give the head office
        (Paderborn, Germany) for every job, its jobs in Zagreb and Trivandrum too, while its
        list names each job's own place (2026-11-25). The page's country stands where the
        list's place agrees with it or names its town; a place the list gives that names no
        known town and not the page's is taken to be abroad (OTHER)."""
        if not place:
            return job
        found = careers.job_countries(dataclasses.replace(job, country=None, location_text=place))
        if found:
            country = job.country if job.country in found else (
                next(iter(found)) if len(found) == 1 else None)
        elif job.location_text and normalise(job.location_text) in normalise(place):
            country = job.country
        else:
            country = OTHER
        return dataclasses.replace(job, location_text=place, country=country)

    def _title_only(self, entry: Listed, sights: dict, start) -> FoundJob | None:
        """A listed job whose page carries no job data (Rippling's pages build their ad with
        scripts, 2026-11-25): its title and place as the list gives them, dated by its first
        sight on the list, so the job isn't lost; its link opens the employer's ad."""
        if not (title := entry.title or title_of(entry.address)):
            return None
        posted, precision = ((entry.posted, "day") if entry.posted
                             else listmemory.posted(sights.get(entry.key), start))
        return FoundJob(source=self.id, source_job_id=entry.address, url=entry.address,
                        title=title, location_text=entry.around, posted_at=posted,
                        date_precision=precision, employer_url=entry.address,
                        source_context={"listed_place": entry.place} if entry.place else {})


def listed_jobs(page: str, base: str, pattern: re.Pattern) -> tuple[list[Listed], list[str]]:
    """The job pages a list page names, in its order, and the further list pages it links to
    for paging. `base` is the list page's own address."""
    text = html.unescape(page or "")
    # start, end, address, the link's own text, a label naming it
    links: list[tuple[int, int, str, str | None, str | None]] = []
    for match in _ANCHOR.finditer(text):
        if (href := _HREF.search(match.group(1))) is None:
            continue
        own = _visible(match.group(2))
        label = _LABEL.search(match.group(1))
        named = _NEW_TAB.sub("", " ".join(label.group(2).split())) if label else ""
        links.append((match.start(), match.end(), href.group(2), own or None, named or None))
    for match in _DATA_LINK.finditer(text):
        links.append((match.start(), match.end(), match.group(1), None, None))
    for match in _ATTR_LINK.finditer(text):
        links.append((match.start(), match.end(), match.group(2), None, None))
    links.sort()
    jobs: dict[str, Listed] = {}
    more: list[str] = []
    here = urlsplit(base)
    job_links = [(start, end) for start, end, address, _own, _named in links
                 if pattern.search(urljoin(base, address))]
    cards = _cards(page, base, pattern)
    for start, end, address, own, named in links:
        full = without_session(urljoin(base, address.strip()))
        parts = urlsplit(full)
        if parts.scheme not in ("http", "https"):
            continue
        match = pattern.search(full)
        if match is None:
            if ((parts.netloc, parts.path) == (here.netloc, here.path)
                    and any(_PAGING.match(name) for name, _ in parse_qsl(parts.query))):
                more.append(full)
            continue
        key = _key(full, match, pattern)
        title = own or named
        if key in jobs and (jobs[key].title or not title):
            continue
        record = _record(text, start)
        place = _data_value(_DATA_PLACE, record)
        title = title or _data_value(_DATA_TITLE, record)
        card = cards.get(key)
        posted = _listed_day(card)
        if card and title:
            card = " ".join(card.replace(title, " ").split())
        jobs[key] = Listed(
            full, title=title, key=key, place=place, posted=posted,
            around=place or (_place_in(card) if card else None)
            or _beside(text, start, end, job_links, after=bool(own)))
    return list(jobs.values()), list(dict.fromkeys(more))


def _key(address: str, match: re.Match, pattern: re.Pattern) -> str:
    """A job's key: its number on its host where the pattern names one, else its address."""
    return f"{urlsplit(address).netloc.lower()}#{match.group(1)}" if pattern.groups else address


# The longest text read as one job's card: beyond it, the "card" is the page itself.
CARD = 1500
_COUNTRY_CODE = re.compile(r"\(([A-Z]{2})\)")
# The day a list says a job was published, after a label naming it: "Online seit: 25.11.2026"
# (umantis), "Veröffentlicht am 3.11.26", "Posted on 2026-11-24".
_LISTED_DAY = re.compile(
    r"\b(?:online seit|veröffentlicht(?: am)?|ausgeschrieben am|eingestellt am|erstellt am|"
    r"posted(?: on)?|published(?: on)?|date posted)\s*:?\s*"
    r"(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})\b|\b(?:posted|published)(?: on)?\s*:?\s*"
    r"(\d{4})-(\d{2})-(\d{2})\b", re.IGNORECASE)


def _listed_day(card: str | None) -> datetime | None:
    """The publication day a job's card states after such a label; None without one."""
    match = _LISTED_DAY.search(card or "")
    if match is None:
        return None
    if match.group(1):
        day, month, year = (int(match.group(n)) for n in (1, 2, 3))
        year += 2000 if year < 100 else 0
    else:
        year, month, day = (int(match.group(n)) for n in (4, 5, 6))
    try:
        return day_at_utc(date(year, month, day))
    except ValueError:
        return None


def _cards(page: str, base: str, pattern: re.Pattern) -> dict[str, str]:
    """Each job's card on a list page: the largest element around its link that holds no other
    job's link (a table row, a list item, a box), as visible text. umantis puts a job's company
    and day before its link and its town after it, in the same row (Diehl's, 2026-11-25)."""
    try:
        root = lxml_html.fromstring(page or "<html></html>")
    except (ParserError, ValueError):
        return {}
    for hidden in root.xpath("//script|//style"):
        hidden.drop_tree()
    keys: dict = {}
    for anchor in root.iter("a"):
        href = anchor.get("href")
        if not href:
            continue
        full = without_session(urljoin(base, href.strip()))
        if (match := pattern.search(full)) is not None:
            keys[anchor] = _key(full, match, pattern)
    cards: dict[str, str] = {}
    for anchor, key in keys.items():
        if key in cards:
            continue
        node = anchor
        while (parent := node.getparent()) is not None and not any(
                keys.get(other, key) != key for other in parent.iter("a")):
            node = parent
        words = " ".join(" ".join(node.itertext()).split())
        if len(words) <= CARD:
            cards[key] = words
    return cards


def _place_in(card: str) -> str | None:
    """The town and country a job's card names ("Überlingen, Germany"), else the card's text."""
    if not card:
        return None
    found = careers.job_countries(FoundJob(source="listpage", source_job_id="", url="",
                                           title="", location_text=card)) - {OTHER}
    # umantis writes "Überlingen am Bodensee (DE)": the country's code after the town.
    found = found or {code for code in _COUNTRY_CODE.findall(card) if code in COUNTRIES}
    if len(found) == 1:
        code = next(iter(found))
        town = place_list.locate(card, code, villages=False)
        if town is not None:
            return f"{town.name}, {COUNTRIES[code].name}"
    return card[:AROUND]


def _beside(text: str, start: int, end: int, job_links: list[tuple[int, int]], after: bool
            ) -> str | None:
    """The text beside a job's link, up to the next or back to the previous job's link: after
    it when the link carries the title (the details follow it, as on rexx sites), before it when
    the link is only an icon after the details (Pfisterer's cards)."""
    if after:
        following = next((other for other, _ in job_links if other > start), len(text))
        words = _visible(text[end:following])
        return words[:AROUND] or None
    previous = max((other_end for _, other_end in job_links if other_end <= start), default=0)
    words = _visible(text[previous:start])
    return words[-AROUND:] or None


_HIDDEN = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)


def _visible(fragment: str) -> str:
    """A page fragment's visible words: without its style and script blocks (Rippling's job
    cards carry their own styles), also one the fragment cuts in half."""
    fragment = _HIDDEN.sub(" ", fragment)
    fragment = re.sub(r"<(?:script|style)\b.*\Z", " ", fragment, flags=re.I | re.S)
    fragment = re.sub(r"\A.*?</(?:script|style)\s*>", " ", fragment, flags=re.I | re.S)
    return " ".join(_TAG.sub(" ", fragment).split())


def without_session(address: str) -> str:
    """The address without a visitor's session number, which some systems add to every link."""
    parts = urlsplit(address)
    if not parts.query:
        return address
    query = [(name, value) for name, value in parse_qsl(parts.query, keep_blank_values=True)
             if not _SESSION.match(name)]
    return urlunsplit(parts._replace(query=urlencode(query), fragment=""))


def _record(text: str, position: int) -> str:
    """The data record (a short "{...}" without inner braces) an address in the page's data
    sits in; empty when it isn't in one."""
    opening, closing = text.rfind("{", 0, position), text.find("}", position)
    if (opening < 0 or closing < 0 or closing - opening > RECORD
            or "}" in text[opening:position] or "{" in text[position:closing]):
        return ""
    return text[opening:closing + 1]


def _data_value(pattern: re.Pattern, record: str) -> str | None:
    match = pattern.search(record) if record else None
    return " ".join(match.group(1).split()) if match else None


# Recognising a careers page as a list of jobs by itself (employers.py): a job's address names it
# by a number of four digits or more, a UUID, or a code of 8 to 12 letters and digits mixed
# (JazzHR's "cto8fD1zOl"), in the same place on every job's address.
_ID = re.compile(
    r"(?<!\d)(\d{4,})(?!\d)|(?<![0-9A-Za-z])([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{12}|(?=[A-Za-z]*\d)(?=\d*[A-Za-z])[A-Za-z0-9]{8,12})(?![0-9A-Za-z])")
# A job's title spelled in its address before its number ("/de/job/hardware_entwickler/900713"):
# it differs from job to job, so it is no part of the shape.
_SLUG = re.compile(r"^(?=.{16,})[^/]*[-_+%][^/]*$")
# Shapes whose addresses speak of jobs are tried first (a list of product pages can be bigger).
_JOBBY = re.compile(r"job|stelle|karriere|career|vacanc|position|offer|apply|bewerb|recruit",
                    re.IGNORECASE)
_ID_PATTERNS = {"number": r"\d+", "uuid": r"[0-9a-f-]{36}", "code": r"[A-Za-z0-9]{8,12}"}
# A list needs at least this many jobs of one shape to be taken for one.
MIN_LISTED = 3
# Shapes tried per page, the biggest first (a news list can outnumber a short job list).
MAX_SHAPES = 3


def recognise(base: str, page: str) -> list[tuple[str, str]]:
    """The likely patterns of a careers page's job addresses, each with one of those addresses,
    the most links first: links of one shape that name at least MIN_LISTED different things by
    number. Whether such an address is a job (its page carries job data) is the caller's check."""
    text = html.unescape(page or "")
    addresses = [match.group(2) for match in (_HREF.search(m.group(1))
                                              for m in _ANCHOR.finditer(text)) if match]
    addresses += _DATA_LINK.findall(text)
    here = without_session(base)
    shapes: dict[tuple, tuple[str, set[str], str]] = {}
    for address in addresses:
        full = without_session(urljoin(base, address.strip()))
        if full == here or urlsplit(full).scheme not in ("http", "https"):
            continue
        if (shape := _shape(full)) is not None:
            key, pattern, number = shape
            entry = shapes.setdefault(key, (pattern, set(), full))
            entry[1].add(number)
    found = sorted((entry for entry in shapes.values() if len(entry[1]) >= MIN_LISTED),
                   key=lambda entry: (not _JOBBY.search(urlsplit(entry[2]).path + "?"
                                                         + urlsplit(entry[2]).query),
                                      -len(entry[1])))
    return [(pattern, sample) for pattern, _numbers, sample in found[:MAX_SHAPES]]


def _shape(address: str) -> tuple[tuple, str, str] | None:
    """An address's shape (where its number sits and what surrounds it), the pattern that
    matches every address of that shape with the number as its first group, and the number."""
    parts = urlsplit(address)
    for name, value in parse_qsl(parts.query):
        if re.fullmatch(r"\d{3,}", value):
            pattern = (re.escape(f"{parts.netloc}{parts.path}") + r"\?(?:[^#]*&)?"
                       + re.escape(name) + r"=(\d+)")
            return (parts.netloc, parts.path, "query", name), pattern, value
    segments = parts.path.split("/")
    for position in range(len(segments) - 1, -1, -1):
        match = _ID.search(segments[position])
        if match is None:
            continue
        group = 1 if match.group(1) else 2
        number = match.group(group)
        kind = ("number" if number.isdigit() else
                "uuid" if len(number) == 36 and number.count("-") == 4 else "code")
        before = segments[position][:match.start(group)]
        after = segments[position][match.end(group):]
        tail = re.search(r"[^A-Za-z0-9]?[A-Za-z]{0,2}$", before).group()
        ending = after if re.fullmatch(r"(?:\.[A-Za-z]{2,5})?", after) else "*"
        following = len(segments) - position - 1
        leading = "/".join("*" if _SLUG.match(segment) else segment
                           for segment in segments[:position])
        pattern = ("/".join(re.escape(f"{parts.netloc}{piece}") if index == 0 else
                            "[^/]+" if piece == "*" else re.escape(piece)
                            for index, piece in enumerate(leading.split("/")))
                   + "/[^/]*?" + re.escape(tail)
                   + f"({_ID_PATTERNS[kind]})" + ("[^/]*" if ending == "*" else re.escape(ending))
                   + (r"(?:/[^/?#]*){" + str(following) + "}" if following else ""))
        return (parts.netloc, leading, tail, kind, ending, following), pattern, number
    return None
