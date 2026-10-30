"""Rebuilds the list of towns Jobcu ships (src/jobcu/data/places.csv.gz) and the regions they
lie in (src/jobcu/data/regions.csv.gz).

Jobcu needs coordinates for towns so it can tell how far a job is from the place someone asked
for, when a job source gives only a place name, and the region of each town so a fact decided for
a whole state or district ("far-right parties are strong everywhere in Saxony") applies to its
small towns too. The lists come from GeoNames' free exports, narrowed to the supported countries:

- `cities1000`: populated places with a known population of over 1,000, with their coordinates
  and region codes (10 MB). Not every town is one of them: a municipality formed by merging
  villages (Stutensee, 25,000 people) exists only as an administrative record, and most British
  villages (Whiteley) and German town parts (Parsdorf) have no population figure at all.
- `admin1CodesASCII` and `admin2Codes`: the names of states, provinces and nations, and of
  counties and districts.
- `DE`: Germany's own export, for its districts (Kreise), which GeoNames keeps one level lower
  than other countries' counties.
- `GB`: the UK's own export, for England's council districts (Thanet, Castle Point, Cannock
  Chase…), which lie inside its counties: a fact looked up for a council district must reach
  the towns in it.
- `DE`, `GB` and `IE` also fill in what `cities1000` leaves out. A municipality with at least
  1,000 people joins the towns; smaller and unmeasured places go to `villages.csv.gz`, which
  `places.locate` reads only when a location names one outright. A village whose name is shared
  with a place far away, a region or an ordinary word is left out: an unknown place stays open,
  a wrong one would give a wrong journey.
- The postal-code exports `GB` and `IE` (`export/zip`): the UK's postcode districts ("CB22") and
  Ireland's Eircode routing keys ("T12"), with a point each, because some job sites give only a
  postcode as the place ("CB22 4QR"). Written to `postcodes.csv.gz`.
- `alternateNamesV2`: each place's and region's name in other languages, so "München" and
  "Munich", "Sachsen" and "Saxony" all work. This download is about 200 MB and is only read here,
  never shipped.

Usage:
    uv run python tools/update_places.py

GeoNames data is licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), so Jobcu
credits GeoNames in README.md and in each file's first line. Run this now and then to refresh it.
"""

import csv
import gzip
import io
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jobcu import places  # noqa: E402
from jobcu.countries import COUNTRIES  # noqa: E402
from jobcu.placenames import countries_in  # noqa: E402
from jobcu.text import normalise  # noqa: E402

DUMP = "https://download.geonames.org/export/dump"
POSTAL = "https://download.geonames.org/export/zip"
DATA = ROOT / "src" / "jobcu" / "data"
TARGET = DATA / "places.csv.gz"
VILLAGES = DATA / "villages.csv.gz"
REGIONS = DATA / "regions.csv.gz"
POSTCODES = DATA / "postcodes.csv.gz"
CREDIT = ("# Towns with at least 1,000 inhabitants in the countries Jobcu supports, with their "
          "names in the local languages. Data © GeoNames (geonames.org), licensed CC BY 4.0. "
          "Rebuilt with tools/update_places.py. Columns: names (separated by |),country,lat,lon,"
          "people,region,district,area")
VILLAGE_CREDIT = ("# Smaller places in Germany, the UK and Ireland, and places with no population "
                  "figure (people is 0), each with a name no other place far away shares. Data © "
                  "GeoNames (geonames.org), licensed CC BY 4.0. Rebuilt with "
                  "tools/update_places.py. Columns: name,country,lat,lon,people,region,district,"
                  "area")
POSTCODE_CREDIT = ("# The UK's postcode districts and Ireland's Eircode routing keys, with the "
                   "middle of the places each covers. Data © GeoNames (geonames.org), licensed "
                   "CC BY 4.0. Rebuilt with tools/update_places.py. Columns: code,country,lat,"
                   "lon")
