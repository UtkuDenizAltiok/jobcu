"""Rebuilds the official populations of German towns (src/jobcu/data/official_people.csv).

GeoNames' figures, which the town list ships (update_places.py), are of mixed age: it had
Braunschweig at 244,715 people and Kiel at 252,668, so for "a city with at least 0.3% of the
country's people" (about 250,000) Kiel counted and Braunschweig didn't, while the official figures
for 31.12.2024 are 252,962 and 252,668. Frankfurt am Main had 650,000 instead of 756,021.

The Federal Statistical Office's list of every German town with town rights (Destatis,
Gemeindeverzeichnis, "Städte nach Fläche, Bevölkerung und Bevölkerungsdichte", on the basis of
the 2022 census) gives each town's official population and its official key. The first five
digits of the key are the town's district, which the town list also records ("DE.K.03101" is
Braunschweig), so each figure reaches exactly one town. The table may be copied and passed on
with its source named (its cover sheet).

Usage:
    uv run python tools/update_official_people.py            download the table and save
    uv run python tools/update_official_people.py table.xlsx  use a downloaded copy
"""

import csv
import io
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jobcu.sources.http import USER_AGENT  # noqa: E402

TABLE = ("https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/"
         "Administrativ/05-staedte.xlsx?__blob=publicationFile")
OUT = ROOT / "src" / "jobcu" / "data" / "official_people.csv"
SHEET = "Städte"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
# The table's own words after a town's name: "Kiel, Landeshauptstadt", "Bremen, Stadt".
_TITLE = re.compile(r",\s*(?:[\w\s.-]*stadt|Stadt|Hansestadt|Universitätsstadt|[\w\s.-]+)$")


def rows(content: bytes, sheet: str = SHEET) -> list[list[str]]:
    """The cells of one sheet of an .xlsx file, as text (standard library only)."""
    book = zipfile.ZipFile(io.BytesIO(content))
    shared = []
    if "xl/sharedStrings.xml" in book.namelist():
        root = ElementTree.fromstring(book.read("xl/sharedStrings.xml"))
        shared = ["".join(t.text or "" for t in item.iter(f"{{{NS['m']}}}t"))
                  for item in root.findall("m:si", NS)]
    workbook = ElementTree.fromstring(book.read("xl/workbook.xml"))
    links = ElementTree.fromstring(book.read("xl/_rels/workbook.xml.rels"))
    targets = {link.get("Id"): link.get("Target") for link in links}
    target = next(targets[node.get(f"{{{NS['r']}}}id")]
                  for node in workbook.find("m:sheets", NS) if node.get("name") == sheet)
    data = ElementTree.fromstring(book.read("xl/" + target.removeprefix("/xl/")))
    table = []
    for row in data.iter(f"{{{NS['m']}}}row"):
        cells: dict[int, str] = {}
        for cell in row.findall("m:c", NS):
            column = 0
            for char in re.match(r"[A-Z]+", cell.get("r")).group():
                column = column * 26 + ord(char) - 64
            value = cell.find("m:v", NS)
            inline = cell.find("m:is", NS)
            if cell.get("t") == "s" and value is not None:
                text = shared[int(value.text)]
            elif inline is not None:
                text = "".join(t.text or "" for t in inline.iter(f"{{{NS['m']}}}t"))
            else:
                text = value.text if value is not None else ""
            cells[column - 1] = (text or "").strip()
        table.append([cells.get(i, "") for i in range(max(cells, default=-1) + 1)])
    return table


def official_towns(table: list[list[str]]) -> list[tuple[str, str, int]]:
    """(district code, town name, people) for every town the table lists."""
    towns = []
    for row in table:
        if len(row) < 6 or not re.fullmatch(r"\d{12}", row[1]) or not row[5]:
            continue
        name = _TITLE.sub("", row[2]).strip()
        towns.append((f"DE.K.{row[1][:5]}", name, int(float(row[5]))))
    return towns


def main() -> None:
    if len(sys.argv) > 1:
        content = Path(sys.argv[1]).read_bytes()
    else:
        import httpx

        response = httpx.get(TABLE, headers={"User-Agent": USER_AGENT}, timeout=60,
                             follow_redirects=True)
        response.raise_for_status()
        content = response.content
    table = rows(content)
    as_of = next((found.group() for line in table[:3] for cell in line
                  if (found := re.search(r"\d{2}\.\d{2}\.\d{4}", cell))), "")
    towns = official_towns(table)
    with OUT.open("w", encoding="utf-8", newline="") as file:
        file.write(f"# Official populations of German towns with town rights on {as_of}\n"
                   "# (2022 census basis). Source: Statistisches Bundesamt (Destatis),\n"
                   "# Gemeindeverzeichnis; copying and passing on with the source named is\n"
                   "# permitted. Rebuilt by tools/update_official_people.py.\n"
                   "# Columns: district, town, people.\n")
        writer = csv.writer(file, lineterminator="\n")
        for district, name, people in sorted(towns, key=lambda town: -town[2]):
            writer.writerow([district, name, people])
    print(f"Saved {len(towns)} towns to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
