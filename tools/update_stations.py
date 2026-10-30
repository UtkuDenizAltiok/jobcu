"""Rebuilds the list of main railway stations Jobcu ships (src/jobcu/data/stations.csv).

Google Maps' journey to a city's centre includes the local trip from the station, and a person who
lives in the city can live by the station. Measured on the places of the owner's search 12
(2026-10-30), a main station was up to about 35 minutes nearer than the centre (Stevenage to
London: 55 minutes to the centre, 38 to King's Cross), which decides jobs under a 50-minute limit.

GeoNames has no field saying which station is a city's main one, so the names are chosen here, for
the biggest towns of the owner's countries (at least 0.3% of the country's people). A town not
listed is measured to its centre, as before. Irish stations appear only where GeoNames has precise
coordinates. A station must lie within the town's reach (places.reach_km), which is why Bristol
Parkway is not listed.

Usage:
    uv run python tools/update_stations.py

GeoNames data is licensed CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), credited in
README.md and in the file's first line.
"""

import csv
import io
import sys
import tempfile
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jobcu import places  # noqa: E402

DUMP = "https://download.geonames.org/export/dump"
TARGET = ROOT / "src" / "jobcu" / "data" / "stations.csv"
STATION_CODES = {"RSTN", "RSTP"}

# By town name in Jobcu's town list, the names as GeoNames writes them.
MAIN_STATIONS = {
    "DE": {
        "Berlin": ["Berlin Hauptbahnhof", "Berlin Südkreuz", "Berlin Gesundbrunnen (S)",
                   "Berlin Ostbahnhof", "Bahnhof Berlin Ostkreuz"],
        "Hamburg": ["Hamburg Central Station", "Bahnhof Hamburg-Altona", "Hamburg-Harburg"],
        "Munich": ["München Hauptbahnhof", "München-Ostbahnhof", "Bahnhof München-Pasing"],
        "Köln": ["Köln Hauptbahnhof", "Köln Messe/Deutz station"],
        "Frankfurt am Main": ["Frankfurt Hauptbahnhof", "Frankfurt South Station"],
        "Düsseldorf": ["Düsseldorf Hauptbahnhof"],
        "Stuttgart": ["Stuttgart Hauptbahnhof"],
        "Essen": ["Essen Hauptbahnhof"],
        "Dortmund": ["Dortmund Hauptbahnhof"],
        "Bremen": ["Hauptbahnhof Bremen"],
        "Nuremberg": ["Nuremberg Central Station"],
        "Hannover": ["Hannover Hauptbahnhof"],
        "Duisburg": ["Duisburg Hauptbahnhof"],
        "Bochum": ["Bochum Hbf"],
        "Wuppertal": ["Wuppertal Hauptbahnhof"],
        "Bielefeld": ["Bielefeld Railway Station"],
        "Bonn": ["Bonn Central Station"],
        "Münster": ["Münster (Westfalen) Hbf"],
        "Mannheim": ["Mannheim Hauptbahnhof"],
        "Augsburg": ["Augsburg Hauptbahnhof"],
        "Wiesbaden": ["Wiesbaden Central Station"],
        "Karlsruhe": ["Karlsruhe Hauptbahnhof"],
        "Aachen": ["Aachen Hauptbahnhof"],
        "Mönchengladbach": ["Mönchengladbach Hbf"],
        "Kiel": ["Hauptbahnhof Kiel"],
    },
    "GB": {
        "London": ["London Kings Cross", "St Pancras International Railway Station",
                   "Euston railway station", "Marylebone Railway Station",
                   "London Paddington station", "Waterloo Railway Station",
                   "London Victoria station", "London Bridge Railway Station",
                   "Liverpool Street Railway Station", "Fenchurch Street Railway Station",
                   "Stratford Mainline Station", "Clapham Junction Station"],
        "Birmingham": ["Birmingham New Street Railway Station",
                       "Birmingham Moor Street Railway Station"],
        "Glasgow": ["Glasgow Central Station", "Glasgow Queen Street Railway Station"],
        "Manchester": ["Manchester Piccadilly Railway Station", "Manchester Victoria"],
        # GeoNames calls today's Sheffield station by the name of the one closed in 1970.
        "Sheffield": ["Sheffield Victoria"],
        "Leeds": ["Leeds Railway Station"],
        "Edinburgh": ["Edinburgh Waverley Railway Station", "Haymarket Railway Station"],
        "Liverpool": ["Liverpool Lime Street Railway Station"],
        "Bristol": ["Bristol Temple Meads Railway Station"],
        "Cardiff": ["Cardiff Central Railway Station"],
        "Leicester": ["Leicester Railway Station"],
        "Bradford": ["Bradford Interchange", "Bradford Forster Square Railway Station"],
        # Great Victoria Street's point is beside Belfast Grand Central, which replaced it.
        "Belfast": ["Great Victoria Street Railway Station", "Belfast Central railway station"],
        "Reading": ["Reading Railway Station"],
        "Brighton": ["Brighton Railway Station"],
        "Milton Keynes": ["Milton Keynes Central Railway Station"],
        "Luton": ["Luton Railway Station", "Luton Airport Parkway Railway Station"],
    },
    "IE": {
        "Dublin": ["Bahnhof Dublin Heuston", "Dublin Connolly railway station"],
        "Galway": ["Galway Ceannt"],
    },
}


def stations_in(country: str, folder: Path) -> dict[str, list[tuple[float, float]]]:
    """Every station in GeoNames' export of one country, by name."""
    archive = folder / f"{country}.zip"
    with httpx.stream("GET", f"{DUMP}/{country}.zip", timeout=300) as reply:
        reply.raise_for_status()
        with archive.open("wb") as file:
            for chunk in reply.iter_bytes():
                file.write(chunk)
    found: dict[str, list[tuple[float, float]]] = {}
    with zipfile.ZipFile(archive) as files, files.open(f"{country}.txt") as raw:
        for line in io.TextIOWrapper(raw, encoding="utf-8"):
            cells = line.split("\t")
            if cells[7] in STATION_CODES:
                found.setdefault(cells[1], []).append((float(cells[4]), float(cells[5])))
    return found


def main() -> None:
    rows = []
    with tempfile.TemporaryDirectory() as folder:
        for country, towns in MAIN_STATIONS.items():
            found = stations_in(country, Path(folder))
            for name, stations in towns.items():
                town = places.find(name, country)
                if town is None or town.name != name:
                    raise SystemExit(f"{name} is not a town name in the list ({country})")
                for station in stations:
                    near = [point for point in found.get(station, []) if places.km(
                        town.latitude, town.longitude, *point) <= places.reach_km(town)]
                    if len(near) != 1:
                        raise SystemExit(f"{station}: {len(near)} matches in {name}")
                    rows.append([country, name, station, *near[0]])
    with TARGET.open("w", encoding="utf-8", newline="") as file:
        file.write("# Main railway stations. Coordinates from GeoNames (geonames.org), CC BY 4.0. "
                   "Built by tools/update_stations.py.\n")
        csv.writer(file, lineterminator="\n").writerows(rows)
    print(f"{len(rows)} stations in {TARGET}")


if __name__ == "__main__":
    main()