REGION_CREDIT = ("# The states, provinces, counties and districts of the countries Jobcu supports, "
                 "with their names in the local languages. Data © GeoNames (geonames.org), "
                 "licensed CC BY 4.0. Rebuilt with tools/update_places.py. Columns: code,level,"
                 "country,names (separated by |)")
MAX_NAMES = 6
MAX_REGION_NAMES = 8
# Countries whose districts GeoNames keeps at its third level: there the second level is a unit
# nobody uses for facts (Germany's Regierungsbezirke).
THIRD_LEVEL_DISTRICTS = ("DE",)
# Countries whose third level holds council districts inside the counties of the second level;
# they become a town's "area".
THIRD_LEVEL_AREAS = ("GB",)
POSTCODE_COUNTRIES = ("GB", "IE")
# Countries whose own export fills in the towns and villages `cities1000` leaves out.
GAP_COUNTRIES = ("DE", "GB", "IE")
MUNICIPALITY = "ADM4"
TOWN_PEOPLE = 1000
# GeoNames' codes for inhabited places. Localities, farms and historical, abandoned or destroyed
# places stay out.
VILLAGE_CODES = ("PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLA5", "PPLS")
# A part of a town ("Surrey Quays") counts only when no village has its name.
TOWN_PART = "PPLX"
# A locality is no village of its own, but a village far from one of its name may not be the place
# meant ("Parkmore" is an estate in Galway and a village in Carlow).
LOCALITY = "PPLL"
# Records of one name this close are one place ("Effingham" has two, 3 km apart).
SAME_PLACE_KM = 10
SHORTEST_VILLAGE_NAME = 4
# A municipality this many times bigger than a listed town of its name, far away, takes the name
# over (Schenefeld near Hamburg, 19,900 people, from Schenefeld in Steinburg, 2,500).
CLEARLY_BIGGER = 3
# Municipalities named like an ordinary word join the villages, so that they aren't found inside
# other words ("Mercedes-Benz Group" is not in Benz). Checked by eye against the 800 added in
# 2026-10.
ORDINARY_WORDS = frozenset(normalise(word) for word in (
    "Aland", "Anger", "Benz", "Berne", "Buch", "Finne", "Grafschaft", "Huy", "Lotte", "March",
    "Marne", "Meine", "Moos", "Müssen", "Perl", "Ringe", "Seeland", "Stapel", "Theres", "Vogtei",
    "Wald",
))
# Villages named like what a location says when it names no town: the kind of place, a direction
# or a landscape. Checked by eye against the villages' names that are also dictionary words, in
# 2026-10; some have no village today but could after a rebuild.
GENERIC_NAMES = frozenset(normalise(word) for word in (
    "Abbey", "Airport", "All Saints", "Anywhere", "Bahnhof", "Bank", "Border", "Borough",
    "Bundesweit", "Büro", "Campus", "Centre", "Chapel", "City", "Coast", "College",
    "Deutschlandweit", "East Side", "Factory", "Field", "Flexible", "Flughafen", "Forest",
    "Global", "Hafen", "Harbour", "Head Office", "Highlands", "Home", "Hospital", "Hybrid",
    "International", "Junction", "Lane", "Lowlands", "Main", "Many", "Midlands", "Mitte", "Mobile",
    "More", "Mountain", "Multiple", "Nationwide", "Nord", "North Side", "Office", "Online",
    "Other", "Others", "Park", "Peak", "Point", "Port", "Quarter", "Region", "Remote", "Road",
    "Sector", "Several", "Shop", "Shore", "Site", "Some", "South Side", "Square", "Station",
    "Street", "Süd", "The Town", "Tower", "Town", "University", "Unknown", "Various", "Virtual",
    "Water", "Werk", "West Side", "Worldwide", "Zentrum",
    "Bodensee", "Lausitz", "Mosel", "Odenwald", "Saar", "Sauerland", "Thames", "Westerwald",
))
# How GeoNames dresses up a municipality's name: "St. Wendel, Kreisstadt", "Bautzen/Budyšin",
# "Illingen / Saar", "Selters (Taunus)", "Neumarkt i.d.OPf.", "Garching b.München",
# "Mühldorf a. Inn", "Bad Homburg v.d. Höhe", "Stadt Aue-Bad Schlema", "Henstedt-Ulzburg
# Municipality". "Markt" is dressing in "Markt Eckental", but the name in "Markt Schwaben, Markt".
_DRESSED_NAME = re.compile(
    r"^Stadt\s+|^Markt\s+(?=[^,]*$)|\s+Municipality$|\s*[,/(].*$|\s+[abiv]\.\s*(?:d\.\s*)?\S.*$")


