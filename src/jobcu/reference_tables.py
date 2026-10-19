"""Exact reviewed table calculations; original source text remains separately verifiable."""

import csv
import io
import re

from jobcu.settings import EvidenceCSV


def calculate(text: str, selection: EvidenceCSV) -> str | None:
    spec = selection.calculation
    if spec is None:
        return None
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=selection.delimiter,
                            strict=True)
        header = next(reader, [])
        used = [*spec.group_by, *spec.sum_columns, *spec.row_identity]
        if (not header or len(set(header)) != len(header) or any(not h.strip() for h in header)
                or not set(used).issubset(header)):
            return None
        context_names = [name for name in header if name not in used]
        separate = {name: set(values) for name, values in spec.separate_values.items()}
        context = None
        groups = {}
        totals = {name: 0 for name in spec.sum_columns}
        unlabelled_totals = {name: 0 for name in spec.sum_columns}
        unlabelled_count = 0
        count = 0
        for row in reader:
            if len(row) != len(header):
                return None
            values = dict(zip(header, row, strict=True))
            current_context = {name: values[name] for name in context_names}
            if context is None:
                context = current_context
            elif current_context != context:
                # A varying qualifier must be grouped explicitly, never silently discarded.
                return None
            numbers = {}
            for name in spec.sum_columns:
                number = values[name].strip()
                if not re.fullmatch(r"[+-]?[0-9]+", number):
                    return None
                numbers[name] = int(number)
            count += 1
            keys = {name: values[name] for name in spec.group_by}
            individual = any(not value.strip() or value in separate.get(name, set())
                             for name, value in keys.items())
            if individual:
                unlabelled_count += 1
            key = ("row", count) if individual else ("group", *keys.values())
            if key not in groups:
                groups[key] = {"group": keys,
                               "sums": {name: 0 for name in spec.sum_columns}, "records": 0}
                if individual:
                    groups[key]["source_row"] = count
                    groups[key]["identity"] = {name: values[name] for name in spec.row_identity}
            group = groups[key]
            group["records"] += 1
            for name, number in numbers.items():
                group["sums"][name] += number
                totals[name] += number
                if individual:
                    unlabelled_totals[name] += number
        if not count:
            return None
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n", delimiter=selection.delimiter)
        writer.writerow(["kind", *(f"context:{name}" for name in context_names),
                         *(f"group:{name}" for name in spec.group_by),
                         *(f"sum:{name}" for name in spec.sum_columns), "records", "source_row",
                         *(f"identity:{name}" for name in spec.row_identity)])

        def write(kind, group, sums, records, source_row="", identity=None):
            writer.writerow([kind, *context.values(),
                             *(group.get(name, "") for name in spec.group_by),
                             *(sums[name] for name in spec.sum_columns), records, source_row,
                             *((identity or {}).get(name, "") for name in spec.row_identity)])

        for group in groups.values():
            individual = "source_row" in group
            write("individual" if individual else "group", group["group"], group["sums"],
                  group["records"], group.get("source_row", ""), group.get("identity"))
        if unlabelled_count:
            # Convenience subtotal only: the individual rows above remain separate members.
            write("unlabelled_total", {}, unlabelled_totals, unlabelled_count)
        write("total", {}, totals, count)
        return output.getvalue()
    except (csv.Error, ValueError):
        return None
