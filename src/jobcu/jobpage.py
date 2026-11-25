"""An employer's job page without the standard job data (schema.org JobPosting), read the way a
person reads it: the title its main heading gives, the place a label names ("Einsatzort:
Stuttgart", "Location: London") or else the town named just above the title, and the ad as the
page's main text.

Only pages the employer's own list says are job pages are read this way (the directory gives the
pattern of their addresses), so a careers page about working there is never taken for an ad. BMW's
and Porsche's job pages carry no job data (2026-11-25): BMW's show the department, town and day
above the title ("Retail Marketing Munich 25.11.2026"), Porsche's label the place and the company
under it ("Einsatzort: Stuttgart", "Gesellschaft: ..."). A day written on the page is not taken
for the posting day: nothing says which day it is, so such jobs are dated by their first sight on
the list (listmemory.py).
"""

import html
import re
from dataclasses import dataclass

from lxml import html as lxml_html
from lxml.etree import ParserError

from jobcu import places as place_list
from jobcu.placenames import countries_in
from jobcu.text import html_to_text, normalise, tidy

# Less main text than this is no ad: a page that builds its ad with scripts (Rippling's) or a
# notice that the job is filled.
MIN_TEXT = 400
# The text above the title that may name the town (BMW's "Retail Marketing", "Munich",
# "25.11.2026"); more is the page's own introduction, where a town would be a guess.
ABOVE_TITLE = 200
SHORT_LINE = 40
# What may follow a town's name on its line: a region or country, or "bei" a bigger town.
_QUALIFIED = re.compile(r"(?:\s*[,(/–-].*|\s+(?:bei|near|am|an der|im|in der)\s.*)?",
                        re.IGNORECASE)
# Labels a job page gives its place ("Einsatzort: Stuttgart", "Location: London"), on a line of
# their own or among others on one ("Kennziffer: J0001 Einsatzort: Stuttgart").
_PLACE_LABEL = re.compile(
    r"(?:^|(?<=\s))(?:job\s+|work(?:ing)?\s+)?(?:locations?|standorte?|arbeitsorte?|"
    r"einsatzorte?|dienstorte?|orte?|place of work|workplace|locatie|lieu(?: de travail)?|sede)"
    r"\s*(?:\(\w+\))?\s*[:：]\s*(.*)$", re.IGNORECASE)
# Labels a job page gives the hiring company ("Gesellschaft: Porsche Zentrum Bensberg").
_COMPANY_LABEL = re.compile(
    r"(?:^|(?<=\s))(?:gesellschaft|organi[sz]ation|company|unternehmen|firma|legal entity|"
    r"hiring company|employer|arbeitgeber)\s*[:：]\s*(.*)$", re.IGNORECASE)
# The next label on the same line ends a value ("Stuttgart Gesellschaft: Porsche AG").
_NEXT_LABEL = re.compile(r"\s+[A-ZÄÖÜ][\w/&.()\- ]{1,30}[:：](?:\s|$)")
_NOT_TEXT = (".//script|.//style|.//noscript|.//template|.//svg|.//iframe|.//form|.//button"
             "|.//nav")


@dataclass(frozen=True)
class PageAd:
    title: str
    place: str | None  # as the page writes it ("Bucharest, Cluj, Timisoara"), or the town's name
    country: str | None  # the town's country, where the place is a town named above the title
    text: str
    company: str | None = None  # the hiring company where a label names it


def read(page: str, listed_title: str | None = None) -> PageAd | None:
    """The ad on a job page without job data, or None when the page has no title or too little
    text to be an ad. Where the employer's list gives the job's title, the ad starts where the
    page names it: a site's own heading and its country switcher can come first ("About
    TDK-Lambda", "Change Location : France"; TDK-Lambda UK's job pages, 2026-11-26)."""
    try:
        document = lxml_html.fromstring(page)
    except (ParserError, ValueError):
        return None
    title = _title(document)
    main = next(iter(document.xpath("//main") or document.xpath("//*[@role='main']")
                     or document.xpath("//article") or document.xpath("//body")), None)
    if not title or main is None:
        return None
    for element in main.xpath(_NOT_TEXT):
        element.drop_tree()
    for element in main.iter("dt", "dd", "label"):
        # A label and its value in a definition list are lines of their own, as on screen.
        element.tail = "\n" + (element.tail or "")
    text = html_to_text(lxml_html.tostring(main, encoding="unicode"))
    if listed_title and (ad := _from_title(text, listed_title)) is not None:
        title, text = " ".join(listed_title.split()), ad
    if len(text) < MIN_TEXT:
        return None
    place, country = _labelled(text, _PLACE_LABEL, _a_place), None
    if place is None and (town := _town_above(text, title)) is not None:
        place, country = town.name, town.country
    return PageAd(title, place, country, text, _labelled(text, _COMPANY_LABEL))


def _from_title(text: str, title: str) -> str | None:
    """The page's text from the first line that names the title on; None if no line does."""
    wanted = " ".join(title.split()).casefold()
    lines = text.split("\n")
    for number, line in enumerate(lines):
        if wanted in " ".join(line.split()).casefold():
            return "\n".join(lines[number:]).strip()
    return None


def _title(document) -> str:
    for heading in document.xpath("//h1"):
        if text := tidy(" ".join(heading.text_content().split())):
            return text
    written = (document.xpath("string(//meta[@property='og:title']/@content)")
               or document.findtext(".//title") or "")
    # "Stellenanzeige: Title | Karriereportal | Company": the part before the site's name.
    return tidy(html.unescape(written).split(" | ")[0].removeprefix("Stellenanzeige:"))


def _labelled(text: str, label: re.Pattern, fits=lambda value: True) -> str | None:
    """The value a label gives, on its line or the next, up to the next label. A value on the
    next line counts only when it `fits`: an empty label ("Site Location:") is followed by
    whatever the page shows next."""
    lines = [line.strip().lstrip("•·*–- \t") for line in text.split("\n")]
    for number, line in enumerate(lines):
        if (match := label.search(line)) is None:
            continue
        value = match.group(1).strip() or next(
            (following for following in lines[number + 1:number + 3]
             if following and fits(following)), "")
        value = _NEXT_LABEL.split(value)[0].strip(" ,;.")
        if 1 < len(value) <= 120:
            return value
    return None


def _a_place(text: str) -> bool:
    """Whether a line names a place: a town or a country Jobcu knows."""
    return place_list.locate(text, villages=False) is not None or bool(countries_in(text))


def _town_above(text: str, title: str) -> place_list.Town | None:
    """The town named in the few short lines above the title (department, town, day). A line
    counts only when it is the town's name, maybe with a qualifier ("Garching bei München",
    "Cork, Ireland"): a sentence can hold a word that is also a town's name ("switch on")."""
    wanted = " ".join(title.split()).casefold()
    above = []
    for line in (" ".join(line.split()) for line in text.split("\n")):
        if wanted in line.casefold():
            break
        above.append(line)
    else:
        return None  # the title isn't in the text: nothing is known to be above it
    if not above or sum(len(line) for line in above) > ABOVE_TITLE:
        return None
    for line in above:
        if not line or len(line) > SHORT_LINE:
            continue
        town = place_list.locate(line, villages=False)
        if town is not None and _QUALIFIED.fullmatch(line[len(town.name):]) and (
                normalise(line[:len(town.name)]) == normalise(town.name)):
            return town
    return None
