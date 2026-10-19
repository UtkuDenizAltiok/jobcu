"""Shared reasoning rules for grounded comparisons, independent of provider or subject."""

CATEGORY_COMPARISON = """\
Use the SAME category membership for a shared member in both geographic units. If separate
intervals overlap, compare the difference: sum known members' (city share - national share),
then bound unknown members by adding their positive differences for the maximum and negative
differences for the minimum. This can prove a comparison despite overlapping separate
intervals. Keep distinct independent candidates distinct; do not merge them into one party.
When comparable evidence establishes that the city is a subset of the country, a member's
national count is at least its city count. If its national count is otherwise missing, this
gives an upper difference of city_count/city_total - city_count/national_total. Keep that as
a bound, never an exact national figure; the corresponding bounds can be summed for distinct
unlabelled members without merging their category memberships.
Apply the condition's actual comparison operator, including strict versus inclusive boundaries.
For 'city share at or below national share', a maximum difference at or below zero proves yes;
a minimum above zero proves no; otherwise keep it unknown. Do not round a deciding boundary.
"""
