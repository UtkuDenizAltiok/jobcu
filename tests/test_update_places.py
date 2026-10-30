"""tools/update_places.py: what it adds to GeoNames' `cities1000`, on made-up records."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("update_places", ROOT / "tools" / "update_places.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

REGIONS = {"XX.01": 1, "XX.01.1": 1}


def record(geoname_id, name, code="PPL", people=0, latitude=50.0, longitude=8.0, municipality="1"):
    """One line of a GeoNames country export, with the columns the tool reads."""
    line = [""] * 19
    line[0], line[1], line[4], line[5] = str(geoname_id), name, str(latitude), str(longitude)
    line[6], line[7] = ("A" if code.startswith("ADM") else "P"), code
    line[10], line[11], line[13], line[14] = "01", "1", municipality, str(people)
    return line


def row(names, people, latitude=50.0, longitude=8.0):
    return [names, "XX", f"{latitude:.3f}", f"{longitude:.3f}", str(people), "XX.01", "XX.01.1", ""]


def municipalities(records, listed=(), rows_in=None):
    written = {str(number): listed_row for number, listed_row in enumerate(listed)}
    left_out = tool.add_municipalities(records, "XX", written, rows_in or {}, REGIONS)
    return written, left_out


def villages(records, towns=(), region_names=frozenset()):
    return {found[0]: found
            for found in tool.villages_of(records, "XX", list(towns), set(region_names), REGIONS)}


@pytest.mark.parametrize("official,plain", [
    ("Stutensee", "Stutensee"),
    ("St. Wendel, Kreisstadt", "St. Wendel"),
    ("Ipsheim, Markt", "Ipsheim"),
    ("Markt Schwaben, Markt", "Markt Schwaben"),
    ("Markt Eckental", "Eckental"),
    ("Stadt Aue-Bad Schlema", "Aue-Bad Schlema"),
    ("Henstedt-Ulzburg Municipality", "Henstedt-Ulzburg"),
    ("Bautzen/Budyšin", "Bautzen"),
    ("Illingen / Saar", "Illingen"),
    ("Selters (Taunus)", "Selters"),
    ("Neumarkt i.d.OPf.", "Neumarkt"),
    ("Garching b.München", "Garching"),
    ("Mühldorf a. Inn", "Mühldorf"),
    ("Bad Homburg v.d. Höhe", "Bad Homburg"),
    ("Castrop-Rauxel", "Castrop-Rauxel"),
])
def test_a_municipality_goes_by_the_name_people_use(official, plain):
    assert tool.plain_name(official) == plain


def test_a_municipality_nobody_listed_becomes_a_town():
    written, left_out = municipalities([record(1, "Oakmere", "ADM4", 25_000, 49.1, 8.5)])
    assert left_out == []
    (added,) = written.values()
    assert added == ["Oakmere", "XX", "49.100", "8.500", "25000", "XX.01", "XX.01.1", ""]


def test_small_municipalities_and_ordinary_words_do_not_become_towns():
    written, _ = municipalities([record(1, "Oakmere", "ADM4", 999),
                                 record(2, "March", "ADM4", 9000)])
    assert written == {}


def test_a_municipality_listed_under_its_name_is_not_added_again():
    town = row("Oakmere", 24_000)
    written, _ = municipalities([record(1, "Oakmere", "ADM4", 25_000, 50.01, 8.01)], [town])
    assert list(written.values()) == [["Oakmere", *town[1:]]]
    # Nor its namesake 5 km away with official dressing.
    town = row("Oakmere", 24_000)
    written, _ = municipalities([record(1, "Oakmere, Stadt", "ADM4", 25_000, 50.04, 8.0)], [town])
    assert len(written) == 1 and town[0] == "Oakmere"


def test_a_short_name_joins_the_town_inside_the_municipality():
    town = row("Oakmere in Fieldshire", 24_000)
    written, _ = municipalities([record(1, "Oakmere", "ADM4", 25_000, municipality="77")], [town],
                                {"77": [town]})
    assert len(written) == 1 and town[0] == "Oakmere in Fieldshire|Oakmere"
    assert town[4] == "24000"  # the town's own count stays
    # "St." and "Sankt" are one word, whichever GeoNames used where.
    town = row("Sankt Oakmere", 24_000)
    written, _ = municipalities([record(1, "St. Oakmere", "ADM4", 25_000, municipality="77")],
                                [town], {"77": [town]})
    assert len(written) == 1
    # A different name in the same municipality is a different place.
    town = row("Elmfield", 11_000)
    written, _ = municipalities([record(1, "Oakmere", "ADM4", 25_000, municipality="77")], [town],
                                {"77": [town]})
    assert len(written) == 2


def test_a_town_with_no_count_takes_its_municipalitys():
    town = row("Oakmere", 0)
    municipalities([record(1, "Oakmere", "ADM4", 25_000)], [town])
    assert town[4] == "25000"


def test_a_bigger_namesake_far_away_only_takes_over_when_clearly_bigger():
    far = {"latitude": 53.0, "longitude": 13.0}
    written, left_out = municipalities([record(1, "Oakmere", "ADM4", 9000, **far)],
                                       [row("Oakmere", 7000)])
    assert left_out == ["Oakmere"] and len(written) == 1
    written, left_out = municipalities([record(1, "Oakmere", "ADM4", 21_000, **far)],
                                       [row("Oakmere", 7000)])
    assert left_out == [] and len(written) == 2
    # Smaller ones are harmless: the biggest of a name still wins.
    written, left_out = municipalities([record(1, "Oakmere", "ADM4", 2000, **far)],
                                       [row("Oakmere", 7000)])
    assert left_out == [] and len(written) == 2
    # Names are compared without accents, so Büchen must stay itself whatever Buchen's size.
    written, left_out = municipalities([record(1, "Oakmere", "ADM4", 21_000, **far)],
                                       [row("Oäkmere|Oakmere", 7000)])
    assert left_out == ["Oakmere"] and len(written) == 1


def test_a_village_gets_one_row_with_what_is_known_about_it():
    found = villages([record(1, "Oakmere", people=389)])
    assert found["Oakmere"] == ["Oakmere", "XX", "50.000", "8.000", "389", "XX.01", "XX.01.1", ""]
    # Two records 3 km apart, and the parish of the same name, are one place: the record in that
    # parish, with the parish's count.
    found = villages([record(1, "Oakmere", latitude=50.02, municipality="8"),
                      record(2, "Oakmere", latitude=50.0, municipality="9"),
                      record(3, "Oakmere", "ADM4", 400, latitude=50.01, municipality="9")])
    assert list(found) == ["Oakmere"]
    assert found["Oakmere"][2] == "50.000" and found["Oakmere"][4] == "400"
    # A municipality with no inhabited place of its name counts itself.
    assert villages([record(1, "Oakmere", "ADM4", 400)])["Oakmere"][4] == "400"
    assert "Oakmere" not in villages([record(1, "Oakmere", "ADM4", 0)])


def test_a_name_shared_with_a_place_far_away_says_too_little():
    assert not villages([record(1, "Oakmere"), record(2, "Oakmere", latitude=53.0)])
    # A locality far away counts against it too, but never makes a village of its own.
    assert not villages([record(1, "Oakmere"), record(2, "Oakmere", "PPLL", latitude=53.0)])
    assert not villages([record(1, "Oakmere", "PPLL")])


def test_a_part_of_a_town_counts_only_when_no_village_has_its_name():
    assert "Oak Quays" in villages([record(1, "Oak Quays", "PPLX")])
    found = villages([record(1, "Oakmere"), record(2, "Oakmere", "PPLX", latitude=53.0)])
    assert found["Oakmere"][2] == "50.000"


@pytest.mark.parametrize("code", ["PPLH", "PPLQ", "PPLW", "PPLF", "ADM3", "ADM4H", "ADMD"])
def test_other_kinds_of_record_are_no_villages(code):
    assert not villages([record(1, "Oakmere", code, 400)])


def test_names_that_say_something_else_are_no_villages():
    town = row("Oakmere bei Elmfield|Birchley", 2000)
    assert not villages([record(1, "Birchley")], [town])  # a listed town's name
    assert not villages([record(1, "Oakmere")], [town])  # and its short name
    assert not villages([record(1, "Oakshire")], region_names={"oakshire"})
    assert not villages([record(1, "Field")])  # what a location says when it names no town
    assert not villages([record(1, "Bayern")])  # a state
    assert not villages([record(1, "Toronto")])  # somewhere else
    assert not villages([record(1, "Aye")])  # too short to be sure of
