"""Personio career sites, with a made-up employer and answers."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.sources import all_sources, personio
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

EMPLOYER = Employer("Beispiel Antriebe", "personio", "beispiel-antriebe", ("DE",))
LIST = [
    {"id": 11, "name": "Leistungselektronik Entwickler (m/w/d)", "employment_type":
     "Festanstellung", "schedule": "Vollzeit", "office": "Starnberg",
     "offices": ["Starnberg"]},
    {"id": 12, "name": "Einkäufer (m/w/d)", "employment_type": "Festanstellung",
     "schedule": "Teilzeit", "office": "Starnberg", "offices": ["Starnberg"]},
    {"id": 13, "name": "", "office": "Starnberg"},
]
PAGE = ("<html><script>self.__next_f.push([1,\"{\\\"published_at\\\":\\\"2026-09-29T08:00:00Z\\\","
        "\\\"created_at\\\":\\\"2026-09-01T08:00:00Z\\\"}\"])</script><body>"
        "<nav>Skip to main content</nav><h1>Leistungselektronik Entwickler (m/w/d)</h1>"
        "<p>Du entwickelst Wechselrichter.</p><ul><li>SiC</li></ul></body></html>")


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("personio", "Personio"),
                         lambda: False, lambda message: None)


def site(asked):
    def handler(request):
        asked.append(request.url.path)
        assert request.url.host == "beispiel-antriebe.jobs.personio.de"
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/search.json":
            return httpx.Response(200, json=LIST)
        return httpx.Response(200, text=PAGE)

    return handler


def test_the_list_gives_every_job_without_opening_pages():
    asked = []
    jobs = list(personio.PersonioSource().list_jobs(EMPLOYER, context(site(asked))))
    assert [job.title for job in jobs] == ["Leistungselektronik Entwickler (m/w/d)",
                                          "Einkäufer (m/w/d)"]
    first = jobs[0]
    assert first.url == "https://beispiel-antriebe.jobs.personio.de/job/11"
    assert first.source_job_id == "beispiel-antriebe/11" and first.location_text == "Starnberg"
    assert first.job_types == ["full_time_permanent"] and jobs[1].job_types == ["part_time"]
    assert first.posted_at is None and first.date_precision == "unknown"
    assert asked == ["/robots.txt", "/search.json"]


def test_a_search_opens_only_matching_pages_for_the_ad_and_date_and_remembers_them():
    terms = [SearchTerm(text="Leistungselektronik", language="de", kind="job_title")]
    start = datetime(2026, 9, 27, tzinfo=UTC)
    asked = []
    source = personio.PersonioSource()
    [job] = source.list_jobs(EMPLOYER, context(site(asked)), countries=["DE"], start=start,
                             terms=terms)
    assert job.posted_at == datetime(2026, 9, 29, 8, tzinfo=UTC)
    assert job.date_precision == "exact" and job.description_is_complete
    assert job.description == "Du entwickelst Wechselrichter.\n• SiC"
    assert asked == ["/robots.txt", "/search.json", "/job/11"]
    # The next search reads the ad from memory instead of opening the page again.
    asked.clear()
    list(personio.PersonioSource().list_jobs(EMPLOYER, context(site(asked)), countries=["DE"],
                                             start=start - timedelta(days=1), terms=terms))
    assert "/job/11" not in asked


def test_a_site_whose_robots_txt_closes_the_list_is_not_read():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        raise AssertionError("the list must not be asked for")

    with pytest.raises(SourceError):
        list(personio.PersonioSource().list_jobs(EMPLOYER, context(handler)))


def test_it_is_one_of_the_career_systems_with_employers_in_the_directory():
    assert any(isinstance(source, personio.PersonioSource) for source in all_sources())
