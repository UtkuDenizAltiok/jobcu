"""Towns and how far apart they are, so "within 50 km" works for sources that give only a name.

Job sources with their own location filter (Adzuna, Reed, the Bundesagentur) do the distance
work themselves. Company career sites and some job boards only say "Garching" or "Ireland,
Limerick", so Jobcu looks the town up in the list it ships (`data/places.csv.gz`, from GeoNames)
and measures the distance itself.

The list holds the towns with at least 1,000 inhabitants in the supported countries. Germany, the
UK and Ireland also have a list of smaller and unmeasured places (`data/villages.csv.gz`: Parsdorf,
Whiteley), which `locate` reads only when a location names one outright: it never finds a village
inside other words, and a village is never a reference place for a journey. Some job sites give
only a postcode ("CB22 4QR", "T12 X70A"), so the UK's postcode districts and Ireland's Eircode
areas are shipped too (`data/postcodes.csv.gz`), each with a point, and a postcode stands for the
town it lies in.
"""

import csv
import gzip
import re
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from functools import cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from jobcu.text import normalise

DATA = Path(__file__).resolve().parent / "data" / "places.csv.gz"
VILLAGES = Path(__file__).resolve().parent / "data" / "villages.csv.gz"
REGIONS = Path(__file__).resolve().parent / "data" / "regions.csv.gz"
POSTCODES = Path(__file__).resolve().parent / "data" / "postcodes.csv.gz"
STATIONS = Path(__file__).resolve().parent / "data" / "stations.csv"
MAX_NAME_WORDS = 4  # "Frankfurt am Main", "'s-Hertogenbosch"
EARTH_RADIUS_KM = 6371.0


def people_for_share(share: float | None, population: int) -> int:
    """The smallest whole population satisfying the decimal percentage the person supplied."""
    return int((Decimal(str(share or 0)) * population).to_integral_value(rounding=ROUND_CEILING))


# Job ads shorten names: "Ottobrunn" for "Ottobrunn bei München", "Halle" for "Halle (Saale)".
_QUALIFIERS = re.compile(
    r"\s*[(,].*|\s+(?:bei|an der|an dem|am|im|in der|ob der|vor der|unter|auf|a\.d\.|sur|sous|"
    r"près de|nad|nad|pri|del|di|de|na)\s+.*$",
    re.IGNORECASE,
)
# Parts of a location that name a district or county, not a town: "München (Kreis)" is the
# district around Munich, not the city, and "Co. Cork" is the county, not Cork city. They are
# used only when nothing more precise is named.
_DISTRICT = re.compile(
    r"\((?:land)?kreis\)|\b(?:land)?kreis\b|\bco\.?\s|\bcounty\b|\bbezirk\b|\bdistrict\b",
    re.IGNORECASE,
)

# States, nations and provinces a location may name on its own ("Sachsen", "Wales"). Some share a
# name with a town ("Sachsen bei Ansbach", Brandenburg an der Havel, a village called Wales), so
# they never count as that town: a job in "Sachsen" could be anywhere in Saxony. City states
# (Berlin, Hamburg, Bremen) and Salzburg are towns as well and aren't listed.
_REGIONS = frozenset(normalise(name) for name in (
    "Baden-Württemberg", "Bayern", "Bavaria", "Brandenburg", "Hessen", "Hesse",
    "Mecklenburg-Vorpommern", "Niedersachsen", "Lower Saxony", "Nordrhein-Westfalen",
    "North Rhine-Westphalia", "NRW", "Rheinland-Pfalz", "Rhineland-Palatinate", "Saarland",
    "Sachsen", "Saxony", "Sachsen-Anhalt", "Saxony-Anhalt", "Schleswig-Holstein", "Thüringen",
    "Thuringia", "England", "Scotland", "Wales", "Cymru", "Northern Ireland", "Great Britain",
    "United Kingdom", "Leinster", "Munster", "Connacht", "Ulster", "Tirol", "Tyrol",
    "Vorarlberg", "Kärnten", "Carinthia", "Steiermark", "Styria", "Niederösterreich",
    "Oberösterreich", "Burgenland", "Česká republika", "Česko", "Czechia", "Czech Republic",
))


