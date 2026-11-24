"""SmartRecruiters career pages: a company's jobs grouped by place, and job pages with the standard
job data as page markup. Made-up companies, jobs and answers."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from jobcu import listmemory
from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.settings import Settings
from jobcu.sources import OPT_IN_SOURCES, TERMS_NOTES, disabled_sources, smartrecruiters
from jobcu.sources.base import JobQuery, SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer, keep_job
from jobcu.sources.http import PoliteClient

COMPANY = Employer("FakeCo", "smartrecruiters", "FakeCo", ("DE", "GB"), True)
JOBS = "https://jobs.smartrecruiters.com/FakeCo"
TERMS = [SearchTerm(text="power electronics", language="en", kind="job_title")]


def group(place, jobs):
    links = "".join(f'<li><a href="{JOBS}/{job_id}-x" class="details"><h4 class="details-title">'
                    f'{title}</h4></a></li>' for job_id, title in jobs)
    return (f'<section class="openings-section opening"><header><h3 class="opening-title title">'
            f'{place}</h3></header><ul>{links}</ul></section>')


def job_page(title, town="Regensburg", country="Germany", posted="2026-11-23T08:00:00.000Z"):
    return (f'<main itemscope itemtype="http://schema.org/JobPosting"><h1 itemprop="title">{title}'
            f'</h1><li itemprop="jobLocation" itemscope itemtype="http://schema.org/Place"><span '
            f'itemprop="address" itemscope itemtype="http://schema.org/PostalAddress"><meta '
            f'itemprop="addressCountry" content="{country}"><meta itemprop="addressLocality" '
            f'content="{town}"></span></li><li itemprop="employmentType">Full-time</li><meta '
            f'itemprop="datePosted" content="{posted}"><div itemprop="description"><p>Design '
            f'fictional converters. Requirements: a degree.</p></div></main>')


class Site:
    def __init__(self, pages, job_pages=None):
        self.pages, self.job_pages, self.asked = pages, job_pages or {}, []

    def __call__(self, request):
        self.asked.append((request.url.host, request.url.path))
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.host == "jobs.smartrecruiters.com":
            job_id = request.url.path.rsplit("/", 1)[-1].split("-")[0]
            return httpx.Response(200, text=self.job_pages.get(job_id, job_page("Some Job")))
        if request.url.path.endswith("/api/groups"):
            return httpx.Response(200, text=self.pages[int(request.url.params["page"])])
        return httpx.Response(200, text=f'<div data-groups-pages="{len(self.pages)}">'
                                        f'{self.pages[0]}</div>')


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("smartrecruiters", "s"), lambda: False,
                         lambda message: None)


def test_a_company_list_is_read_whole_each_job_once_with_its_place_in_a_supported_country():
    site = Site([group("Austin, TX", [(1, "Power Electronics Engineer")]),
                 group("Regensburg, Germany", [(1, "Power Electronics Engineer"), (2, "Nurse")])
                 + group("Leeds, United Kingdom", [(3, "Chef")])])
    jobs = smartrecruiters.SmartRecruitersSource()._list(COMPANY, context(site))
    assert [(job.title, job.location_text, job.country) for job in jobs] == [
        ("Power Electronics Engineer", "Regensburg, Germany", "DE"),
        ("Nurse", "Regensburg, Germany", "DE"), ("Chef", "Leeds, United Kingdom", "GB")]
    assert ("careers.smartrecruiters.com", "/FakeCo/api/groups") in site.asked


def test_a_company_page_that_leads_to_another_site_is_not_followed():
    asked = []

    def handler(request):
        asked.append(request.url.host)
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        return httpx.Response(302, headers={"location": "https://jobs.fakeco.example/en/"})

    with pytest.raises(SourceError):
        smartrecruiters.SmartRecruitersSource()._list(COMPANY, context(handler))
    assert "jobs.fakeco.example" not in asked


def test_matching_titles_are_read_from_their_pages_and_new_unmatched_titles_go_to_the_ai():
    now = datetime.now(UTC)
    start = now - timedelta(hours=24)
    first_list = [group("Regensburg, Germany", [(1, "Power Electronics Engineer"), (2, "Nurse")])]
    site = Site(first_list)
    found = list(smartrecruiters.SmartRecruitersSource().list_jobs(
        COMPANY, context(site), countries=["DE"], start=start, terms=TERMS))
    assert [job.title for job in found] == ["Some Job"]  # the page's own title
    full = found[0]
    assert full.description_is_complete and "fictional converters" in full.description
    assert full.date_precision == "exact" and full.posted_at.date().isoformat() == "2026-11-23"
    assert full.location_text == "Regensburg, Germany" and full.job_types

    listmemory.note("smartrecruiters", "FakeCo", [f"{JOBS}/1-x", f"{JOBS}/2-x"],
                    now - timedelta(hours=20))
    site = Site([group("Regensburg, Germany", [(1, "Power Electronics Engineer"), (2, "Nurse"),
                                               (5, "Test Bench Lead")])])
    later = list(smartrecruiters.SmartRecruitersSource().list_jobs(
        COMPANY, context(site), countries=["DE"], start=start, terms=TERMS))
    assert [job.title for job in later] == ["Some Job", "Test Bench Lead"]
    assert not [path for host, path in site.asked if host == "jobs.smartrecruiters.com"]
    query = JobQuery(countries=["DE"], places=[], terms=TERMS, posted_within_hours=24,
                     started_at=now)
    new = keep_job(later[1], COMPANY, query, start)
    assert new.title_unmatched and new.date_precision == "day"


def test_a_street_in_the_page_s_town_field_leaves_the_list_s_town():
    site = Site([group("Hannover, Germany", [(7, "Power Electronics Engineer")])],
                {"7": job_page("Power Electronics Engineer", town="Fictional Street 3-5")})
    [job] = smartrecruiters.SmartRecruitersSource().list_jobs(
        COMPANY, context(site), countries=["DE"], start=datetime.now(UTC) - timedelta(days=2),
        terms=TERMS)
    assert job.location_text == "Hannover, Germany"


def test_it_is_read_only_for_a_person_who_accepts_the_site_terms():
    assert "smartrecruiters" in OPT_IN_SOURCES and "terms" in TERMS_NOTES["smartrecruiters"]
    assert "smartrecruiters" in disabled_sources(Settings())
    assert "smartrecruiters" not in disabled_sources(Settings(source_opt_ins=["smartrecruiters"]))
