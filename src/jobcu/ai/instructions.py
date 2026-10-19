"""Shared reasoning rules for grounded comparisons, independent of provider or subject."""

CATEGORY_COMPARISON = """\
Use the SAME category membership for a shared member in both geographic units. If separate
intervals overlap, compare the difference: sum known members' (city share - national share),
then bound unknown members by adding their positive differences for the maximum and negative
differences for the minimum. This can prove a comparison despite overlapping separate
intervals. Keep distinct independent candidates distinct; do not merge them into one party.
Apply the condition's actual comparison operator, including strict versus inclusive boundaries.
For 'city share at or below national share', a maximum difference at or below zero proves yes;
a minimum above zero proves no; otherwise keep it unknown. Do not round a deciding boundary.
"""