def download(client: httpx.Client, name: str, base: str = DUMP) -> Path:
    target = Path(tempfile.gettempdir()) / (name if base == DUMP else f"postal-{name}")
    print(f"Downloading {base}/{name} …")
    with client.stream("GET", f"{base}/{name}") as response, target.open("wb") as file:
        response.raise_for_status()
        for chunk in response.iter_bytes(1 << 20):
            file.write(chunk)
    print(f"  {target.stat().st_size / 1e6:.0f} MB")
    return target


def rows_of(archive: Path, member: str):
    # GeoNames' files have no quoting: a name starting with a quote mark is just that.
    with zipfile.ZipFile(archive) as zipped, zipped.open(member) as raw:
        yield from csv.reader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t",
                              quoting=csv.QUOTE_NONE)


def rows_of_text(path: Path):
    with path.open(encoding="utf-8") as file:
        yield from csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE)


def main() -> int:
    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        cities = download(client, "cities1000.zip")
        admin1 = download(client, "admin1CodesASCII.txt")
        admin2 = download(client, "admin2Codes.txt")
        exports = {country: download(client, f"{country}.zip")
                   for country in dict.fromkeys((*THIRD_LEVEL_DISTRICTS, *THIRD_LEVEL_AREAS,
                                                 *GAP_COUNTRIES))}
        postal = {country: download(client, f"{country}.zip", POSTAL)
                  for country in POSTCODE_COUNTRIES}
        alternates = download(client, "alternateNamesV2.zip")

    # Regions: code → [level, country, names]; GeoNames id → code, for their other names.
    regions: dict[str, list] = {}
    region_ids: dict[str, str] = {}
    for line in rows_of_text(admin1):
        country = line[0].split(".")[0]
        if country in COUNTRIES:
            regions[line[0]] = ["region", country, [line[1], line[2]]]
            region_ids[line[3]] = line[0]
    for line in rows_of_text(admin2):
        country = line[0].split(".")[0]
        if country in COUNTRIES and country not in THIRD_LEVEL_DISTRICTS:
            regions[line[0]] = ["district", country, [line[1], line[2]]]
            region_ids[line[3]] = line[0]
    for country in (*THIRD_LEVEL_DISTRICTS, *THIRD_LEVEL_AREAS):
        for line in rows_of(exports[country], f"{country}.txt"):
            if line[7] != "ADM3" or not line[12]:
                continue
            if country in THIRD_LEVEL_DISTRICTS:
                code, level = f"{country}.K.{line[12]}", "district"
            else:
                code, level = _area_code(country, line[10], line[11], line[12]), "area"
            regions[code] = [level, country, [line[1], line[2]]]
            region_ids[line[0]] = code

    towns: dict[str, list] = {}
    languages: dict[str, set[str]] = {}
    # Which listed towns lie in which municipality, by the ids of both.
    in_municipality: dict[tuple[str, str], list[str]] = {}
    for line in rows_of(cities, "cities1000.txt"):
        country = line[8]
        if country not in COUNTRIES:
            continue
        names = [line[1]] + ([line[2]] if line[2] and line[2] != line[1] else [])
        towns[line[0]] = [names, *_place_columns(line, country, regions)]
        languages[line[0]] = {"en", *COUNTRIES[country].ad_languages}
        if line[13]:
            in_municipality.setdefault((country, line[13]), []).append(line[0])
    for code, (_, country, _) in regions.items():
        languages[code] = {"en", *COUNTRIES[country].ad_languages}

    extra: dict[str, set[str]] = {}
    for row in rows_of(alternates, "alternateNamesV2.txt"):
        if len(row) < 5:
            continue
        key = row[1] if row[1] in towns else region_ids.get(row[1])
        if key is None:
            continue
        colloquial = len(row) > 6 and row[6] == "1"
        historic = len(row) > 7 and row[7] == "1"
        if colloquial or historic or row[2] not in languages[key]:
            continue
        extra.setdefault(key, set()).add(row[3])

    written = {}
    for town_id, (names, country, latitude, longitude, people, *codes) in towns.items():
        all_names = dict.fromkeys([*names, *sorted(extra.get(town_id, ()))])
        written[town_id] = ["|".join(list(all_names)[:MAX_NAMES]), country, latitude, longitude,
                            people, *codes]
    records = {country: list(rows_of(exports[country], f"{country}.txt"))
               for country in GAP_COUNTRIES}
    for country in GAP_COUNTRIES:
        rows_in = {code: [written[town_id] for town_id in ids]
                   for (where, code), ids in in_municipality.items() if where == country}
        left_out = add_municipalities(records[country], country, written, rows_in, regions)
        print(f"  {country}: municipalities left out because a town of about their size has "
              f"their name: {', '.join(left_out) or 'none'}")
    written = sorted(written.values(), key=lambda row: (row[1], row[0]))
    _write(TARGET, CREDIT, written)

    used = {code for row in written for code in row[5:]}
    region_rows = []
    region_names: dict[str, set[str]] = {country: set() for country in GAP_COUNTRIES}
    for code, (level, country, names) in regions.items():
        if code not in used:
            continue
        all_names = dict.fromkeys([*names, *sorted(extra.get(code, ()))])
        region_rows.append([code, level, country,
                            "|".join(name for name in list(all_names)[:MAX_REGION_NAMES] if name)])
        if country in region_names:
            region_names[country] |= {key for name in all_names
                                      for key in (normalise(name), places._region_key(name))}
    region_rows.sort()
    _write(REGIONS, REGION_CREDIT, region_rows)

    village_rows = []
    for country in GAP_COUNTRIES:
        village_rows += villages_of(records[country], country, written, region_names[country],
                                    regions)
    village_rows.sort(key=lambda row: (row[1], row[0]))
    _write(VILLAGES, VILLAGE_CREDIT, village_rows)

    postcode_rows = []
    for country, archive in postal.items():
        points: dict[str, list[tuple[float, float]]] = {}
        for line in rows_of(archive, f"{country}.txt"):
            if line[9] and line[10]:
                points.setdefault(line[1].upper(), []).append((float(line[9]), float(line[10])))
        for code, spots in sorted(points.items()):
            latitude = sum(spot[0] for spot in spots) / len(spots)
            longitude = sum(spot[1] for spot in spots) / len(spots)
            postcode_rows.append([code, country, f"{latitude:.3f}", f"{longitude:.3f}"])
    _write(POSTCODES, POSTCODE_CREDIT, postcode_rows)
    print(f"{len(written):,} towns in {len({row[1] for row in written})} countries → "
          f"{TARGET.relative_to(ROOT)} ({TARGET.stat().st_size / 1024:.0f} KB); "
          f"{len(village_rows):,} villages → {VILLAGES.relative_to(ROOT)} "
          f"({VILLAGES.stat().st_size / 1024:.0f} KB); "
          f"{len(region_rows):,} regions → {REGIONS.relative_to(ROOT)} "
          f"({REGIONS.stat().st_size / 1024:.0f} KB); {len(postcode_rows):,} postcodes → "
          f"{POSTCODES.relative_to(ROOT)} ({POSTCODES.stat().st_size / 1024:.0f} KB)")
    return 0


