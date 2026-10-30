"""Fictional routes verify consistent off-peak timing without real service calls."""

import json
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
from test_travel import FakeMaps, group, meter, near

from jobcu import db, places, travel
from jobcu.countries import COUNTRIES
from jobcu.location import Anchor, TownRef
from jobcu.sources.http import PoliteClient

NOW = datetime(2026, 10, 12, 10, tzinfo=UTC)


@pytest.mark.parametrize("country", COUNTRIES)
def test_representative_departure_is_wednesday_1030_in_each_country(country):
    result = datetime.fromisoformat(travel.departure(country, NOW).replace("Z", "+00:00"))
    local = result.astimezone(ZoneInfo(travel._TIMEZONES.get(country, "Europe/Paris")))
    assert local.weekday() == 2 and (local.hour, local.minute) == (10, 30)
    assert result > NOW


@pytest.mark.parametrize(("country", "expected"), [
    ("DE", "2026-10-28T09:30:00Z"), ("GB", "2026-10-28T10:30:00Z"),
    ("FI", "2026-10-28T08:30:00Z"),
])
def test_future_departure_uses_the_offset_after_the_clock_change(country, expected):
    assert travel.departure(country, datetime(2026, 10, 24, 12, tzinfo=UTC)) == expected


def test_one_search_crossing_midnight_keeps_its_week_and_deduplicates():
    now = datetime(2026, 10, 13, 21, 59, tzinfo=UTC)  # Tuesday in Germany
    bodies = []

    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=[{
            "destinationIndex": 0, "condition": "ROUTE_EXISTS", "duration": "600s",
        }])

    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    maps = travel.GoogleMaps("fictional-key", http, now=lambda: now)
    assert maps.between_addresses("Workplace", "Town A", "transit", "DE") == 10
    now += timedelta(minutes=2)  # Wednesday local would otherwise move to another week
    assert maps.between_addresses("Workplace", "Town B", "transit", "DE") == 10
    assert bodies[0]["departureTime"] == bodies[1]["departureTime"]
    assert maps.between_addresses("Workplace", "Town A", "transit", "DE") == 10
    assert len(bodies) == 2


def test_old_morning_ai_memory_is_retained_but_not_reused_for_new_timing():
    point = travel.job_point(group("Weßling"))
    town = places.find("Munich", "DE")
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO travel_memory (origin, destination, mode, measured_by, minutes, "
            "measured_at) VALUES (?, ?, ?, ?, ?, ?)",
            (point.identity, "DE:Munich:edge", "transit", travel.ESTIMATE, 45, NOW.isoformat()),
        )
    assert travel.recall(point, [town], "transit", now=NOW) == {}
    travel.remember(point, {"Munich": 25}, "transit", now=NOW)
    assert travel.recall(point, [town], "transit", now=NOW + timedelta(days=1)) == {"Munich": 25}
    assert travel.recall(point, [town], "transit", now=NOW + timedelta(days=45)) == {"Munich": 25}
    assert travel.recall(point, [town], "transit", now=NOW + timedelta(days=91)) == {}
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM travel_memory").fetchone()[0] == 2


@pytest.mark.parametrize("by", [travel.MAPS, travel.ESTIMATE])
def test_old_transit_condition_gets_new_timing_then_limit_edits_reuse_it(by):
    condition = near()
    condition.anchor = Anchor(named=[TownRef(name="Munich", country="DE")])
    job = group("Weßling")
    point = travel.job_point(job)
    old = {"minutes": {"Munich": 90}, "by": by, "point": point.key,
           "routing_version": travel.MAPS_ROUTING_VERSION}
    condition.travel[travel.job_key(job)] = old
    fake = FakeMaps({"Munich": 20})
    tested = meter(fake)
    tested.measure([condition], [job], [0])
    reading = condition.travel[travel.job_key(job)]
    assert reading["timing_profile"] == travel.TRAVEL_TIMING
    assert reading["minutes"]["Munich"] == 20 and len(fake.requests) == 1
    assert "timing_profile" not in old and old["minutes"]["Munich"] == 90
    condition.max_minutes = 30
    tested.measure([condition], [job], [0])
    assert len(fake.requests) == 1


def test_traffic_free_driving_reading_does_not_need_a_timing_refresh():
    condition = near()
    condition.travel_mode = "drive"
    condition.anchor = Anchor(named=[TownRef(name="Munich", country="DE")])
    job = group("Weßling")
    condition.travel[travel.job_key(job)] = {
        "minutes": {"Munich": 20}, "by": travel.MAPS, "point": travel.job_point(job).key,
        "routing_version": travel.MAPS_ROUTING_VERSION,
    }
    fake = FakeMaps({"Munich": 30})
    meter(fake).measure([condition], [job], [0])
    assert fake.requests == []