# England's nine regions (the Office for National Statistics' ITL1 regions, with their codes),
# which GeoNames doesn't list: each is made of counties and unitary authorities in
# `regions.csv.gz`. Election results and many other facts are given per region: search 11's
# answer named five of them, and without them its condition left most of England unchecked.
ENGLISH_REGIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "GB.ENG.TLC": (("North East England", "North East", "North-East England"),
                   ("D1", "D8", "E5", "F5", "I5", "I7", "J5", "J6", "K9", "M7", "N3", "N6")),
    "GB.ENG.TLD": (("North West England", "North West", "North-West England"),
                   ("A8", "A9", "B1", "C1", "C9", "E9", "G9", "H2", "H8", "I2", "K1", "L2", "L5",
                    "L8", "N1", "N2", "O1", "O6", "P2", "P7", "Q1", "Z7", "Z8")),
    "GB.ENG.TLE": (("Yorkshire and the Humber", "Yorkshire and Humber", "Yorkshire"),
                   ("A3", "B4", "C2", "D5", "E1", "G6", "G8", "H3", "J2", "J3", "J7", "L3", "L9",
                    "O7", "Q5")),
    "GB.ENG.TLF": (("East Midlands",),
                   ("D2", "D3", "H4", "H5", "H7", "J8", "J9", "L4", "NNH", "WNH")),
    "GB.ENG.TLG": (("West Midlands",),
                   ("A7", "C7", "D7", "F7", "L6", "L7", "M2", "M9", "N4", "O2", "O8", "P3", "Q3",
                    "Q4")),
    "GB.ENG.TLH": (("East of England", "East England", "Eastern England"),
                   ("C3", "E4", "F8", "I1", "I9", "K3", "M5", "N5", "O3", "Z5", "Z6")),
    "GB.ENG.TLI": (("London", "Greater London"), ("GLA",)),
    "GB.ENG.TLJ": (("South East England", "South East", "South-East England"),
                   ("B3", "B6", "B9", "E2", "F2", "G2", "G5", "I3", "I6", "K2", "K6", "K7", "M1",
                    "M4", "N7", "P4", "P6", "P9", "Q2")),
    "GB.ENG.TLK": (("South West England", "South West", "South-West England"),
                   ("A4", "AA", "B7", "C6", "D4", "D6", "E6", "J4", "K4", "M3", "M6", "N9", "O4",
                    "P8", "Z9")),
}
_ENGLISH_MEMBERS = {code: frozenset(f"GB.ENG.{district}" for district in districts)
                    for code, (_, districts) in ENGLISH_REGIONS.items()}


def region_inside(inner: str, outer: str) -> bool:
    """Whether the region coded `inner` lies in `outer`: the same one, or an English county or
    district inside one of England's nine regions."""
    district = ".".join(inner.split(".")[:3])
    return inner == outer or district in _ENGLISH_MEMBERS.get(outer, ())


@dataclass(frozen=True)
class Town:
    name: str
    country: str
    latitude: float
    longitude: float
    people: int  # 0 when GeoNames has no figure, as for most British villages
    # The state, province or nation, the county or district, and (in England) the council
    # district inside a county, as codes in `regions.csv.gz` ("DE.13" is Saxony, "DE.K.14625"
    # Landkreis Bautzen, "GB.ENG.G5.2636057" Thanet in Kent).
    region: str = ""
    district: str = ""
    area: str = ""

    def lies_in(self, code: str) -> bool:
        return code in (self.region, self.district, self.area) or (
            self.district in _ENGLISH_MEMBERS.get(code, ()))


@dataclass(frozen=True)
class Region:
    code: str
    # "region" (a state, province or nation), "district" (a county or district) or "area" (a
    # council district inside a county)
    level: str
    country: str
    name: str