def _area_code(country: str, admin1: str, admin2: str, admin3: str) -> str:
    return f"{country}.{admin1}.{admin2}.{admin3}"


def _place_columns(line: list[str], country: str, regions: dict) -> list[str]:
    """A GeoNames record's country, coordinates, population and region codes, as the town and
    village lists write them."""
    region = f"{country}.{line[10]}"
    if country in THIRD_LEVEL_DISTRICTS:
        district = f"{country}.K.{line[12]}" if line[12] else ""
    else:
        district = f"{country}.{line[10]}.{line[11]}" if line[11] else ""
    area = _area_code(country, line[10], line[11], line[12]) if line[12] else ""
    return [country, f"{float(line[4]):.3f}", f"{float(line[5]):.3f}", line[14] or "0",
            region if region in regions else "", district if district in regions else "",
            area if area in regions else ""]


def _people(line: list[str]) -> int:
    return int(line[14] or 0)


def plain_name(name: str) -> str:
    """A municipality's name as people write it ("St. Wendel, Kreisstadt" is St. Wendel)."""
    return _DRESSED_NAME.sub("", name).strip() or name


def _comparable(name: str) -> str:
    """For telling whether two spellings name one place: "St." and "Sankt" are the same word."""
    return re.sub(r"^sankt\b", "st", normalise(plain_name(name)))


