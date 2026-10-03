"""Job sitemaps with JobPosting pages (sources/sitemaps.py), with a made-up recruiter's site."""

from datetime import UTC, datetime, timedelta

import httpx

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.sources import careers, sitemaps
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

NOW = datetime.now(UTC)
DAY = timedelta(days=1)


def stamp(when):
    return when.date().isoformat()


INDEX = """<?xml version="1.0"?><sitemapindex>
<sitemap><loc>https://recruit.test/sitemap_blogs.xml</loc></sitemap>
<sitemap><loc>https://recruit.test/sitemap_jobs.xml</loc></sitemap></sitemapindex>"""

JOBS = f"""<?xml version="1.0"?><urlset>
<url><loc>https://recruit.test/job-details/power-electronics-engineer-london</loc>
<lastmod>{stamp(NOW)}</lastmod></url>
<url><loc>https://recruit.test/job-details/electronics-engineer-old-ad</loc>
<lastmod>{stamp(NOW - 20 * DAY)}</lastmod></url>
<url><loc>https://recruit.test/job-details/payroll-administrator-leeds</loc>
<lastmod>{stamp(NOW)}</lastmod></url>
<url><loc>https://recruit.test/jobs/27724/graduate-electronics-engineer</loc></url>
<url><loc>https://recruit.test/about-us</loc><lastmod>{stamp(NOW)}</lastmod></url>
</urlset>"""


def page(title, town, country, posted):
    return (f'<html><script type="application/ld&#x2B;json">{{"@type": "JobPosting", '
            f'"title": "{title}", "datePosted": "{posted.isoformat()}", '
            f'"description": "<p>Design SMPS.\nTest them.</p>", "employmentType": "FULL_TIME", '
            f'"hiringOrganization": {{"name": "Recruit Group Ltd"}}, "jobLocation": '
            f'{{"address": {{"addressLocality": "{town}", "addressCountry": "{country}"}}}}}}'
            f'</script></html>')


PAGES = {
    "/job-details/power-electronics-engineer-london":
        page("Power Electronics Engineer", "London", "GB", NOW - timedelta(hours=5)),
    "/job-details/electronics-engineer-old-ad":
        page("Electronics Engineer", "Leeds", "GB", NOW - 20 * DAY),
    "/job-details/payroll-administrator-leeds":
        page("Payroll Administrator", "Leeds", "GB", NOW - timedelta(hours=3)),
    "/jobs/27724/graduate-electronics-engineer":
        page("Graduate Electronics Engineer", "Nottingham", "United Kingdom", NOW - DAY),
}


def site(requested):
    def handler(request):
        path = request.url.path
        requested.append(path)
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /admin/\n")
        if path == "/sitemap.xml":
            return httpx.Response(200, text=INDEX)
        if path == "/sitemap_jobs.xml":
            return httpx.Response(200, text=JOBS)
        if path in PAGES:
            return httpx.Response(200, text=PAGES[path])
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("sitemap", "Sitemaps"), lambda: False,
                         lambda message: None)


def test_fresh_matching_job_pages_are_read_from_the_sitemap(monkeypatch):
    recruiter = Employer("Recruit Group", "sitemap", "https://recruit.test/sitemap.xml", ("GB",),
                         False)
    monkeypatch.setattr(careers, "load_directory", lambda: (recruiter,))
    terms = [SearchTerm(text="Electronics Engineer", language="en", kind="job_title")]
    query = JobQuery(["GB"], [], terms, 72, NOW)
    requested = []
    jobs = list(sitemaps.SitemapSource().search(query, site(requested)))
    assert sorted(job.title for job in jobs) == [
        "Graduate Electronics Engineer", "Power Electronics Engineer"]
    london = next(job for job in jobs if job.location_text == "London")
    assert london.country == "GB" and london.company == "Recruit Group Ltd"
    assert london.description_is_complete and "Test them" in london.description
    assert london.date_precision == "exact" and london.job_types
    assert next(job for job in jobs if job.location_text == "Nottingham").country == "GB"
    # The old ad and the unrelated one were never opened; the blog sitemap wasn't read.
    assert "/job-details/electronics-engineer-old-ad" not in requested
    assert "/job-details/payroll-administrator-leeds" not in requested
    assert "/sitemap_blogs.xml" not in requested

    # The next search takes the pages from the ad memory.
    requested.clear()
    again = list(sitemaps.SitemapSource().search(query, site(requested)))
    assert sorted(job.title for job in again) == sorted(job.title for job in jobs)
    assert not any(path.startswith(("/job-details/", "/jobs/")) for path in requested)


def test_the_directory_check_looks_at_a_few_pages_for_the_countries():
    recruiter = Employer("Recruit Group", "sitemap", "https://recruit.test/sitemap.xml", ())
    source = sitemaps.SitemapSource()
    ctx = site([])
    survey = source.survey(recruiter, ctx)
    assert survey.counts["GB"] == 4
    assert source.readable(recruiter, ctx)


def test_countries_and_address_words():
    assert sitemaps.country_code("UK") == "GB" and sitemaps.country_code("Deutschland") == "DE"
    assert sitemaps.country_code("Atlantis") is None and sitemaps.country_code(None) is None
    assert "graduate electronics engineer" in sitemaps.words_of(
        "https://recruit.test/jobs/27724/graduate-electronics-engineer")
    assert "Hardwareentwickler" in sitemaps.words_of(
        "https://jobs.test/stellen/Hardwareentwickler%20%28m-w-d%29")