def lookup_names(spellings) -> set[str]:
    """What a town is filed under: each spelling, whole and without its qualifier, with "Sankt"
    and "St." the same word (GeoNames has Sankt Wendel, ads say St. Wendel)."""
    written = {normalise(name) for name in spellings}
    short = {normalise(_QUALIFIERS.sub("", name)) for name in spellings}
    names = (written | short) - {""}
    return names | {re.sub(r"\bsankt\b", "st", name) for name in names} | {
        re.sub(r"\bst\b", "sankt", name) for name in names}


@cache
def _towns(path: Path = DATA) -> dict[str, tuple[Town, ...]]:
    """Every town by its normalised name, biggest first ("Berlin" is the German capital)."""
    index: dict[str, list[Town]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for row in csv.reader(line for line in file if not line.startswith("#")):
            names, country, latitude, longitude, people, *codes = row
            spellings = names.split("|")
            town = Town(spellings[0], country, float(latitude), float(longitude), int(people),
                        *codes)
            for spelling in lookup_names(spellings):
                index.setdefault(spelling, []).append(town)
    return {name: tuple(sorted(towns, key=lambda t: -t.people))
            for name, towns in index.items()}


@cache
def towns_in(country: str) -> tuple[Town, ...]:
    """Every town of one country in the list, biggest first."""
    unique = {town for towns in _towns().values() for town in towns if town.country == country}
    return tuple(sorted(unique, key=lambda town: -town.people))


# Words that say what kind of region a name is, not which one: "Landkreis Bautzen", "Bautzen
# district" and "Bautzen" are the same district; "Free State of Saxony" is Saxony.
_REGION_WORDS = re.compile(
    r"\b(?:landkreis|kreisfreie stadt|stadtkreis|kreis|bezirk|regierungsbezirk|district|"
    r"county|borough|royal borough|city and county|city|metropolitan|unitary authority|council|"
    r"region|province|provincia|provincie|state|free state|freistaat|land|bundesland|"
    r"department|departement|département|voivodeship|województwo|of|the|de|di|del|du|la|le)\b"
)


def _region_key(name: str | None) -> str:
    return " ".join(_REGION_WORDS.sub(" ", normalise(name)).split())


@cache
def _regions(path: Path = REGIONS) -> dict[str, tuple[Region, ...]]:
    """Every state, province, nation, county and district by its normalised names, with and
    without words like "Landkreis" or "County"."""
    index: dict[str, list[Region]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as file:
        for row in csv.reader(line for line in file if not line.startswith("#")):
            code, level, country, names = row
            spellings = names.split("|")
            region = Region(code, level, country, spellings[0])
            keys = {normalise(name) for name in spellings} | {_region_key(n) for n in spellings}
            for key in keys - {""}:
                index.setdefault(key, []).append(region)
    for code, (spellings, _) in ENGLISH_REGIONS.items():
        region = Region(code, "region", "GB", spellings[0])
        for key in {normalise(name) for name in spellings} | {_region_key(n) for n in spellings}:
            index.setdefault(key, []).append(region)
    return {key: tuple(regions) for key, regions in index.items()}


def find_region(name: str | None, country: str | None = None) -> Region | None:
    """The state, province, nation, county or district with this name, in the given country.
    A whole name wins over a shortened one, and a state over a district of the same name."""
    for key in (normalise(name), _region_key(name)):
        found = [region for region in _regions().get(key, ())
                 if country is None or region.country == country]
        if found:
            return min(found, key=lambda region: region.level != "region")
    return None


def named(name: str | None) -> tuple[Town, ...]:
    """Every town called exactly this, in any supported country, biggest first."""
    return _towns().get(normalise(name), ())


def find(name: str | None, country: str | None = None) -> Town | None:
    """The best known town with this name, preferring the one in the given country."""
    towns = _towns().get(normalise(name))
    if not towns:
        return None
    if country:
        in_country = [town for town in towns if town.country == country]
        return in_country[0] if in_country else None
    return towns[0]


# "London (+1 other)", "München (+ 1 weiterer Standort)": Google's listing of several workplaces.
_MORE_PLACES = re.compile(r"\(\s*\+\s*\d+[^)]*\)")


def names_more_places(text: str | None) -> bool:
    """True when a location says the job has more workplaces than the one it names."""
    return _MORE_PLACES.search(text or "") is not None


def without_more_places(text: str | None) -> str:
    return _MORE_PLACES.sub("", text or "").strip()


def locate(text: str | None, country: str | None = None, *, villages: bool = True) -> Town | None:
    """The town a free-text location names ("Ireland, Limerick" → Limerick).

    Longer names win ("Frankfurt am Main" over "Frankfurt"), then the bigger town. A district
    or county counts only when no town is named besides it ("Unterhaching, München (Kreis)" is
    Unterhaching), and a state or nation never counts ("Sachsen" is no town). When no town is
    named, a village of the given country counts if a piece of the location is its whole name
    ("Parsdorf, Bavaria, Germany"; `villages=False` for text that isn't surely a place). A location
    with neither but a UK postcode or an Eircode is the town that postcode lies in.
    """
    text = without_more_places(text)
    parts = [_town_of_district(part) for part in re.split(r"[,;|]", text)
             if normalise(part) not in _REGIONS]
    if not any(part.strip() for part in parts):
        return None

    def named_in(words: str) -> Town | None:
        return _locate(words, country) or (_village(words, country) if villages else None)

    precise = [part for part in parts if not _DISTRICT.search(part)]
    if precise and len(precise) < len(parts):
        town = named_in(", ".join(precise))
        if town is not None:
            return town
    return named_in(", ".join(parts)) or postcode_town(text, country)


# A full UK postcode ("CB22 4QR", "S336RR") or one standing alone ("CB22"), and a full Eircode
# ("T12 X70A"): the part before the space is the district or routing key.
_UK_POSTCODE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?)\s*\d[A-Z]{2}\b")
_UK_DISTRICT_ONLY = re.compile(r"\s*([A-Z]{1,2}\d[A-Z\d]?)\s*")
_EIRCODE = re.compile(r"\b([AC-FHKNPRTV-Y]\d{2}|D6W)\s*[0-9AC-FHKNPRTV-Y]{4}\b")


@cache
def _postcodes(path: Path = POSTCODES) -> dict[tuple[str, str], tuple[float, float]]:
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return {(country, code): (float(latitude), float(longitude))
                for code, country, latitude, longitude
                in csv.reader(line for line in file if not line.startswith("#"))}


def postcode_town(text: str | None, country: str | None = None) -> Town | None:
    """The town a UK postcode or an Eircode in the text lies in, or None."""
    text = (text or "").upper()
    candidates = []
    if country in (None, "GB"):
        candidates += [("GB", m.group(1)) for m in _UK_POSTCODE.finditer(text)]
        if (alone := _UK_DISTRICT_ONLY.fullmatch(text)) is not None:
            candidates.append(("GB", alone.group(1)))
    if country in (None, "IE"):
        candidates += [("IE", m.group(1)) for m in _EIRCODE.finditer(text)]
    for key in candidates:
        if key in _postcodes():
            return _town_at(*_postcodes()[key], key[0])
    return None


def reach_km(town: Town) -> float:
    """How far a town's built-up area reaches from its centre, roughly, from its population:
    about 1.5 km for a village, 6 km for Augsburg, 11 km for Munich, 23 km for London."""
    return max(1.5, 0.6 * (town.people / 1000) ** 0.4)


@cache
def _main_stations() -> dict[tuple[str, str], tuple[tuple[float, float], ...]]:
    stations: dict[tuple[str, str], list[tuple[float, float]]] = {}
    with STATIONS.open(encoding="utf-8", newline="") as file:
        for country, town, _, latitude, longitude in csv.reader(
                line for line in file if not line.startswith("#")):
            stations.setdefault((country, town), []).append((float(latitude), float(longitude)))
    return {key: tuple(points) for key, points in stations.items()}


def main_stations(town: Town) -> tuple[tuple[float, float], ...]:
    """The points of a town's main railway stations, where `data/stations.csv` lists them. A
    village with a listed city's name has none: a station must lie within the town's reach."""
    return tuple(point for point in _main_stations().get((town.country, town.name), ())
                 if km(town.latitude, town.longitude, *point) <= reach_km(town))


@cache
def _town_at(latitude: float, longitude: float, country: str) -> Town | None:
    """The town a point lies in: the biggest town whose built-up area reaches it, or else the
    nearest town. A city's own districts in the list must not win over the city."""
    nearest: tuple[float, Town] | None = None
    inside: Town | None = None
    for town in towns_in(country):
        distance = km(latitude, longitude, town.latitude, town.longitude)
        if nearest is None or distance < nearest[0]:
            nearest = (distance, town)
        if distance <= reach_km(town) and (inside is None or town.people > inside.people):
            inside = town
    return inside or (nearest[1] if nearest else None)


# Only towns this big reach farther than about 3 km, so only they can contain another town.
_CONTAINING_PEOPLE = 50_000


@cache
def _big_towns(country: str) -> tuple[Town, ...]:
    return tuple(town for town in towns_in(country) if town.people >= _CONTAINING_PEOPLE)


@cache
def part_of(town: Town) -> Town | None:
    """The bigger town this one lies inside, when the list names a city's own district as a
    town of its own (Hamburg's Wandsbek and Eimsbüttel, London's boroughs), else None."""
    for bigger in _big_towns(town.country):
        if bigger.people <= town.people:
            return None
        if distance_km(bigger, town) <= reach_km(bigger):
            return bigger
    return None


_HYPHENATED = re.compile(r"\b(\w+)-(\w+(?:-\w+)*)\b")


def _town_of_district(text: str) -> str:
    """Ads write a district after its town: "Wietmarschen-Lohne" is Lohne in Wietmarschen, not
    the town of Löhne. A hyphenated name the list doesn't know stands for its first part, when
    that is a town ("Castrop-Rauxel" is a town in its own right and stays)."""
    def first_part(match: re.Match) -> str:
        whole, town = match.group(0), match.group(1)
        return town if find(whole) is None and find(town) is not None else whole

    return _HYPHENATED.sub(first_part, text)


def _locate(text: str | None, country: str | None) -> Town | None:
    words = normalise(text).split()
    best: Town | None = None
    best_words = 0
    for start in range(len(words)):
        for length in range(min(MAX_NAME_WORDS, len(words) - start), 0, -1):
            if length < best_words:
                break
            town = find(" ".join(words[start : start + length]), country)
            if town is not None and (length > best_words or
                                     (best is not None and town.people > best.people)):
                best, best_words = town, length
    return best


@cache
def _villages(path: Path = VILLAGES) -> dict[tuple[str, str], Town]:
    """Every village by its country and normalised name. No two far apart share a name."""
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return {(country, normalise(name)): Town(name, country, float(latitude), float(longitude),
                                                 int(people), *codes)
                for name, country, latitude, longitude, people, *codes
                in csv.reader(line for line in file if not line.startswith("#"))}


# What separates the pieces of a location ("Parsdorf - DE", "Whiteley  United Kingdom", "Ulm •
# über XING").
_PIECES = re.compile(r"[,;|/()•]|\s{2,}|\s[-–—]\s")
_NUMBERS = re.compile(r"\b\d+\b")  # "85599 Parsdorf"


def _village(text: str, country: str | None) -> Town | None:
    """The village a piece of the location is the whole name of, or names first with hyphens
    ("Kesselsdorf-Saxony-Germany"), in a known country: a name alone is too little to tell a
    village's country."""
    if not country:
        return None
    for piece in _PIECES.split(text):
        for words in (piece, piece.split("-")[0]):
            town = _villages().get((country, " ".join(_NUMBERS.sub(" ", normalise(words)).split())))
            if town is not None:
                return town
    return None


def distance_km(a: Town, b: Town) -> float:
    """Distance in a straight line, which is close enough for "within 50 km"."""
    return km(a.latitude, a.longitude, b.latitude, b.longitude)


def km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """Distance in a straight line between two points on the map."""
    lat1, lon1, lat2, lon2 = map(radians, (lat_a, lon_a, lat_b, lon_b))
    haversine = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(haversine))