def _names_one_place(name: str, row: list[str], same_municipality: bool, line: list[str]) -> bool:
    """Whether a municipality is a town already listed: of the same name close by, or inside
    the municipality with a name that contains it ("Schwandorf in Bayern", "Weinstadt-Endersbach",
    "Lutherstadt Wittenberg")."""
    close = places.km(float(line[4]), float(line[5]), float(row[2]), float(row[3])) <= SAME_PLACE_KM
    wanted = _comparable(name)
    for spelling in row[0].split("|"):
        listed = _comparable(spelling)
        if listed == wanted and (close or same_municipality):
            return True
        if same_municipality and (f" {wanted} " in f" {listed} " or f" {listed} " in f" {wanted} "):
            return True
    return False


def _names_index(rows) -> dict[tuple[str, str], list[list[str]]]:
    index: dict[tuple[str, str], list[list[str]]] = {}
    for row in rows:
        for key in places.lookup_names(row[0].split("|")):
            index.setdefault((row[1], key), []).append(row)
    return index


def add_municipalities(records: list[list[str]], country: str, written: dict[str, list[str]],
                       rows_in: dict[str, list[list[str]]], regions: dict) -> list[str]:
    """Adds to `written` the municipalities of at least TOWN_PEOPLE that aren't listed, and to
    the towns they duplicate the name people use for them ("Schwandorf" for "Schwandorf in
    Bayern").

    The biggest town of a name wins, so a municipality only somewhat bigger than a listed town of
    its name, far away, is left out (and returned): Neuried near Munich must not become the one in
    Baden, 270 km away. The same goes for a name that differs by its accents: names are compared
    without them, and Büchen must not become Buchen."""
    index = _names_index(written.values())
    left_out = []
    municipalities = [line for line in records if line[7] == MUNICIPALITY
                      and _people(line) >= TOWN_PEOPLE
                      and normalise(plain_name(line[1])) not in ORDINARY_WORDS]
    for line in sorted(municipalities, key=lambda line: (-_people(line), int(line[0]))):
        name = plain_name(line[1])
        named_so = index.get((country, normalise(name)), [])
        same = next((row for row in rows_in.get(line[13], [])
                     if _names_one_place(name, row, True, line)), None) or (
            next((row for row in named_so if _names_one_place(name, row, False, line)), None))
        people = int(same[4]) or _people(line) if same else _people(line)
        # The official name is worth keeping unless all it adds is a word after a comma.
        spellings = list(dict.fromkeys((name, line[1]) if "," not in line[1] else (name,)))
        keys = places.lookup_names(spellings)
        if any(_takes_name_over(name, people, index[country, key]) for key in keys
               if (country, key) in index and same not in index[country, key]):
            if not same:
                left_out.append(name)
            continue
        if same:
            same[4] = str(people)
            if not all(same in index.get((country, key), ()) for key in keys):
                same[0] += "|" + "|".join(spellings)
        else:
            same = ["|".join(spellings), *_place_columns(line, country, regions)]
            written[f"{MUNICIPALITY}.{line[0]}"] = same
        for key in keys:
            if same not in index.get((country, key), ()):
                index.setdefault((country, key), []).append(same)
    return left_out


