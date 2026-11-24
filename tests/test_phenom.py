"""Phenom career sites: the site's own search answers with each country's jobs and their posting
days; a job's page has the full ad. Made-up companies, jobs and answers."""

import json
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.settings import Settings
from jobcu.sources import OPT_IN_SOURCES, TERMS_NOTES, disabled_sources, phenom
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

BOARD = "careers.fake.example/global/en"
COMPANY = Employer("FakeCo", "phenom", BOARD, ("DE", "GB"), True)


def job(number, title, country="Germany", places=None, posted="2026-11-20T00:00:00.000+0000"):
    return {"jobId": number, "title": title, "country": country, "postedDate": posted,
            "multi_location": places or [f"Erlangen, Bavaria, {country}"], "type": "Full Time",
            "descriptionTeaser": "Design fictional converters..."}


class Site:
    def __init__(self, lists, robots="User-agent: *\nDisallow: */px-widgets\n", page=None):
        self.lists, self.robots, self.page, self.bodies = lists, robots, page, []

    def __call__(self, request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=self.robots)
        if request.url.path.startswith("/global/en/job/"):
            return httpx.Response(200, text=self.page or "")
        body = json.loads(request.content)
        self.bodies.append(body)
        countries = (body["selected_fields"] or {}).get("country") or []
        jobs = [j for name in countries for j in self.lists.get(name, [])]
        counts = {name: len(found) for name, found in self.lists.items()}
        start = body["from"]
        return httpx.Response(200, json={"refineSearch": {
            "totalHits": len(jobs) if countries else sum(counts.values()),
            "data": {"jobs": jobs[start:start + body["size"]],
                     "aggregations": [{"field": "country", "value": counts}]}}})


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("phenom", "phenom"), lambda: False,
                         lambda message: None)



def test_each_searched_country_s_list_is_read_whole_in_the_site_s_own_words(monkeypatch):
    monkeypatch.setattr(phenom, "PAGE_SIZE", 2)
    site = Site({"Deutschland": [job("A1", "Power Electronics Engineer"), job("A2", "Nurse"),
                                 job("A3", "Chef", places=["Lyon, France", "Erlangen, Germany"])],
                 "United Kingdom": [job("B1", "Teacher", country="United Kingdom",
                                        places=["Leeds, United Kingdom"])],
                 "Brazil": [job("C1", "Engineer", country="Brazil")]})
    jobs = list(phenom.PhenomSource().list_jobs(COMPANY, context(site), countries=["DE"],
                                                start=datetime.now(UTC), terms=[]))
    assert [j.title for j in jobs] == ["Power Electronics Engineer", "Nurse", "Chef"]
    assert {b["selected_fields"].get("country", [None])[0] for b in site.bodies} == {
        None, "Deutschland"}
    assert [b["from"] for b in site.bodies if b["selected_fields"]] == [0, 2]
    assert site.bodies[0]["lang"] == "en_global" and site.bodies[0]["country"] == "global"
    first = jobs[0]
    assert first.country == "DE" and first.date_precision == "day"
    assert first.posted_at.date() == date(2026, 11, 20)
    assert first.url == "https://careers.fake.example/global/en/job/A1"
    assert first.job_types == ["full_time_permanent", "fixed_term"]
    assert not first.description_is_complete
    # A job in several places, one of them in Germany, is on Germany's list with all of them.
    assert jobs[2].location_text == "Lyon, France; Erlangen, Germany"


def test_a_job_s_page_gives_the_full_ad_and_only_an_earlier_day():
    page = ('<script type="application/ld+json">' + json.dumps({
        "@type": "JobPosting", "title": "Power Electronics Engineer", "datePosted": "2026-11-23",
        "description": "<p>The full fictional ad.</p>"}) + "</script>")
    site = Site({"Germany": [job("A1", "Power Electronics Engineer")]}, page=page)
    source = phenom.PhenomSource()
    ctx = context(site)
    [listed] = source.list_jobs(COMPANY, ctx, countries=["DE"], start=datetime.now(UTC),
                                terms=[])
    full = source.load_details(listed, ctx)
    assert full.description == "The full fictional ad." and full.description_is_complete
    assert full.posted_at.date() == date(2026, 11, 20)  # the page's later day is an update
    site.page = page.replace("2026-11-23", "2026-10-01")
    earlier = phenom.PhenomSource().load_details(listed, context(site))
    assert earlier.posted_at.date() == date(2026, 10, 1)


def test_robots_txt_is_respected():
    site = Site({"Germany": [job("A1", "Engineer")]}, robots="User-agent: *\nDisallow: /widgets\n")
    with pytest.raises(SourceError):
        list(phenom.PhenomSource().list_jobs(COMPANY, context(site), countries=["DE"],
                                             start=datetime.now(UTC) - timedelta(days=1),
                                             terms=[]))
    assert not site.bodies


def test_the_directory_check_takes_the_site_s_own_counts():
    site = Site({"Germany": [job("A1", "Engineer")] * 3, "Ireland": [job("B1", "Nurse")],
                 "Brazil": [job("C1", "Chef")]})
    survey = phenom.PhenomSource().survey(COMPANY, context(site))
    assert dict(survey.counts) == {"DE": 3, "IE": 1, "other": 1}


def test_it_is_read_only_for_a_person_who_accepts_the_site_terms():
    assert "phenom" in OPT_IN_SOURCES and "terms" in TERMS_NOTES["phenom"]
    assert "phenom" in disabled_sources(Settings())
    assert "phenom" not in disabled_sources(Settings(source_opt_ins=["phenom"]))
