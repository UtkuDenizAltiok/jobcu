"""Jobvite career sites (sources/jobvite.py): a company's list page and job pages with JobPosting
data, read only for a person who accepts Jobvite's terms. A made-up company and answers."""

import json
from datetime import UTC, datetime, timedelta

import httpx

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.settings import Settings
from jobcu.sources import OPT_IN_SOURCES, TERMS_NOTES, careers, disabled_sources, jobvite
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.careerlinks import board_in_job_link
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

NOW = datetime.now(UTC)


def row(job_id, title, place):
    return (f'<tr><td class="jv-job-list-name"><a href="/example-power/job/{job_id}">{title}</a>'
            f'</td><td class="jv-job-list-location">{place}</td></tr>')


LIST = ('<html><h3>Engineering</h3><table class="jv-job-list"><tbody>'
        + row("oGate001", "Hardware Engineer Gate Drivers", "Exampleburg,\n Germany")
        + row("oPay0002", "Payroll Specialist", "San Jose,\n California")
        + "</tbody></table></html>")


def job_page(title, country, posted):
    return ('<script type="application/ld+json">' + json.dumps({
        "@context": "http://schema.org", "@type": "JobPosting", "title": title,
        "datePosted": posted.date().isoformat(), "hiringOrganization": "Example Power",
        "description": "<p>Design fictional gate drivers for fictional power modules.</p>",
        "jobLocation": [{"@type": "Place", "address": {"addressCountry": country}}]})
        + "</script>")


def site(requested):
    def handler(request):
        requested.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.path == "/example-power/jobs":
            return httpx.Response(200, text=LIST)
        if request.url.path == "/example-power/job/oGate001":
            return httpx.Response(200, text=job_page("Hardware Engineer Gate Drivers", "Germany",
                                                     NOW - timedelta(hours=3)))
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("jobvite", "Jobvite"), lambda: False,
                         lambda message: None)


def test_a_jobvite_company_s_matching_jobs_are_read_from_its_list_and_job_pages(monkeypatch):
    # The directory gives only the list's address: Jobvite's job page pattern is known.
    company = Employer("Example Power", "jobvite", "https://jobs.jobvite.com/example-power/jobs",
                       ("DE",), True)
    monkeypatch.setattr(careers, "load_directory", lambda: (company,))
    terms = [SearchTerm(text="Hardware Engineer", language="en", kind="job_title")]
    requested = []
    jobs = list(jobvite.JobviteSource().search(JobQuery(["DE"], [], terms, 24, NOW),
                                               site(requested)))
    assert [(job.title, job.country, job.company) for job in jobs] == [
        ("Hardware Engineer Gate Drivers", "DE", "Example Power")]
    assert jobs[0].url == "https://jobs.jobvite.com/example-power/job/oGate001"
    assert "fictional gate drivers" in jobs[0].description
    assert "/example-power/job/oPay0002" not in requested  # abroad and unmatched: never opened


def test_it_is_read_only_for_a_person_who_accepts_jobvite_s_terms():
    assert "jobvite" in OPT_IN_SOURCES and "terms" in TERMS_NOTES["jobvite"]
    assert "jobvite" in disabled_sources(Settings())
    assert "jobvite" not in disabled_sources(Settings(source_opt_ins=["jobvite"]))


def test_a_jobvite_job_link_names_its_company_s_list():
    assert board_in_job_link("https://jobs.jobvite.com/example-power/job/oGate001") == (
        "jobvite", "https://jobs.jobvite.com/example-power/jobs")
    assert jobvite.job_pattern("https://jobs.jobvite.com/example-power/jobs") == (
        r"jobs\.jobvite\.com/example\-power/job/(\w+)")