def _takes_name_over(name: str, people: int, rows: list[list[str]]) -> bool:
    """Whether a town of this size would wrongly become what a name stands for."""
    biggest = max(rows, key=lambda row: int(row[4]))
    if people <= int(biggest[4]):
        return False
    spelled_alike = biggest[0].split("|")[0].casefold().startswith(name.casefold())
    return not spelled_alike or people < CLEARLY_BIGGER * int(biggest[4])


def _generic(name: str, country: str, region_names: set[str]) -> bool:
    """Whether a name says something other than a village when a job's location gives it."""
    key = normalise(name)
    return (len(key) < SHORTEST_VILLAGE_NAME or key in GENERIC_NAMES or key in region_names
            or key in places._REGIONS or bool(countries_in(name) - {country}))


def villages_of(records: list[list[str]], country: str, towns: list[list[str]],
                region_names: set[str], regions: dict) -> list[list[str]]:
    """The inhabited places of a country that aren't in the town list, one row per name. A name
    several places far apart share is left out: it doesn't say which of them a job is in."""
    known = {key for row in towns if row[1] == country
             for key in places.lookup_names(row[0].split("|"))}
    municipalities = {(normalise(plain_name(line[1])), line[13]): line for line in records
                      if line[7] == MUNICIPALITY}
    by_name: dict[str, list[list[str]]] = {}
    parts: dict[str, list[list[str]]] = {}
    localities: dict[str, list[list[str]]] = {}
    for line in records:
        is_municipality = line[7] == MUNICIPALITY and _people(line) > 0
        if not is_municipality and line[7] not in (*VILLAGE_CODES, TOWN_PART, LOCALITY):
            continue
        name = plain_name(line[1]) if is_municipality else line[1]
        key = normalise(name)
        if key in known or _generic(name, country, region_names):
            continue
        group = {TOWN_PART: parts, LOCALITY: localities}.get(line[7], by_name)
        group.setdefault(key, []).append(line)
    rows = []
    for key, lines in {**parts, **by_name}.items():
        others = localities.get(key, [])
        if any(places.km(float(a[4]), float(a[5]), float(b[4]), float(b[5])) > SAME_PLACE_KM
               for a in lines for b in (*lines, *others)):
            continue
        # The inhabited place of a municipality of its name, whose count it can take over.
        best = min(lines, key=lambda line: (line[7] == MUNICIPALITY,
                                            (key, line[13]) not in municipalities,
                                            -_people(line), int(line[0])))
        people = max(_people(line) for line in lines)
        if not people and (key, best[13]) in municipalities:
            people = _people(municipalities[key, best[13]])
        name = plain_name(best[1]) if best[7] == MUNICIPALITY else best[1]
        columns = _place_columns(best, country, regions)
        columns[3] = str(people)
        rows.append([name, *columns])
    return rows


def _write(target: Path, credit: str, rows: list[list[str]]) -> None:
    buffer = io.StringIO()
    buffer.write(credit + "\n")
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    target.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(target, "wb", compresslevel=9, mtime=0) as out:
        out.write(buffer.getvalue().encode("utf-8"))


if __name__ == "__main__":
    sys.exit(main())
