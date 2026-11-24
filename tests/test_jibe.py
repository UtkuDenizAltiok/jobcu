"""Jibe career sites: the site's own search lists each country's jobs newest first, with the
full ad. Made-up companies, jobs and answers."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.settings import Settings
from jobcu.sources import OPT_IN_SOURCES, disabled_sources, jibe
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

COMPANY = Employer("FakeCo", "jibe", "careers.fake.example", ("DE", "GB"), True)
NOW = datetime.now(UTC)


def record(slug, title, days_ago, place="Erlangen, Germany", code="DE", form="%B %d, %Y"):
    return {"data": {"slug": slug, "req_id": slug, "title": title,
                     "posted_date": (NOW - timedelta(days=days_ago)).strftime(form),
                     "full_location": place, "country_code": code, "employment_type": "FULL_TIME",
                     "description": "<p>Design fictional converters.</p>",
                     "qualifications": "<p>A degree.</p>"}}


def site(pages, robots="User-agent: *\nAllow: /\n", asked=None):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots)
        if asked is not None:
            asked.append(dict(request.url.params))
        page = int(request.url.params["page"])
        jobs = pages[page - 1] if page <= len(pages) else []
        return httpx.Response(200, json={"jobs": jobs, "totalCount": sum(map(len, pages))})
    return handler


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("jibe", "jibe"), lambda: False,
                         lambda message: None)


def test_a_country_s_list_is_read_newest_first_until_a_page_of_older_jobs(monkeypatch):
    monkeypatch.setattr(jibe, "PAGE_SIZE", 2)
    asked = []
    pages = [[record("1", "Power Electronics Engineer", 0), record("2", "Nurse", 1)],
             [record("3", "Chef", 9), record("4", "Teacher", 10)],
             [record("5", "Baker", 20), record("6", "Driver", 30)]]
    jobs = list(jibe.JibeSource().list_jobs(COMPANY, context(site(pages, asked=asked)),
                                            countries=["DE"], start=NOW - timedelta(days=3)))
    assert [job.title for job in jobs] == ["Power Electronics Engineer", "Nurse", "Chef", "Teacher"]
    assert [params["page"] for params in asked] == ["1", "2"]
    assert asked[0]["location"] == "Germany" and asked[0]["sortBy"] == "posted_date"
    first = jobs[0]
    assert first.country == "DE" and first.date_precision == "day"
    assert first.posted_at.date() == NOW.date()
    assert first.description_is_complete and "A degree." in first.description
    assert first.url == "https://careers.fake.example/jobs/1"
    assert first.job_types == ["full_time_permanent", "fixed_term"]


def test_an_iso_posting_time_and_a_job_in_several_countries():
    pages = [[record("7", "Analyst", 0, place="Warsaw, Poland; Germany", code="PL",
                     form="%Y-%m-%dT%H:%M:%S+0000")]]
    [job] = jibe.JibeSource().list_jobs(COMPANY, context(site(pages)), countries=["DE"],
                                        start=NOW - timedelta(days=1))
    # Listed for Germany among its places: Germany is its country here.
    assert job.country == "DE" and job.date_precision == "exact"
    assert job.posted_at.date() == NOW.date()


def test_robots_txt_is_respected():
    with pytest.raises(SourceError):
        list(jibe.JibeSource().list_jobs(
            COMPANY, context(site([[record("1", "Engineer", 0)]],
                                  robots="User-agent: *\nDisallow: /api/\n")),
            countries=["DE"], start=NOW))


def test_the_directory_check_counts_each_country_s_list():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        total = {"Germany": 12, "Ireland": 3}.get(request.url.params["location"], 0)
        return httpx.Response(200, json={"jobs": [], "totalCount": total})
    survey = jibe.JibeSource().survey(COMPANY, context(handler))
    assert dict(survey.counts) == {"DE": 12, "IE": 3}


def test_it_runs_by_default():
    assert "jibe" not in OPT_IN_SOURCES and "jibe" not in disabled_sources(Settings())
