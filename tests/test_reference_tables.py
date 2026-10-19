import csv
import io

import pytest

from jobcu.reference_tables import calculate
from jobcu.settings import EvidenceCSV


def table(rows):
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue()


HEADER = ["City", "Event", "Group", "Member", "Count", "Other count"]


def selection(**changes):
    spec = {"group_by": ["Group"], "sum_columns": ["Count", "Other count"],
            "row_identity": ["Member"]}
    spec.update(changes)
    return EvidenceCSV(columns=HEADER, calculation=spec)


def test_all_rows_zeroes_multiple_measures_and_distinct_unnamed_members_survive():
    rows = [HEADER, ["Springford", "2030", "A", "one", "14", "3"],
            ["Springford", "2030", "A", "two", "0", "0"],
            ["Springford", "2030", "B", "three", "9", "1"],
            ["Springford", "2030", "", "same name", "3", "1"],
            ["Springford", "2030", "", "same name", "4", "1"]]
    records = list(csv.DictReader(io.StringIO(calculate(table(rows), selection()))))
    assert records[0] == {"kind": "group", "context:City": "Springford",
        "context:Event": "2030", "group:Group": "A", "sum:Count": "14", "sum:Other count": "3",
        "records": "2", "source_row": "", "identity:Member": ""}
    assert records[1]["sum:Count"] == "9" and records[1]["sum:Other count"] == "1"
    assert [r["source_row"] for r in records[2:4]] == ["4", "5"]
    assert [r["identity:Member"] for r in records[2:4]] == ["same name"] * 2
    assert records[-2]["kind"] == "unlabelled_total" and records[-2]["sum:Count"] == "7"
    assert records[-1]["kind"] == "total" and records[-1]["sum:Count"] == "30"
    assert records[-1]["sum:Other count"] == "6" and records[-1]["records"] == "5"


def test_signed_integers_and_quoted_group_names_keep_exact_arithmetic_and_identity():
    rows = [HEADER, ["Springford", "2030", 'Night, "staff"\nservice', "one", "+14", "-3"],
            ["Springford", "2030", 'Night, "staff"\nservice', "two", "-2", "03"]]
    records = list(csv.DictReader(io.StringIO(calculate(table(rows), selection()))))
    assert records[0]["group:Group"] == 'Night, "staff"\nservice'
    assert records[0]["sum:Count"] == "12" and records[0]["sum:Other count"] == "0"


@pytest.mark.parametrize("value", ["", "1.5", "NaN", "1,000", "one", "1_000"])
def test_missing_or_noninteger_cells_are_not_guessed_or_dropped(value):
    rows = [HEADER, ["Springford", "2030", "A", "one", "14", "1"],
            ["Springford", "2030", "A", "two", value, "1"]]
    assert calculate(table(rows), selection()) is None


@pytest.mark.parametrize("column,new_value", [("City", "Otherford"), ("Event", "2031")])
def test_a_varying_unreviewed_qualifier_cannot_be_lost_in_an_aggregate(column, new_value):
    first = ["Springford", "2030", "A", "one", "14", "1"]
    second = ["Springford", "2030", "A", "two", "0", "1"]
    second[HEADER.index(column)] = new_value
    assert calculate(table([HEADER, first, second]), selection()) is None


@pytest.mark.parametrize("body", ["", table([HEADER]), "City,City\nSpringford,Springford\n",
    table([HEADER, ["Springford", "2030", "A", "one", "14", "1"], ["missing"]]),
    'City,Event,Group,Member,Count,Other count\nSpringford,2030,"unfinished\n'])
def test_invalid_or_empty_tables_never_produce_partial_calculations(body):
    assert calculate(body, selection()) is None


def test_unknown_columns_are_rejected_and_an_unselected_calculation_is_not_invented():
    body = table([HEADER, ["Springford", "2030", "A", "one", "14", "1"]])
    assert calculate(body, selection(group_by=["Unknown"])) is None
    assert calculate(body, EvidenceCSV(columns=HEADER)) is None


def test_reviewed_collective_labels_are_not_misrepresented_as_one_shared_member():
    rows = [HEADER, ["Springford", "2030", "Unassigned", "one", "14", "1"],
            ["Springford", "2030", "Unassigned", "two", "2", "1"]]
    spec = selection(separate_values={"Group": ["Unassigned"]})
    records = list(csv.DictReader(io.StringIO(calculate(table(rows), spec))))
    assert [r["kind"] for r in records] == ["individual", "individual", "unlabelled_total", "total"]
    assert [r["identity:Member"] for r in records[:2]] == ["one", "two"]
    assert records[-1]["sum:Count"] == "16"
