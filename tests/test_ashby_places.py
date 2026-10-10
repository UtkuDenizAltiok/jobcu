"""Fictional structured workplaces through collection and location-check selection."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest

from jobcu import jobplace, jobstore, pipeline, places, travel
from jobcu.countries import COUNTRIES
from jobcu.dedupe import JobGroup
from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.location import Place
from jobcu.sources import careers
from jobcu.sources.ashby import AshbySource, to_found_job
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.careers import Employer, keep_job
from jobcu.sources.http import PoliteClient

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)
COMPANY = Employer("Example Services", "ashby", "example", tuple(COUNTRIES), elsewhere=True)


def posting(**changes):
    return {
        "id": "fictional-42", "title": "Staff Nurse", "location": "Office",
        "jobUrl": "https://example.test/jobs/42", "publishedAt": NOW.isoformat(),
        "descriptionPlain": "Provide nursing care. Professional registration required.",
        "employmentType": "FullTime", "workplaceType": "OnSite", **changes,
    }


def selected(item, country, city=None):
    wanted = [] if city is None else [Place(
        name=city, local_name=city, country=country, kind="city", radius_km=None)]
    query = JobQuery([country], wanted, [SearchTerm(
        text=item["title"], language="en", kind="job_title")], 24, NOW)
    return keep_job(to_found_job(item, COMPANY), COMPANY, query, NOW - timedelta(hours=24))


@pytest.mark.parametrize("country", COUNTRIES)
@pytest.mark.parametrize("secondary", [False, True], ids=["primary", "secondary"])
def test_structured_workplaces_survive_country_and_city_selection(country, secondary):
    town = places.towns_in(country)[0]
    address = {"addressLocality": town.name, "addressCountry": COUNTRIES[country].name}
    item = posting(address={"postalAddress": address})
    if secondary:
        item = posting(location="Overseas office", address={"postalAddress": {
            "addressCountry": "USA"}}, secondaryLocations=[
                {"location": "European office", "address": address}])
    job = selected(item, country, town.name)
    assert job is not None and job.country == country
    assert job.source_job_id == "fictional-42" and not job.title_unmatched
    assert job.description_is_complete and job.description == item["descriptionPlain"]
    point = travel.job_point(JobGroup([job], {"ashby": "employer"}))
    assert point is not None and point.country == country and point.town == town.name


@pytest.mark.parametrize("title,description", [
    ("Staff Nurse", "Provide nursing care. Professional registration required."),
    ("Primary Teacher", "Teach primary classes. Teaching qualification required."),
    ("Hardware Engineer", "Design electronic circuits. German C1 required."),
])
def test_source_locality_avoids_redundant_research_without_losing_requirements(title, description):
    item = posting(title=title, descriptionPlain=description, address={"postalAddress": {
        "addressLocality": "Cork", "addressCountry": "Ireland"}})
    job = selected(item, "IE")
    assert job is not None
    group = JobGroup([job], {"ashby": "employer"})
    assert not travel.needs_place(group)
    assert not jobplace.needs_looking_up(group)
    assert not jobplace.needs_requirements(group, {"score": 90, "evidence": {}})
    assert group.best_description_copy.description == description
    assert job.posted_at == NOW and job.date_precision == "exact"
    assert job.url == item["jobUrl"] and job.work_mode == "on_site"


def test_legacy_nested_secondary_address_and_free_text_are_preserved():
    item = posting(location="Main office", secondaryLocations=[{
        "location": "Partner clinic", "address": {"postalAddress": {
            "addressLocality": "Dublin", "addressRegion": "Leinster",
            "addressCountry": "Ireland"}}}])
    job = selected(item, "IE", "Dublin")
    assert job is not None
    assert "Main office" in job.location_text and "Partner clinic" in job.location_text
    assert "Dublin" in job.location_text


def test_multiple_secondary_countries_keep_the_requested_one():
    item = posting(location="US office", address={"postalAddress": {"addressCountry": "USA"}},
                   secondaryLocations=[
                       {"location": "German clinic", "address": {
                           "addressLocality": "Berlin", "addressCountry": "Germany"}},
                       {"location": "Irish clinic", "address": {
                           "addressLocality": "Cork", "addressCountry": "Ireland"}}])
    assert selected(item, "IE", "Cork") is not None
    assert selected(item, "DE", "Berlin") is not None
    assert selected(item, "GB") is None


def test_a_region_without_a_town_stays_unknown_for_online_checks():
    item = posting(address={"postalAddress": {
        "addressRegion": "Bayern", "addressCountry": "Germany"}})
    job = selected(item, "DE")
    assert job is not None
    group = JobGroup([job], {"ashby": "employer"})
    assert travel.job_point(group) is None and jobplace.needs_looking_up(group)


@pytest.mark.parametrize("country,region", [("IE", "Cork"), ("DE", "Berlin")])
def test_a_structured_region_sharing_a_town_name_does_not_invent_a_workplace(country, region):
    job = selected(posting(address={"postalAddress": {
        "addressRegion": region, "addressCountry": COUNTRIES[country].name}}), country)
    assert job is not None
    group = JobGroup([job], {"ashby": "employer"})
    assert travel.job_point(group) is None and jobplace.needs_looking_up(group)


def test_a_structured_region_does_not_override_a_stated_locality():
    job = selected(posting(address={"postalAddress": {
        "addressLocality": "Cork", "addressRegion": "Dublin", "addressCountry": "Ireland"}}),
        "IE")
    assert travel.job_point(JobGroup([job], {"ashby": "employer"})).town == "Cork"


@pytest.mark.parametrize("address", [None, [], "invalid", {"postalAddress": []}, {
    "postalAddress": {"addressLocality": None, "addressRegion": [], "addressCountry": 123}}])
def test_malformed_optional_addresses_do_not_destroy_usable_location_text(address):
    job = to_found_job(posting(location="Cork, Ireland", address=address,
                               secondaryLocations=[None, "invalid", {}]), COMPANY)
    assert job.location_text == "Cork, Ireland"
    assert job.description_is_complete


def test_duplicate_address_words_do_not_repeat():
    job = to_found_job(posting(location="Cork", address={"postalAddress": {
        "addressLocality": " Cork ", "addressCountry": "Ireland"}}), COMPANY)
    assert job.location_text == "Cork, Ireland"


def test_existing_list_request_keeps_the_irish_secondary_job_without_extra_reading(monkeypatch):
    item = posting(location="US office", address={"postalAddress": {"addressCountry": "USA"}},
                   secondaryLocations=[{"location": "Partner clinic", "address": {
                       "addressLocality": "Cork", "addressCountry": "Ireland"}}])
    requests = []

    def handler(request):
        requests.append(request.url.path)
        assert request.url.path == "/posting-api/job-board/example"
        return httpx.Response(200, json={"jobs": [item, posting(id="hidden", isListed=False)]})

    monkeypatch.setattr(careers, "load_directory", lambda: (COMPANY,))
    monkeypatch.setattr(careers, "found_employers", lambda: ())
    http = PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler))
    report = SourceReport("ashby", "Ashby")
    ctx = SourceContext(http, KeyStore(), report, lambda: False, lambda message: None)
    query = JobQuery(["IE"], [], [SearchTerm(
        text="Staff Nurse", language="en", kind="job_title")], 24, NOW)
    try:
        found = list(AshbySource().search(query, ctx))
        assert len(found) == 1 and found[0].source_job_id == "fictional-42"
        group = JobGroup(found, {"ashby": "employer"})
        assert not jobplace.needs_looking_up(group)
        assert not jobplace.needs_requirements(group, {"score": 90, "evidence": {}})
        assert requests == ["/posting-api/job-board/example"] and report.requests == 1
    finally:
        http.close()


def test_old_full_text_cache_cannot_restore_discarded_workplace_evidence():
    legacy = selected(posting(location="Ireland", descriptionPlain="Full nursing requirements"),
                      "IE")
    jobstore.remember_ad(legacy, reader_version=1)
    fresh = selected(posting(descriptionPlain="", address={"postalAddress": {
        "addressLocality": "Cork", "addressCountry": "Ireland"}}), "IE")
    group = JobGroup([fresh], {"ashby": "employer"})
    collected = pipeline.Collected([fresh], [SourceReport("ashby", "Ashby")],
                                   {"ashby": AshbySource()})
    http = PoliteClient(transport=httpx.MockTransport(
        lambda request: pytest.fail("This source supplies its ad in the list; no detail traffic")))
    try:
        pipeline.load_full_ads([group], [0], collected, http, KeyStore(),
                               SimpleNamespace(stop_requested=False, update=lambda *args: None))
        assert group.main.location_text == "Office, Cork, Ireland"
        assert group.main.description == "" and not group.main.description_is_complete
        assert not jobplace.needs_looking_up(group)
        assert collected.reports[0].requests == 0
    finally:
        http.close()


def test_corrected_full_text_cache_remains_reusable():
    job = selected(posting(address={"postalAddress": {
        "addressLocality": "Cork", "addressCountry": "Ireland"}}), "IE")
    jobstore.remember_ad(job, reader_version=AshbySource.detail_cache_version)
    cached = jobstore.remembered_ad(job, reader_version=AshbySource.detail_cache_version)
    assert cached is not None and cached.description == job.description
    assert cached.location_text == job.location_text and cached.country == "IE"
