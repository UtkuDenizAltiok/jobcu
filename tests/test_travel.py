"""Travel limits to reference places: "at most 50 minutes by public transport to a city with at
least 0.3% of the country's people". The owner's example: a job in Fürstenfeldbruck fits through
Munich, although Fürstenfeldbruck itself is small.

Google Maps is always a fake here; nothing contacts the real service."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import pytest
from test_location_conditions import ScriptedClient
from test_search import ready  # noqa: F401

from jobcu import db, places, travel
from jobcu.dedupe import JobGroup
from jobcu.filters import condition_fit
from jobcu.keystore import KeyStore
from jobcu.location import (
    Anchor,
    CheckedCondition,
    Condition,
    ConditionEdit,
    LocationPlan,
    PlaceRegion,
    SortedAnchor,
    SortedCondition,
    TownRef,
    apply_edits,
    check_conditions,
)
from jobcu.pipeline import build_card
from jobcu.settings import Settings
from jobcu.sources.base import FoundJob
from jobcu.sources.http import PoliteClient
from jobcu.travel import TravelGuess, TravelGuesses, TravelMeter

NOW = datetime(2026, 9, 21, 10, 0, tzinfo=UTC)
OWNERS_TEXT = "at most 50 minutes to a city with at least 0.3% of the country's people"


def near(minutes=50, share=0.003, **extra):
    return Condition(text=OWNERS_TEXT, understood_as="Within 50 minutes of a big city",
                     status="estimate", kind="near", max_minutes=minutes, travel_mode="transit",
                     anchor=Anchor(description="cities with at least 0.3%",
                                   min_share_of_country=share), **extra)


def group(location, job_id="1", company="FakeCo", latitude=None, longitude=None):
    return JobGroup(copies=[FoundJob(
        source="s", source_job_id=job_id, url=f"https://jobs.test/{job_id}", title="Engineer",
        company=company, location_text=location, country="DE", latitude=latitude,
        longitude=longitude, posted_at=NOW, date_precision="exact")])


class FakeMaps:
    """Answers route matrices with made-up minutes per destination town."""

    def __init__(self, minutes):
        self.minutes = minutes  # {town name: minutes}
        self.requests = []

    def handler(self, request):
        body = json.loads(request.content)
        self.requests.append((request.url.path, body, dict(request.headers)))
        if "departureTime" in body and body["travelMode"] != "TRANSIT" and "routingPreference" \
                not in body:
            # What the real Routes API answers (checked 2026-09-22).
            return httpx.Response(400, json=[{"error": {
                "code": 400, "status": "INVALID_ARGUMENT",
                "message": "Timestamp cannot be set for TRAFFIC_UNAWARE routing mode."}}])
        elements = []
        for index, destination in enumerate(body["destinations"]):
            point = destination["waypoint"]["location"]["latLng"]
            # The town whose built-up area reaches the point: trips go to a town's nearest edge.
            town = min(places.towns_in("DE"), key=lambda t: (round(max(0.0, places.km(
                t.latitude, t.longitude, point["latitude"], point["longitude"])
                - places.reach_km(t)), 2), -t.people))
            minutes = self.minutes.get(town.name)
            elements.append({"originIndex": 0, "destinationIndex": index,
                             **({"duration": f"{minutes * 60}s", "condition": "ROUTE_EXISTS"}
                                if minutes is not None else {"condition": "ROUTE_NOT_FOUND"})})
        return httpx.Response(200, json=elements)


def meter(fake=None, key=True, client=None, settings=None, notes=None):
    keys = KeyStore()
    if key:
        keys.set(travel.KEY_NAME, "fake-maps-key")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(fake.handler if fake else _no_network))
    return TravelMeter(client, keys, http, settings or Settings(),
                       note=(notes.append if notes is not None else lambda m: None),
                       now=lambda: NOW)


def _no_network(request):
    raise AssertionError("Google Maps must not be asked here")


# --- Reading the sentence -----------------------------------------------------------------


def test_the_owners_sentence_is_one_condition_with_a_reference_point():
    sorted_kinds = {OWNERS_TEXT: SortedCondition(
        text=OWNERS_TEXT, understood_as="Within 50 minutes by public transport of a big city",
        kind="near", max_minutes=50, travel_mode="transit",
        anchor=SortedAnchor(description="cities with at least 0.3% of the people",
                            min_share_of_country=0.003))}
    client = ScriptedClient(None, sorted_kinds=sorted_kinds)
    (condition,) = check_conditions(client, [OWNERS_TEXT], ["DE", "IE"])
    assert condition.kind == "near" and condition.max_minutes == 50
    assert condition.anchor.min_share_of_country == 0.003 and condition.filters
    assert client.research_calls == []  # sizes need no web look-up


def test_reference_places_that_must_be_looked_up_are_researched():
    text = "at most 30 minutes by car from a university town"
    sorted_kinds = {text: SortedCondition(
        text=text, understood_as="Within 30 minutes by car of a university town", kind="near",
        max_minutes=30, travel_mode="drive",
        anchor=SortedAnchor(description="a university town", needs_the_web=True))}
    answer = CheckedCondition(understood_as="University towns", kind="towns_that_fit",
                              towns=[TownRef(name="Freising", country="DE")],
                              confidence="checked", note="From the universities' list.")
    client = ScriptedClient(answer, sorted_kinds=sorted_kinds)
    (condition,) = check_conditions(client, [text], ["DE"])
    assert condition.kind == "near" and condition.travel_mode == "drive"
    assert [t.name for t in condition.anchor.researched] == ["Freising"]
    assert condition.sources and len(client.research_calls) == 1


def test_reference_places_of_a_size_come_from_the_town_list():
    towns = {town.name for town in travel.anchor_towns(near().anchor, "DE")}
    assert "Munich" in towns and "Fürstenfeldbruck" not in towns
    both = Anchor(min_people=100_000, named=[TownRef(name="Freising", country="DE"),
                                             TownRef(name="Augsburg", country="DE")])
    assert [t.name for t in travel.anchor_towns(both, "DE")] == ["Augsburg"]


# --- Measuring ----------------------------------------------------------------------------


def test_fuerstenfeldbruck_fits_through_munich():
    fake = FakeMaps({"Munich": 17, "Augsburg": 55})
    condition = near()
    job = group("Fürstenfeldbruck, Fürstenfeldbruck (Kreis)")
    meter(fake).measure([condition], [job], [0])
    assert condition_fit(condition, job) == "yes"
    (path, body, headers), = fake.requests
    assert path.endswith("computeRouteMatrix") and body["travelMode"] == "TRANSIT"
    assert headers["x-goog-api-key"] == "fake-maps-key"
    assert body["departureTime"] == "2026-09-23T08:30:00Z"  # Wednesday, 10:30 local
    assert condition.status == "applied"  # measured, not estimated
    card = build_card(job, job_id=1, is_new=True, state=None, scored=None,
                      plan=LocationPlan(text="", understood_as="", countries=["DE"], places=[],
                                        conditions=[condition], not_checked_yet=[],
                                        outside_supported_area=[], broad=False),
                      source_names={"s": "Board"}, possible_duplicate_of=None, started_at=NOW,
                      posted_within_hours=24)
    check = card["location_checks"][-1]
    assert check["status"] == "verified" and check["source"] == "Google Maps"
    assert check["detail"] == "Munich, 17 min by public transport"


def test_farther_cities_are_not_asked_when_the_nearest_are_far_over_the_limit():
    # Search 12: only 56 of 1,970 routes fitted, and none after the nearest two took this long.
    far = FakeMaps({"Munich": 101, "Augsburg": 130, "Nuremberg": 40})
    condition = near()
    job = group("Fürstenfeldbruck")
    meter(far).measure([condition], [job], [0])
    assert len(far.requests) == 1  # one round: the two nearest cities
    assert condition_fit(condition, job) == "no"
    assert travel.detail(condition, job)[0] == "Munich, 101 min by public transport"

    # At twice the limit the next cities are still asked, and one can fit.
    closer = FakeMaps({"Munich": 100, "Augsburg": 130, "Nuremberg": 40})
    condition = near()
    meter(closer).measure([condition], [job], [0])
    assert len(closer.requests) > 1
    assert condition_fit(condition, job) == "yes"


def test_a_searchs_share_of_routes_goes_to_the_workplaces_nearest_a_city_first(monkeypatch):
    # 24 searches a month of 600-770 routes each used up 9,000 by about the 13th search; each
    # search now gets its share, and the nearest workplaces are measured first.
    monkeypatch.setattr(travel, "MAPS_FEWEST_PER_SEARCH", 2)
    monkeypatch.setattr(travel, "MAPS_MOST_PER_SEARCH", 2)  # one step: 2 cities, 1 sample each
    fake = FakeMaps({"Munich": 17, "Augsburg": 55})
    condition = near()
    farther, nearer = group("Landsberg am Lech", "1"), group("Fürstenfeldbruck", "2")
    meter(fake).measure([condition], [farther, nearer], [0, 1])
    origins = {b["origins"][0]["waypoint"]["location"]["latLng"]["latitude"]
               for _, b, _ in fake.requests}
    assert origins == {48.179}  # Fürstenfeldbruck, although listed second
    assert condition_fit(condition, nearer) == "yes"
    assert condition_fit(condition, farther) == "unknown"  # no AI here to estimate it


def test_googles_times_are_kept_for_the_exact_same_place_only_when_the_person_chooses():
    # The owner (2026-10-30): keep a measured time for the same place 90 days, ask Google for
    # any other place. Off (0) by default: Google's terms allow keeping only coordinates.
    def search(fake, days, job, when=NOW):
        settings = Settings()
        settings.limits.maps_memory_days = days
        keys = KeyStore()
        keys.set(travel.KEY_NAME, "fake-maps-key")
        http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                            transport=httpx.MockTransport(fake.handler))
        condition = near()
        TravelMeter(None, keys, http, settings, now=lambda: when).measure([condition], [job], [0])
        return condition

    first = FakeMaps({"Munich": 17, "Augsburg": 55})
    search(first, 90, group("Fürstenfeldbruck", "1"))
    assert len(first.requests) == 1
    again = FakeMaps({"Munich": 99})  # Google is not asked: the kept 17 minutes decide
    later = search(again, 90, group("Fürstenfeldbruck", "2"), NOW + timedelta(days=60))
    assert again.requests == [] and condition_fit(later, group("Fürstenfeldbruck", "2")) == "yes"
    moved = FakeMaps({"Munich": 18, "Augsburg": 55})  # another point in the same town
    search(moved, 90, group("Fürstenfeldbruck", "3", latitude=48.18, longitude=11.26))
    assert len(moved.requests) == 1
    stale = FakeMaps({"Munich": 17, "Augsburg": 55})
    search(stale, 90, group("Fürstenfeldbruck", "4"), NOW + timedelta(days=91))
    assert len(stale.requests) == 1
    off = FakeMaps({"Munich": 17, "Augsburg": 55})  # not kept: asked again the next day
    search(off, 0, group("Fürstenfeldbruck", "5"), NOW + timedelta(days=1))
    assert len(off.requests) == 1


def test_when_paid_limits_only_tell_routes_go_on_past_the_limit_with_a_note():
    from jobcu import db

    with db.connect() as conn:
        conn.execute("INSERT INTO source_requests (day, source, count) VALUES (?, ?, ?)",
                     (NOW.strftime("%Y-%m-%d"), "google_maps_routes", 9000))
    settings = Settings()
    settings.limits.paid_limits = "tell"
    notes = []
    fake = FakeMaps({"Munich": 17, "Augsburg": 55})
    condition, job = near(), group("Fürstenfeldbruck")
    meter(fake, settings=settings, notes=notes).measure([condition], [job], [0])
    assert len(fake.requests) == 1 and condition_fit(condition, job) == "yes"
    assert any("past your limit of 9,000" in note for note in notes)
    stopping = FakeMaps({"Munich": 17})
    meter(stopping).measure([near()], [group("Fürstenfeldbruck", "2")], [0])
    assert stopping.requests == []  # the default stops at the limit


def test_car_trips_are_measured_without_a_departure_time():
    fake = FakeMaps({"Munich": 25})
    condition = near(minutes=30)
    condition.travel_mode = "drive"
    job = group("Fürstenfeldbruck")
    notes = []
    meter(fake, notes=notes).measure([condition], [job], [0])
    (_, body, _), = fake.requests
    assert body["travelMode"] == "DRIVE" and "departureTime" not in body
    assert condition_fit(condition, job) == "yes"
    assert notes == ["Google Maps compares sampled city-edge and city-centre destinations; "
                     "other districts may have faster connections."]
    assert travel.detail(condition, job) == ("Munich, 25 min by car", "Google Maps")


def test_google_diagnostics_do_not_log_account_specific_error_text(caplog):
    def refuse(request):
        return httpx.Response(400, json=[{"error": {
            "code": 400, "message": "Bad field for projects/fictional-account."}}])

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(refuse))
    with caplog.at_level("WARNING"), pytest.raises(travel.MapsError, match="code 400"):
        travel.GoogleMaps("fake-maps-key", http, now=lambda: NOW).minutes(
            travel.job_point(group("Freising")), [places.find("Munich", "DE")], "transit")
    assert "Google Maps refused a request (code 400)" in caplog.text
    assert "fictional-account" not in caplog.text and "Bad field" not in caplog.text


def test_google_s_daily_limit_is_named_as_such(caplog):
    def used_up(request):
        return httpx.Response(429, json=[{"error": {"code": 429, "message":
            "Quota exceeded for quota metric 'Route Matrix Elements' and limit 'Route matrix "
            "elements per day' of service 'routes.googleapis.com'."}}])

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(used_up))
    with caplog.at_level("WARNING"), pytest.raises(travel.MapsError, match="daily quota"):
        travel.GoogleMaps("fake-maps-key", http, now=lambda: NOW).minutes(
            travel.job_point(group("Freising")), [places.find("Munich", "DE")], "transit")
    assert "quota scope: day" in caplog.text


def test_an_unclassified_refusal_logs_google_s_generic_names_but_not_the_account(caplog):
    def refuse(request):
        return httpx.Response(429, json={"error": {
            "code": 429, "status": "RESOURCE_EXHAUSTED",
            "message": "Resource exhausted for projects/fictional-account.",
            "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                         "reason": "RATE_LIMIT_EXCEEDED", "metadata": {
                             "consumer": "projects/fictional-account",
                             "quota_limit": "FictionalElementsPerProject"}}]}})

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(refuse))
    with caplog.at_level("WARNING"), pytest.raises(travel.MapsError):
        travel.GoogleMaps("fake-maps-key", http, now=lambda: NOW).minutes(
            travel.job_point(group("Freising")), [places.find("Munich", "DE")], "transit")
    assert ("quota scope: unknown; status RESOURCE_EXHAUSTED; reason RATE_LIMIT_EXCEEDED; "
            "quota_limit FictionalElementsPerProject; retry-after none)") in caplog.text
    assert "fictional-account" not in caplog.text


def _refusing_transit(minute_scope=False, succeed_after=None):
    calls = {"transit": 0, "drive": 0}

    def handle(request):
        mode = json.loads(request.content)["travelMode"].lower()
        calls[mode] += 1
        if mode == "drive" or (succeed_after is not None and calls[mode] in succeed_after):
            return httpx.Response(200, json=[{"originIndex": 0, "destinationIndex": 0,
                                              "status": {}, "duration": "1500s",
                                              "condition": "ROUTE_EXISTS"}])
        message = ("Quota exceeded for quota metric 'Elements' and limit 'Elements per minute'."
                   if minute_scope else "Quota exceeded.")
        return httpx.Response(429, json=[{"error": {"code": 429, "message": message}}])

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handle))
    return travel.GoogleMaps("fake-maps-key", http, now=lambda: NOW), calls


def _ask(maps, mode, town="Freising"):
    return maps.minutes(travel.job_point(group(town)), [places.find("Munich", "DE")], mode)


def test_a_mode_refused_by_an_unidentified_quota_is_not_asked_again_this_search():
    maps, calls = _refusing_transit()
    for _ in range(travel.UNIDENTIFIED_QUOTA_STOP):
        with pytest.raises(travel.MapsError, match="did not say"):
            _ask(maps, "transit")
    sent = calls["transit"]
    with pytest.raises(travel.MapsError, match="stopped asking for journeys by public transport"):
        _ask(maps, "transit", "Erding")
    assert calls["transit"] == sent  # no further refused attempts count against the allowance
    assert _ask(maps, "drive").minutes == {"Munich": 25}  # another mode keeps working


@pytest.mark.parametrize("minute_scope,succeed_after", [(True, None), (False, {5})])
def test_throttling_or_a_success_between_refusals_keeps_the_mode_available(
        minute_scope, succeed_after):
    maps, calls = _refusing_transit(minute_scope, succeed_after)
    for town in ("Freising", "Erding", "Dachau", "Moosburg"):
        try:
            _ask(maps, "transit", town)
        except travel.MapsError as exc:
            assert "stopped asking" not in str(exc)
    assert not maps._mode_unavailable


def test_clear_cases_need_no_route_look_up():
    condition = near(minutes=10)
    in_munich = group("München", "1")
    far_away = group("Garmisch-Partenkirchen", "2")  # no big city within 10 minutes' reach
    meter().measure([condition], [in_munich, far_away], [0, 1])
    assert condition_fit(condition, in_munich) == "yes"
    assert condition_fit(condition, far_away) == "no"
    assert travel.detail(condition, far_away)[0].startswith("nearest is Munich")


def test_a_job_anywhere_in_an_eligible_city_needs_no_trip():
    # Search 8 measured "Moosach, München" (an address 7 km from the centre) as 27 minutes to
    # Munich. A reference place is where the person would live: a job in one needs nothing more.
    condition = near(minutes=10)
    moosach = group("Moosach, München", "1", latitude=48.180, longitude=11.510)
    augsburg = group("Augsburg", "2", latitude=48.330, longitude=10.960)  # an outer district
    meter().measure([condition], [moosach, augsburg], [0, 1])  # no Google request at all
    assert condition_fit(condition, moosach) == "yes"
    assert travel.detail(condition, moosach)[0] == "in Munich"
    assert condition_fit(condition, augsburg) == "yes"
    # By distance too, and a town of the same name far away is another town.
    by_km = near(max_km=1, minutes=None)
    assert condition_fit(by_km, moosach) == "yes"
    other = travel.Point(47.49, 11.10, "DE", "address", "Munich")  # in Garmisch
    assert travel.home_town(other, travel.anchor_towns(by_km.anchor, "DE")) is None


def test_a_close_call_is_measured_from_the_ads_own_place_only():
    # A company can have several sites with the same name, so Jobcu never looks up a company's
    # address elsewhere: the place the ad names is what counts (the owner's decision).
    fake = FakeMaps({"Munich": 52})
    condition = near()
    job = group("Fürstenfeldbruck", company="Has Many Sites GmbH")
    meter(fake).measure([condition], [job], [0])
    assert len(fake.requests) > 1  # finish the other reachable alternatives too
    assert all(path == "/distanceMatrix/v2:computeRouteMatrix" for path, _, _ in fake.requests)
    assert condition_fit(condition, job) == "no"
    assert travel.detail(condition, job)[0].startswith("Munich, 52 min by public transport")


def test_without_a_key_the_ai_estimates_and_says_so():
    class GuessingClient:
        def __init__(self):
            self.prompts = []

        def generate(self, output, **request):
            self.prompts.append(request["prompt"])
            return TravelGuesses(answers=[TravelGuess(id="P0", town="Munich", minutes=25)])

    client, notes = GuessingClient(), []
    condition = near()
    job = group("Fürstenfeldbruck")
    meter(key=False, client=client, notes=notes).measure([condition], [job], [0])
    assert condition_fit(condition, job) == "yes" and condition.status == "estimate"
    assert "Fürstenfeldbruck" in client.prompts[0] and "Munich" in client.prompts[0]
    assert travel.detail(condition, job)[1] == "AI estimate"


def test_the_monthly_limit_stops_google_maps_and_the_ai_takes_over():
    class GuessingClient:
        def generate(self, output, **request):
            import re
            towns = re.findall(r"([^,|]+) \(edge \d+ km\)",
                               request["prompt"].split("| to:", 1)[1])
            return TravelGuesses(answers=[
                TravelGuess(id="P0", town=town.strip(), minutes=70) for town in towns])

    settings = Settings()
    settings.limits.maps_monthly_routes = 0
    notes = []
    condition = near()
    job = group("Fürstenfeldbruck")
    meter(client=GuessingClient(), settings=settings, notes=notes).measure([condition], [job], [0])
    assert condition_fit(condition, job) == "no"  # all reachable cities have an estimate
    assert any("route allowance" in note for note in notes)


def test_a_corrected_limit_needs_no_new_look_up():
    fake = FakeMaps({"Munich": 17, "Augsburg": 55})
    condition = near()
    job = group("Fürstenfeldbruck")
    plan = LocationPlan(text="", understood_as="", countries=["DE"], places=[],
                        conditions=[condition], not_checked_yet=[], outside_supported_area=[],
                        broad=False)
    meter(fake).measure([condition], [job], [0])
    stricter = apply_edits(ScriptedClient(None), plan,
                           [ConditionEdit(text=OWNERS_TEXT, original=0, max_minutes=15)])
    corrected = stricter.conditions[0]
    meter().measure([corrected], [job], [0])  # would fail if Google Maps were asked again
    assert condition_fit(corrected, job) == "no" and corrected.changed_by_you
    # Another way of travelling means the old times don't apply any more.
    by_car = apply_edits(ScriptedClient(None), plan,
                         [ConditionEdit(text=OWNERS_TEXT, original=0, travel_mode="drive")])
    assert by_car.conditions[0].travel == {}


def test_job_sites_coordinates_come_first():
    job = group("Somewhere", latitude=48.18, longitude=11.25)
    point = travel.job_point(job)
    assert (point.latitude, point.longitude, point.how) == (48.18, 11.25, "address")
    assert travel.job_point(group("Fürstenfeldbruck")).how == "town"


@pytest.mark.parametrize(("country", "expected"), [
    ("DE", "2026-09-23T08:30:00Z"), ("GB", "2026-09-23T09:30:00Z"),
    ("FI", "2026-09-23T07:30:00Z"),
])
def test_departure_is_a_weekday_morning_local_time(country, expected):
    assert travel.departure(country, NOW) == expected
    wednesday_early = NOW + timedelta(days=1, hours=12)  # Wednesday local → following week
    assert travel.departure("DE", wednesday_early) == "2026-09-30T08:30:00Z"


def test_a_distance_limit_is_measured_in_a_straight_line():
    condition = Condition(text="within 30 km of Munich", understood_as="Within 30 km of Munich",
                          status="applied", kind="near", max_km=30,
                          anchor=Anchor(named=[TownRef(name="Munich", country="DE")]))
    assert condition_fit(condition, group("Fürstenfeldbruck")) == "yes"
    assert condition_fit(condition, group("Augsburg")) == "no"


def test_testing_the_key_explains_problems_plainly():
    def refused(request):
        return httpx.Response(403, json={"error": {"message": "API key not valid"}})

    keys = KeyStore()
    assert travel.check_key(keys, None)[1] == "Please save a Google Maps key first."
    keys.set(travel.KEY_NAME, "wrong-key")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(refused))
    ok, message = travel.check_key(keys, http)
    assert not ok and "didn't accept the key" in message


def test_key_test_uses_stations_and_describes_public_transport():
    requests = []

    def reply(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=[{"originIndex": 0, "destinationIndex": 0,
                                        "duration": "1620s", "condition": "ROUTE_EXISTS"}])

    keys = KeyStore()
    keys.set(travel.KEY_NAME, "fake-maps-key")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(reply))
    ok, message = travel.check_key(keys, http)
    assert ok
    (body,) = requests
    assert "Freising" in body["origins"][0]["waypoint"]["address"]
    assert "Bahnhof" in body["origins"][0]["waypoint"]["address"]
    assert "Hauptbahnhof" in body["destinations"][0]["waypoint"]["address"]
    assert body["travelMode"] == "TRANSIT" and "departureTime" in body
    assert "27 min by public transport" in message
    assert "Wednesday at 10:30" in message and "checks access" in message
    assert "by train" not in message


def test_key_test_counts_one_element_and_respects_the_route_limit():
    from jobcu import db
    from jobcu.settings import save_settings

    def reply(request):
        return httpx.Response(200, json=[{"duration": "1500s", "condition": "ROUTE_EXISTS"}])

    settings = Settings()
    settings.limits.maps_monthly_routes = 1
    save_settings(settings)
    keys = KeyStore()
    keys.set(travel.KEY_NAME, "fake-maps-key")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(reply))
    assert travel.check_key(keys, http)[0]
    with db.connect() as conn:
        assert conn.execute("SELECT SUM(count) FROM source_requests "
                            "WHERE source = 'google_maps_routes'").fetchone()[0] == 1
    refusing_http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                                 transport=httpx.MockTransport(_no_network))
    ok, message = travel.check_key(keys, refusing_http)
    assert not ok and "monthly route limit" in message


class Sampled:
    """Made-up minutes by the destination's point and the local departure time: `first` for the
    main station asked first, `edge`, and `next_station`, each `{"10:30": minutes, ...}` or one
    number for every departure. None answers "no route"."""

    def __init__(self, origin, *, first, edge=None, next_station=None, town="Munich"):
        city = places.find(town, "DE")
        point = travel.job_point(group(origin))
        samples = travel.transit_samples(point, city)
        self.answers = dict(zip(samples, [first, edge, next_station], strict=False))
        self.samples = samples
        self.requests = []

    def __call__(self, request):
        body = json.loads(request.content)
        self.requests.append(body)
        when = datetime.fromisoformat(body["departureTime"].replace("Z", "+00:00")).astimezone(
            ZoneInfo("Europe/Berlin")).strftime("%H:%M")
        elements = []
        for index, destination in enumerate(body["destinations"]):
            point = destination["waypoint"]["location"]["latLng"]
            answer = self.answers[point["latitude"], point["longitude"]]
            minutes = answer.get(when) if isinstance(answer, dict) else answer
            elements.append({"destinationIndex": index, "condition": "ROUTE_NOT_FOUND"}
                            if minutes is None else
                            {"destinationIndex": index, "condition": "ROUTE_EXISTS",
                             "duration": f"{minutes * 60}s"})
        return httpx.Response(200, json=elements)

    def asked(self, number):
        return [(d["waypoint"]["location"]["latLng"]["latitude"],
                 d["waypoint"]["location"]["latLng"]["longitude"])
                for d in self.requests[number]["destinations"]]


def measured_by(reply, origin, minutes=50, settings=None):
    condition = near(minutes=minutes)
    condition.anchor = Anchor(named=[TownRef(name="Munich", country="DE")])
    job = group(origin)
    keys = KeyStore()
    keys.set(travel.KEY_NAME, "fake-maps-key")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(reply))
    tested = TravelMeter(None, keys, http, settings or Settings(), now=lambda: NOW)
    tested.measure([condition], [job], [0])
    return tested, condition, job


def test_a_good_main_station_settles_the_journey_with_one_route():
    sampled = Sampled("Rosenheim", first=40, edge=129, next_station=60)
    tested, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "yes"
    assert sampled.asked(0) == [sampled.samples[0]] and len(sampled.requests) == 1
    assert tested._routes.used_this_search == 1
    # The station nearest the job: München Ost is on Rosenheim's side of Munich.
    assert sampled.samples[0] == (48.12778, 11.60444)


def test_a_slow_main_station_does_not_hide_a_reachable_edge():
    sampled = Sampled("Rosenheim", first=70, edge=45, next_station=90)
    tested, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "yes"
    assert travel.detail(condition, job) == ("Munich, 45 min by public transport", "Google Maps")
    assert sampled.asked(1) == sampled.samples[1:] and len(sampled.requests) == 2
    assert tested._routes.used_this_search == 3


def test_a_city_far_over_the_limit_is_not_asked_again():
    # Of 1,083 stored city journeys, 888 were over twice the limit, and no edge fitted them.
    sampled = Sampled("Rosenheim", first=101, edge=20, next_station=20)
    tested, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "no"
    assert len(sampled.requests) == 1 and tested._routes.used_this_search == 1


def test_no_route_to_the_main_station_still_tries_the_edge():
    sampled = Sampled("Rosenheim", first=None, edge=45, next_station=None)
    _, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "yes"
    assert len(sampled.requests) == 2


def test_a_near_miss_is_asked_again_at_later_departures():
    # Measured for real: the journey after 10:30 can be a slow one, a commuter takes the good train.
    sampled = Sampled("Rosenheim", first={"10:30": 68, "10:50": 68, "11:10": 48}, edge=129,
                      next_station=54)
    tested, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "yes"
    assert travel.detail(condition, job)[0] == "Munich, 48 min by public transport"
    times = [body["departureTime"] for body in sampled.requests]
    assert times == ["2026-09-23T08:30:00Z", "2026-09-23T08:30:00Z", "2026-09-23T08:50:00Z",
                     "2026-09-23T09:10:00Z"]
    # Later departures ask only the two best samples, never the slow edge.
    assert sampled.asked(2) == [sampled.samples[2], sampled.samples[0]]
    assert tested._routes.used_this_search == 1 + 2 + 2 + 2


def test_a_later_departure_that_fits_needs_no_further_one():
    sampled = Sampled("Rosenheim", first={"10:30": 68, "10:50": 48, "11:10": 40}, edge=129,
                      next_station=90)
    _, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "yes"
    assert len(sampled.requests) == 3


def test_beyond_a_near_miss_no_later_departure_is_asked():
    sampled = Sampled("Rosenheim", first=76, edge=129, next_station=90)
    tested, condition, job = measured_by(sampled, "Rosenheim")
    assert condition_fit(condition, job) == "no"
    assert len(sampled.requests) == 2 and tested._routes.used_this_search == 3


def test_a_failed_later_step_leaves_the_job_unknown_not_ruled_out():
    def reply(request):
        body = json.loads(request.content)
        if body["departureTime"].endswith("08:30:00Z"):
            return httpx.Response(200, json=[
                {"destinationIndex": index, "condition": "ROUTE_EXISTS", "duration": "3600s"}
                for index in range(len(body["destinations"]))])
        return httpx.Response(400, json={"error": {"status": "INVALID_ARGUMENT"}})

    _, condition, job = measured_by(reply, "Rosenheim")
    assert condition_fit(condition, job) == "unknown"
    assert travel.detail(condition, job)[0].startswith("Munich, 60 min")


def test_later_departures_are_remembered_apart_and_not_asked_again():
    sampled = Sampled("Rosenheim", first={"10:30": 68, "10:50": 60, "11:10": 55}, edge=129,
                      next_station=90)
    settings = Settings()
    settings.limits.maps_memory_days = 90
    _, condition, job = measured_by(sampled, "Rosenheim", settings=settings)
    assert condition_fit(condition, job) == "no"
    sent = len(sampled.requests)
    assert sent == 4
    _, again, job = measured_by(sampled, "Rosenheim", settings=settings)
    assert len(sampled.requests) == sent
    assert travel.detail(again, job)[0] == "Munich, 55 min by public transport"
    with db.connect() as conn:
        kept = {row["destination"].split("|")[1] for row in conn.execute(
            "SELECT destination FROM travel_memory")}
    assert kept == {"wednesday-1030", "wednesday-1030+20", "wednesday-1030+40"}


def test_a_later_departure_can_cross_the_hour():
    assert travel.departure("DE", NOW, 40) == "2026-09-23T09:10:00Z"


def test_a_person_who_asks_for_the_centre_gets_only_the_centre():
    munich = places.find("Munich", "DE")
    assert travel.transit_samples(travel.job_point(group("Rosenheim")), munich, True) == [
        (munich.latitude, munich.longitude)]


def test_a_town_with_no_listed_station_starts_at_its_centre():
    town = places.Town("Example City", "DE", 50, 8, 400_000)
    point = travel.Point(50.5, 8, "DE", "town", "Example Town")
    assert places.main_stations(town) == ()
    assert travel.transit_samples(point, town) == [(50, 8), travel.edge_point(point, town)]


def test_a_village_named_like_a_listed_city_has_no_main_station():
    assert places.main_stations(places.Town("Luton", "GB", 50.59, -3.51, 1_000)) == ()


def test_every_listed_station_is_in_its_town():
    file = Path(places.__file__).parent / "data" / "stations.csv"
    rows = [line.split(",") for line in file.read_text(encoding="utf-8").splitlines()
            if not line.startswith("#")]
    assert rows
    for country, name, station, *_ in rows:
        town = places.find(name, country)
        assert town is not None and town.name == name, station
    towns = {(country, name) for country, name, *_ in rows}
    listed = sum(len(places.main_stations(places.find(name, country))) for country, name in towns)
    assert listed == len(rows)


def test_car_journeys_still_compare_the_edge_and_the_centre_at_once():
    fake = FakeMaps({"Munich": 25})
    condition = near()
    condition.travel_mode = "drive"
    job = group("Freising")
    meter(fake).measure([condition], [job], [0])
    assert len(fake.requests) == 1
    assert len(fake.requests[0][1]["destinations"]) == 2 * len(
        travel.anchor_towns(condition.anchor, "DE")[:travel.NEAREST])


def test_a_journey_asks_one_destination_at_first():
    requests = []

    def reply(request):
        body = json.loads(request.content)
        requests.append(body)
        return httpx.Response(200, json=[
            {"destinationIndex": index, "condition": "ROUTE_EXISTS", "duration": "2100s"}
            for index in range(len(body["destinations"]))])

    condition = near(minutes=50)
    condition.anchor = Anchor(named=[TownRef(name="Munich", country="DE")])
    job = group("Freising")
    keys = KeyStore()
    keys.set(travel.KEY_NAME, "fake-maps-key")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(reply))
    tested = TravelMeter(None, keys, http, Settings(), now=lambda: NOW)
    tested.measure([condition], [job], [0])
    assert condition_fit(condition, job) == "yes"
    assert travel.detail(condition, job) == ("Munich, 35 min by public transport", "Google Maps")
    assert len(requests) == 1 and len(requests[0]["destinations"]) == 1
    assert tested._routes.used_this_search == 1


@pytest.mark.parametrize(("edge", "centre", "expected"), [
    ("1140s", "2100s", 19),
    (None, "2100.001s", 36),
    ("5400s", None, 90),
    ("bad", "infs", None),
])
def test_sampled_routes_keep_available_times_and_round_fractional_seconds(edge, centre, expected):
    def reply(request):
        return httpx.Response(200, json=[
            {"destinationIndex": index,
             "condition": "ROUTE_EXISTS" if duration is not None else "ROUTE_NOT_FOUND",
             "duration": duration}
            for index, duration in [(1, centre), (0, edge)]
        ])

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(reply))
    origin = travel.Point(54, -6, "IE", "town", "Example Town")
    town = places.Town("Example City", "IE", 53, -6, 200_000)
    found = travel.GoogleMaps("fake-maps-key", http, now=lambda: NOW).minutes(
        origin, [town], "transit")
    if edge == "bad":
        assert found.minutes == {} and found.unchecked == {"Example City"}
    else:
        assert found.minutes == {"Example City": expected} and not found.unchecked


def test_a_matrix_element_error_is_not_used_as_a_successful_journey():
    def reply(request):
        assert "status" in request.headers["X-Goog-FieldMask"].split(",")
        return httpx.Response(200, json=[
            {"destinationIndex": 0, "status": {"code": 7}, "condition": "ROUTE_EXISTS",
             "duration": "60s"},
            {"destinationIndex": 1, "status": {}, "condition": "ROUTE_EXISTS",
             "duration": "1200s"},
        ])

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(reply))
    origin = travel.Point(54, -6, "IE", "town", "Example Town")
    town = places.Town("Example City", "IE", 53, -6, 200_000)
    found = travel.GoogleMaps("fake-maps-key", http, now=lambda: NOW).minutes(
        origin, [town], "transit")
    assert found.minutes == {"Example City": 20}
    assert found.unchecked == {"Example City"}


def test_no_journey_is_asked_past_the_maps_limit():
    condition = near()
    condition.anchor = Anchor(named=[TownRef(name="Munich", country="DE")])
    settings = Settings()
    settings.limits.maps_monthly_routes = 0
    notes = []
    tested = meter(client=None, settings=settings, notes=notes)
    job = group("Freising")
    tested.measure([condition], [job], [0])  # the mocked HTTP refuses any unexpected request
    assert tested._routes.used_this_search == 0
    assert condition_fit(condition, job) == "unknown"
    assert any("route allowance" in note for note in notes)


def test_an_old_single_edge_answer_is_rechecked_after_the_routing_change():
    condition = near()
    condition.anchor = Anchor(named=[TownRef(name="Munich", country="DE")])
    job = group("Freising")
    point = travel.job_point(job)
    condition.travel[travel.job_key(job)] = {
        "minutes": {"Munich": 90}, "by": "Google Maps", "from": "town", "point": point.key}
    fake = FakeMaps({"Munich": 35})
    meter(fake).measure([condition], [job], [0])
    assert condition_fit(condition, job) == "yes" and len(fake.requests) == 1
    assert condition.travel[travel.job_key(job)]["routing_version"] == travel.MAPS_ROUTING_VERSION


# --- A whole search -----------------------------------------------------------------------


@pytest.mark.parametrize(("role", "field"), [
    ("Hardware Engineer", "Electronics"), ("Library Assistant", "Library services"),
])
def test_a_search_keeps_jobs_near_a_big_city_and_leaves_out_far_ones(
        ready, monkeypatch, role, field):  # noqa: F811
    import re

    from conftest import make_pdf
    from test_search import PROFILE, FakeAI, wait_until_done

    from jobcu import documents, search
    from jobcu.ai.base import RawReply, Usage
    from jobcu.settings import SearchForm
    from jobcu.sources.base import JobSource

    documents.save_upload("cv", "cv.pdf", make_pdf([
        "Alex Example", f"{role} with five years of professional experience.",
        f"Field: {field}.", "Languages: English fluent."]))
    documents.save_upload("cover_letter", "letter.txt",
                          f"I would like to work as a {role}. ".encode() * 5)

    class NearAI(FakeAI):
        def complete_json(self, **request):
            name, prompt = request["schema_name"], request["prompt"]
            if name == "Profile":
                answer = {**PROFILE, "summary": f"Experienced {role}.",
                          "current_or_last_role": role, "field": field,
                          "skills": ["Teamwork"], "technical_areas": [],
                          "target_roles": [role], "target_fields": [field]}
            elif name == "SearchWordsAnswer":
                answer = {"terms": [{"text": role, "language": "en", "kind": "job_title"}]}
            elif name == "LocationInterpretation":
                answer = {"understood_as": "Germany, near a big city.", "limits_countries": True,
                          "countries": ["DE"], "places": [],
                          "conditions_about_places": [{"text": OWNERS_TEXT,
                              "understood_as": "Within 50 minutes of a big city",
                              "kind": "near", "max_minutes": 50, "travel_mode": "transit",
                              "anchor": {"description": "big cities",
                                         "min_share_of_country": 0.003}}],
                          "conditions_about_the_job": [], "outside_supported_area": []}
            elif name == "SortedConditions":
                answer = {"conditions": [{
                    "text": OWNERS_TEXT, "understood_as": "Within 50 minutes of a big city",
                    "kind": "near", "max_minutes": 50, "travel_mode": "transit",
                    "anchor": {"description": "big cities", "min_share_of_country": 0.003}}]}
            elif name == "TravelGuesses":
                answer = {"answers": [
                    {"id": pid, "town": town.strip(),
                     "minutes": 25 if "Fürstenfeldbruck" in line and town.strip() == "Munich"
                     else 95}
                    for pid, line in re.findall(r"^(P\d+) \| (.*)$", prompt, re.MULTILINE)
                    for town in re.findall(r"([^,|]+) \(edge \d+ km\)",
                                           line.split("| to:", 1)[1])]}
            else:
                return super().complete_json(**request)
            return RawReply(json.dumps(answer), Usage(10, 5))

    class PlacedSource(JobSource):
        id, name, kind = "placed", "Placed Jobs", "job_board"

        def search(self, query, ctx):
            for i, place in enumerate(["Fürstenfeldbruck", "Hof", "München"]):
                yield FoundJob(source="placed", source_job_id=str(i), url=f"https://jobs.test/{i}",
                               title=role, company=f"Company {i}",
                               location_text=place, country="DE",
                               posted_at=datetime.now(UTC), date_precision="exact",
                               description="Full ad", description_is_complete=True)

    monkeypatch.setattr("jobcu.ai.client.AIClient.adapter", lambda self: NearAI())
    monkeypatch.setattr("jobcu.pipeline.all_sources", lambda: [PlacedSource()])
    manager = search.SearchManager()
    manager.start(SearchForm(location_text="Germany, " + OWNERS_TEXT))
    result = wait_until_done(manager)
    assert result["status"] == "finished", result["error"]
    assert result["result"]["profile"]["field"] == field
    jobs = result["result"]["jobs"]
    assert sorted(card["location"] for card in jobs["cards"]) == [
        "Fürstenfeldbruck", "München"]
    assert [card["location"] for card in jobs["ruled_out_by_conditions"]] == ["Hof"]
    assert jobs["location_unchecked"] == []
    bruck = next(card for card in jobs["cards"] if card["location"] == "Fürstenfeldbruck")
    check = bruck["location_checks"][-1]
    assert check["detail"] == "Munich, 25 min by public transport"
    assert check["source"] == "AI estimate"
    assert any("Google Maps key" in note for note in result["notes"])


# --- Remembered for 90 days ---------------------------------------------------------------


def test_googles_travel_times_are_never_kept_beyond_the_search():
    # The Routes API terms (19.3) allow keeping coordinates only, so the next search asks again.
    fake = FakeMaps({"Munich": 17, "Augsburg": 55})
    meter(fake).measure([near()], [group("Fürstenfeldbruck", "1")], [0])
    meter(fake).measure([near()], [group("Fürstenfeldbruck", "2")], [0])
    assert len(fake.requests) == 2
    from jobcu import db
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM travel_memory").fetchone()[0] == 0


def test_ai_estimates_are_remembered_for_90_days_from_the_same_town():
    class GuessingClient:
        calls = 0

        def generate(self, output, **request):
            GuessingClient.calls += 1
            return TravelGuesses(answers=[TravelGuess(id="P0", town="Munich", minutes=25)])

    meter(key=False, client=GuessingClient()).measure([near()], [group("Fürstenfeldbruck")], [0])
    later = near()
    job = group("Fürstenfeldbruck", "2", company="Other GmbH")
    meter(key=False, client=GuessingClient()).measure([later], [job], [0])
    assert GuessingClient.calls == 1 and condition_fit(later, job) == "yes"
    month = TravelMeter(GuessingClient(), KeyStore(), None, Settings(),
                        now=lambda: NOW + timedelta(days=45))
    month.measure([near()], [job], [0])
    assert GuessingClient.calls == 1  # still remembered after a month and a half
    stale = TravelMeter(GuessingClient(), KeyStore(), None, Settings(),
                        now=lambda: NOW + timedelta(days=91))
    stale.measure([near()], [job], [0])
    assert GuessingClient.calls == 2


def test_estimates_are_remembered_only_until_there_is_a_key():
    class GuessingClient:
        calls = 0

        def generate(self, output, **request):
            GuessingClient.calls += 1
            return TravelGuesses(answers=[TravelGuess(id="P0", town="Munich", minutes=25)])

    meter(key=False, client=GuessingClient()).measure([near()], [group("Fürstenfeldbruck")], [0])
    meter(key=False, client=GuessingClient()).measure([near()], [group("Fürstenfeldbruck")], [0])
    assert GuessingClient.calls == 1  # the second search used the remembered estimate
    fake = FakeMaps({"Munich": 17, "Augsburg": 55})
    with_key = near()
    meter(fake).measure([with_key], [group("Fürstenfeldbruck")], [0])
    assert len(fake.requests) == 1 and travel.detail(with_key, group("Fürstenfeldbruck")) == (
        "Munich, 17 min by public transport", "Google Maps")


# --- Reference places defined by any fact -------------------------------------------------


def test_places_that_fail_a_fact_are_never_reference_places():
    anchor = Anchor(min_share_of_country=0.003, avoided=[TownRef(name="Dresden", country="DE")],
                    looked_up=True)
    towns = {town.name for town in travel.anchor_towns(anchor, "DE")}
    assert "Leipzig" in towns and "Dresden" not in towns


def test_a_whole_region_that_fails_a_fact_gives_no_reference_places_but_its_exceptions():
    # Search 8 measured Radeberg to Dresden although Dresden should have been avoided.
    anchor = Anchor(min_share_of_country=0.003, looked_up=True,
                    avoided_regions=[PlaceRegion(code="DE.13", name="Saxony", country="DE")],
                    exceptions=[TownRef(name="Leipzig", country="DE")])
    towns = {town.name for town in travel.anchor_towns(anchor, "DE")}
    assert "Dresden" not in towns and "Chemnitz" not in towns
    assert "Leipzig" in towns and "Munich" in towns

    fitting = Anchor(researched_regions=[PlaceRegion(code="DE.13", name="Saxony", country="DE")],
                     min_people=100_000, looked_up=True)
    assert {town.name for town in travel.anchor_towns(fitting, "DE")} == {
        "Dresden", "Leipzig", "Chemnitz"}


def test_one_fact_is_looked_up_once_for_the_job_town_and_the_reference_places():
    far_right = "no cities where far-right parties polled above the national average"
    commute = "at most 50 minutes by public transport to a city with at least 0.3% of people"
    sorted_kinds = {
        commute: SortedCondition(
            text=commute, understood_as="Within 50 minutes of a big city that isn't a "
            "far-right stronghold", kind="near", max_minutes=50, travel_mode="transit",
            anchor=SortedAnchor(description="big cities that aren't far-right strongholds",
                                min_share_of_country=0.003, needs_the_web=True,
                                look_up=far_right)),
        far_right: SortedCondition(text=far_right, understood_as="Not in far-right strongholds",
                                   kind="needs_the_web"),
    }
    avoid = CheckedCondition(understood_as="Avoid far-right strongholds", kind="towns_to_avoid",
                             towns=[TownRef(name="Dresden", country="DE"),
                                    TownRef(name="Chemnitz", country="DE")],
                             confidence="checked", note="Federal election 2025 results.")
    client = ScriptedClient(avoid, sorted_kinds=sorted_kinds)
    reference, own_town = check_conditions(client, [commute, far_right], ["DE"])
    assert len(client.research_calls) == 1
    assert [t.name for t in reference.anchor.avoided] == ["Dresden", "Chemnitz"]
    assert reference.anchor.min_share_of_country == 0.003 and reference.sources
    assert own_town.kind == "towns_to_avoid" and own_town.text == far_right


def test_a_fact_given_in_fewer_words_is_the_other_condition_s_fact():
    # The owner's own sentence (2026-09-22): the travel condition's reference places were looked
    # up from the part in brackets alone, which the AI read as turnout.
    far_right = ("I dont want far-right fascist supporter cities (the elections voting ratio "
                 "should be less than its country average)")
    commute = "at most 50 minutes by car to a city that has at least %0.3 of its country's people"
    sorted_kinds = {
        commute: SortedCondition(
            text=commute, understood_as="Within 50 minutes by car of such a city", kind="near",
            max_minutes=50, travel_mode="drive",
            anchor=SortedAnchor(description="big cities", min_share_of_country=0.003,
                                needs_the_web=True, look_up="the elections voting ratio should "
                                "be less than its country average")),
        far_right: SortedCondition(text=far_right, understood_as="Not far-right cities",
                                   kind="needs_the_web"),
    }
    avoid = CheckedCondition(understood_as="Avoid far-right strongholds", kind="towns_to_avoid",
                             towns=[TownRef(name="Görlitz", country="DE")], confidence="checked",
                             note="AfD above its national share.")
    client = ScriptedClient(avoid, sorted_kinds=sorted_kinds)
    reference, own_town = check_conditions(client, [commute, far_right], ["DE"])
    (call,) = client.research_calls
    assert "far-right fascist supporter cities" in call["prompt"]
    assert reference.anchor.look_up == far_right and own_town.kind == "towns_to_avoid"
    assert [t.name for t in reference.anchor.avoided] == ["Görlitz"]


def test_the_size_still_counts_when_the_fact_about_the_places_can_t_be_checked():
    text = "at most 50 minutes to a big city where far-right parties are weak"
    sorted_kinds = {text: SortedCondition(
        text=text, understood_as="Within 50 minutes of such a city", kind="near",
        max_minutes=50, travel_mode="drive",
        anchor=SortedAnchor(description="big cities", min_share_of_country=0.003,
                            needs_the_web=True, look_up="far-right parties are weak"))}
    from jobcu.reference_places import ReferenceAnswers

    nothing = ReferenceAnswers(cities=[])
    (condition,) = check_conditions(ScriptedClient(nothing, sorted_kinds=sorted_kinds), [text],
                                    ["DE"])
    assert condition.kind == "near" and condition.anchor.min_share_of_country == 0.003
    assert condition.anchor.looked_up and condition.reference_status == "not_checked"
    assert "Missing cities remain unknown" in condition.note


def test_a_fact_without_a_size_counts_towns_big_enough_to_be_called_cities():
    text = "within 30 minutes of a city that isn't a far-right stronghold"
    sorted_kinds = {text: SortedCondition(
        text=text, understood_as="Within 30 minutes of such a city", kind="near",
        max_minutes=30, travel_mode="transit",
        anchor=SortedAnchor(description="cities that aren't far-right strongholds",
                            needs_the_web=True, look_up="far-right strongholds"))}
    avoid = CheckedCondition(understood_as="x", kind="towns_to_avoid",
                             towns=[TownRef(name="Dresden", country="DE")], confidence="checked",
                             note="")
    (condition,) = check_conditions(ScriptedClient(avoid, sorted_kinds=sorted_kinds), [text],
                                    ["DE"])
    assert condition.anchor.min_people == 20_000 and "20,000" in condition.note


def test_places_to_avoid_can_be_corrected():
    condition = near()
    condition.anchor.avoided = [TownRef(name="Dresden", country="DE"),
                                TownRef(name="Leipzig", country="DE")]
    plan = LocationPlan(text="", understood_as="", countries=["DE"], places=[],
                        conditions=[condition], not_checked_yet=[], outside_supported_area=[],
                        broad=False)
    corrected = apply_edits(ScriptedClient(None), plan, [
        ConditionEdit(text=OWNERS_TEXT, original=0, avoided=["Dresden"])]).conditions[0]
    assert [t.name for t in corrected.anchor.avoided] == ["Dresden"]
    assert corrected.changed_by_you
    assert "Leipzig" in {t.name for t in travel.anchor_towns(corrected.anchor, "DE")}


def test_whole_regions_to_avoid_can_be_corrected_too():
    condition = near()
    condition.anchor.avoided_regions = [PlaceRegion(code="DE.13", name="Saxony", country="DE")]
    plan = LocationPlan(text="", understood_as="", countries=["DE"], places=[],
                        conditions=[condition], not_checked_yet=[], outside_supported_area=[],
                        broad=False)
    edit = ConditionEdit(text=OWNERS_TEXT, original=0,
                         avoided=["All of Saxony", "All of Thüringen", "Except Leipzig", "Gera"])
    corrected = apply_edits(ScriptedClient(None), plan, [edit]).conditions[0]
    assert [r.name for r in corrected.anchor.avoided_regions] == ["Saxony", "Thuringia"]
    assert [t.name for t in corrected.anchor.exceptions] == ["Leipzig"]
    assert [t.name for t in corrected.anchor.avoided] == ["Gera"]
    towns = {t.name for t in travel.anchor_towns(corrected.anchor, "DE")}
    assert "Leipzig" in towns and "Dresden" not in towns and "Erfurt" not in towns


# --- Facts decided country by country -----------------------------------------------------


def test_a_fact_about_whole_countries_narrows_the_countries_searched():
    from jobcu.location import (
        LocationInterpretation,
        fits,
        interpret_location,
    )

    text = "a country in the top 10 for work-life balance"

    class CountryClient:
        research_calls = 0

        def generate(self, output, **request):
            if output is LocationInterpretation:
                return LocationInterpretation(
                    understood_as="Anywhere, in a top-10 work-life-balance country.",
                    limits_countries=False, countries=[], places=[],
                    conditions_about_places=[SortedCondition(
                        text=text, understood_as="Top-10 countries for work-life balance",
                        kind="needs_the_web")], conditions_about_the_job=[],
                    outside_supported_area=[])
            return CheckedCondition(understood_as="Top-10 work-life balance (OECD index)",
                                    kind="countries_that_fit", countries=["NL", "DK", "NO"],
                                    confidence="checked", note="OECD Better Life Index.")

        def research(self, **request):
            CountryClient.research_calls += 1
            from jobcu.ai.base import ResearchReply, Source, Usage
            return ResearchReply("notes", [Source("https://oecd.example/bli", "OECD")],
                                 Usage(1, 1))

    plan = interpret_location(CountryClient(), text)
    assert plan.countries == ["DK", "NL", "NO"] and not plan.broad
    (condition,) = plan.conditions
    assert condition.kind == "countries_that_fit" and condition.status == "applied"
    assert fits(condition, "NL", "Utrecht") == "yes" and fits(condition, "DE", "Berlin") == "no"
    assert CountryClient.research_calls == 1


def test_reference_places_can_be_limited_to_countries_by_a_fact():
    anchor = Anchor(min_people=500_000, countries_fit=["NL"])
    assert travel.anchor_towns(anchor, "DE") == []
    assert {"Amsterdam", "Rotterdam"} <= {t.name for t in travel.anchor_towns(anchor, "NL")}


def test_trips_go_to_the_nearest_edge_of_a_city_not_its_centre():
    # Search 9: Google gave Weichs to Munich's centre 53 minutes, so three PCB jobs there were
    # left out at "50 min"; the owner's search in the cloud left out four jobs in Weßling at
    # "Munich, 45 min". A reference place is where the person would live: any part of it.
    sampled = Sampled("Weßling, Oberbayern", first=45, edge=22, next_station=45)
    _, condition, job = measured_by(sampled, "Weßling, Oberbayern", minutes=40)
    assert condition_fit(condition, job) == "yes"
    latitude, longitude = sampled.asked(1)[0]
    wessling, munich = places.find("Weßling", "DE"), places.find("Munich", "DE")
    to_centre = places.distance_km(wessling, munich)
    to_sent = places.km(wessling.latitude, wessling.longitude, latitude, longitude)
    assert to_sent == pytest.approx(to_centre - places.reach_km(munich), abs=0.1)


def test_the_ai_estimates_the_trip_to_the_nearest_edge_too():
    class GuessingClient:
        def __init__(self):
            self.requests = []

        def generate(self, output, **request):
            self.requests.append(request)
            return TravelGuesses(answers=[TravelGuess(id="P0", town="Munich", minutes=20)])

    client = GuessingClient()
    condition = near(minutes=40)
    meter(key=False, client=client).measure([condition], [group("Weßling")], [0])
    assert "nearest edge" in client.requests[0]["system"]
    assert "Munich (edge 14 km)" in client.requests[0]["prompt"]
    # Estimates remembered to a town's centre before this change are not reused.
    assert travel._destination("DE", "Munich") == "DE:Munich:edge:wednesday-1030"


def test_a_citys_own_districts_are_not_reference_places_of_their_own():
    # Search 9: Hamburg's Wandsbek, Eimsbüttel and "Marienthal" (287,101 people) took both
    # "nearest" slots and showed on cards as "Marienthal, 53 min by car".
    towns = [town.name for town in travel.anchor_towns(near().anchor, "DE")]
    assert "Hamburg" in towns and "Munich" in towns and "Augsburg" in towns
    assert not {"Wandsbek", "Eimsbüttel", "Marienthal"} & set(towns)
    assert "London" in [town.name for town in travel.anchor_towns(near().anchor, "GB")]
    assert "Croydon" not in [town.name for town in travel.anchor_towns(
        near(share=0.001).anchor, "GB")]
    # Named places stay as the person named them.
    named = Anchor(named=[TownRef(name="Wandsbek", country="DE")])
    assert [town.name for town in travel.anchor_towns(named, "DE")] == ["Wandsbek"]


def test_a_rough_city_radius_cannot_prove_an_unnamed_workplace_is_in_the_city():
    condition = near(minutes=10)
    pasing = group("Somewhere", latitude=48.150, longitude=11.460)  # 9 km west of the centre
    fake = FakeMaps({"Munich": 15})
    meter(fake).measure([condition], [pasing], [0])
    assert fake.requests
    assert travel.home_town(travel.job_point(pasing), [places.find("Munich", "DE")]) is None
    assert "in Munich" != travel.detail(condition, pasing)[0]


def test_a_distance_limit_counts_from_the_citys_edge():
    condition = Condition(text="within 10 km of a big city", understood_as="Within 10 km",
                          status="applied", kind="near", max_km=10,
                          anchor=Anchor(named=[TownRef(name="Munich", country="DE")]))
    assert condition_fit(condition, group("Dachau")) == "yes"  # 17 km from the centre
    assert condition_fit(condition, group("Freising")) == "no"  # 33 km


def test_a_trip_to_the_city_centre_ends_at_the_centre_when_the_person_says_so():
    # README's own example: "not more than 50 minutes by public transport from a city centre".
    fake = FakeMaps({"Munich": 30})
    condition = near(minutes=40)
    condition.anchor.to_centre = True
    job = group("Weßling, Oberbayern")
    meter(fake).measure([condition], [job], [0])
    (_, body, _), = fake.requests
    sent = body["destinations"][0]["waypoint"]["location"]["latLng"]
    munich = places.find("Munich", "DE")
    assert (sent["latitude"], sent["longitude"]) == (munich.latitude, munich.longitude)
    assert len(body["destinations"]) == 2  # one centre for each of the two reference cities
    # A job 9 km from the centre is measured too, not counted as in the city.
    pasing = group("Somewhere", "2", latitude=48.150, longitude=11.460)
    assert travel.home_town(travel.job_point(pasing), [munich], to_centre=True) is None
    assert travel.home_town(travel.job_point(pasing), [munich]) is None
    by_km = Condition(text="within 10 km of Munich city centre", understood_as="…",
                      status="applied", kind="near", max_km=10,
                      anchor=Anchor(named=[TownRef(name="Munich", country="DE")], to_centre=True))
    assert condition_fit(by_km, group("Dachau")) == "no"  # 17 km from the centre
    assert travel._destination("DE", "Munich", centre=True) == "DE:Munich:centre:wednesday-1030"



def test_a_town_the_ad_names_goes_before_a_listing_of_several_workplaces():
    # Google's "Berlin (+1 other)" with an ad about Munich: no conflict, the job is in Munich.
    job = group("Berlin  (+\xa01 other)")
    assert travel.job_point(job).town == places.find("Berlin", "DE").name
    job.place_from_text = ["Munich"]
    assert not travel.workplace_conflict(job)
    assert travel.job_point(job).town == places.find("Munich", "DE").name
    # A listing of one workplace elsewhere stays a conflict to confirm.
    job.copies[0].location_text = "Berlin"
    assert travel.workplace_conflict(job)


def test_conflicting_ad_workplace_does_not_reuse_feed_point_or_old_journey():
    job = group("Berlin", latitude=52.52, longitude=13.405)
    job.place_from_text = ["Munich"]
    condition = near()
    condition.travel[travel.job_key(job)] = {"minutes": {"Berlin": 0}, "by": travel.MAPS}
    assert travel.workplace_conflict(job)
    assert travel.job_point(job) is None
    assert condition_fit(condition, job) == "unknown"
    # Updated original metadata may resolve the conflict without inventing a workplace.
    job.copies[0].location_text = "Munich"
    job.copies[0].latitude = job.copies[0].longitude = None
    assert not travel.workplace_conflict(job)
    assert travel.job_point(job).town == places.find("Munich", "DE").name
    # A nearby district spelling is not a conflict; distant alternative towns stay unresolved.
    job.place_from_text = ["Garching bei München"]
    assert not travel.workplace_conflict(job)
    job.place_from_text = ["Munich", "Berlin"]
    assert travel.workplace_conflict(job)
