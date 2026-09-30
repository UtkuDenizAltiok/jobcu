"""Softgarden career sites, with a made-up employer and pages."""

import json
from datetime import UTC, date, datetime

import httpx
import pytest

from jobcu.freshness import day_at_utc
from jobcu.keystore import KeyStore
from jobcu.sources import all_sources, softgarden
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

EMPLOYER = Employer("Beispiel Power", "softgarden", "beispielpower", ("DE",))


def block(job_id, day, title, audience, *towns):
    places = "".join(f'<span class="location-view-item">{town}</span>' for town in towns)
    return (f'<div class="matchElement" id="job_id_{job_id}">'
            f'<div class="matchValue date">{day}</div><div class="matchValue title">'
            f'<a href="../job/{job_id}/words-?jobDbPVId=9&amp;l=de" target="_blank">{title}</a>'
            f'</div><div class="matchValue audience">{audience}</div>'
            f'<div class="matchValue ProjectGeoLocationCity"><div class="location-container">'
            f'{places}</div></div></div>')


LIST = ("<html><body>" + block(11, "01.09.26", "Entwicklungsingenieur (Hardware &amp; SMPS)*",
                               "Berufserfahrene", "Bad Lobenstein")
        + block(12, "15.09.26", "Werkstudent Marketing*", "Student/in", "München", "Berlin")
        + "</body></html>")
POSTING = {"@context": "https://schema.org", "@type": "JobPosting",
           "title": "Entwicklungsingenieur (Hardware & SMPS)",
           "description": "<p>Sie entwickeln Schaltnetzteile.</p>",
           "datePosted": "2026-09-01T08:35:57+02:00", "employmentType": "FULL_TIME",
           "hiringOrganization": {"name": "Beispiel Power GmbH"},
           "jobLocation": {"address": {"addressLocality": "Bad Lobenstein",
                                       "addressCountry": "DE"}}}


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("softgarden", "Softgarden"),
                         lambda: False, lambda message: None)


def site(request):
    assert request.url.host == "beispielpower.softgarden.io"
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text="User-agent: *\nDisallow: /api/\nDisallow: /*/widgets/\n")
    if request.url.path == "/de/vacancies":
        return httpx.Response(200, text=LIST)
    page = f'<script type="application/ld+json">{json.dumps(POSTING)}</script>'
    return httpx.Response(200, text=page)


def test_the_list_page_gives_titles_days_towns_and_audiences():
    first, second = softgarden.SoftgardenSource().list_jobs(EMPLOYER, context(site))
    assert first.title == "Entwicklungsingenieur (Hardware & SMPS)*"
    assert first.url == "https://beispielpower.softgarden.io/job/11/words-"
    assert first.source_job_id == "beispielpower/11" and first.company == "Beispiel Power"
    assert first.posted_at == day_at_utc(date(2026, 9, 1)) and first.date_precision == "day"
    assert first.location_text == "Bad Lobenstein" and first.job_types == []
    assert second.location_text == "München, Berlin"
    assert second.job_types == ["internship_or_working_student"]


def test_the_job_page_gives_the_full_ad_and_the_exact_time():
    source = softgarden.SoftgardenSource()
    ctx = context(site)
    job = source.load_details(next(source.list_jobs(EMPLOYER, ctx)), ctx)
    assert job.description == "Sie entwickeln Schaltnetzteile." and job.description_is_complete
    assert job.posted_at == datetime(2026, 9, 1, 6, 35, 57, tzinfo=UTC)
    assert job.date_precision == "exact"


def test_a_site_whose_robots_txt_closes_the_list_is_not_read():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /\n")
        raise AssertionError("the list must not be asked for")

    with pytest.raises(SourceError):
        list(softgarden.SoftgardenSource().list_jobs(EMPLOYER, context(handler)))


def test_it_is_one_of_the_career_systems_with_employers_in_the_directory():
    assert any(isinstance(source, softgarden.SoftgardenSource) for source in all_sources())
