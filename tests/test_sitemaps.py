"""Job sitemaps with JobPosting pages (sources/sitemaps.py), with a made-up recruiter's site."""

import dataclasses
import json
import sys
from datetime import UTC, datetime, timedelta

import httpx

from jobcu import jobstore, scoring
from jobcu.dedupe import JobGroup
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


LANGUAGES = ("de", "en", "it", "fr", "pt_br")
MULTILINGUAL = "<?xml version='1.0'?><urlset>" + "".join(
    f"<url><loc>https://group.test/{language}/job/{slug}</loc><lastmod>{stamp(NOW)}</lastmod></url>"
    for slug in ("hardwareentwickler_elektronik__m_w_d_/101", "elektronikentwickler__m_w_d_/102")
    for language in LANGUAGES) + "</urlset>"


def multilingual_site(requested):
    def handler(request):
        path = request.url.path
        requested.append(path)
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /it/job/\nDisallow: /fr/job/"
                                            "\nDisallow: /pt_br/job/\n")
        if path == "/sitemap.xml":
            return httpx.Response(200, text=MULTILINGUAL)
        if "/job/" in path:
            title = "Hardwareentwickler Elektronik" if "/101" in path else "Elektronikentwickler"
            return httpx.Response(200, text=page(title, "Kiel", "Germany", NOW - DAY))
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("sitemap", "Sitemaps"), lambda: False,
                         lambda message: None)


def test_a_job_listed_in_many_languages_is_opened_once_in_the_searched_countrys_language(
        monkeypatch):
    group = Employer("Example Group", "sitemap", "https://group.test/sitemap.xml", ("DE",))
    monkeypatch.setattr(careers, "load_directory", lambda: (group,))
    monkeypatch.setattr(sitemaps, "MAX_PAGES", 2)
    terms = [SearchTerm(text="Elektronikentwickler", language="de", kind="job_title"),
             SearchTerm(text="Hardwareentwickler", language="de", kind="job_title")]
    requested = []
    jobs = list(sitemaps.SitemapSource().search(JobQuery(["DE"], [], terms, 72, NOW),
                                                multilingual_site(requested)))
    # Both jobs, each from its German page: the English copies weren't opened, and the
    # languages robots.txt closes neither were opened nor used up the two pages allowed.
    assert sorted(job.title for job in jobs) == ["Elektronikentwickler",
                                                 "Hardwareentwickler Elektronik"]
    opened = [path for path in requested if "/job/" in path]
    assert sorted(opened) == ["/de/job/elektronikentwickler__m_w_d_/102",
                              "/de/job/hardwareentwickler_elektronik__m_w_d_/101"]


def test_a_new_job_whose_address_misses_the_search_words_goes_to_the_title_check(monkeypatch):
    group = Employer("Example Group", "sitemap", "https://group.test/sitemap.xml", ("DE",))
    monkeypatch.setattr(careers, "load_directory", lambda: (group,))
    terms = [SearchTerm(text="Hardwareentwickler", language="de", kind="job_title")]
    query = JobQuery(["DE"], [], terms, 24, NOW)
    source = sitemaps.SitemapSource()
    requested = []
    # The first reading records the list: its jobs' first sight proves no posting day.
    first = list(source.search(query, multilingual_site(requested)))
    assert [job.title for job in first] == ["Hardwareentwickler Elektronik"]

    newer = MULTILINGUAL.replace("</urlset>", "".join(
        f"<url><loc>https://group.test/{language}/job/elektrischer_entwickler__m_w_d_/103</loc>"
        f"<lastmod>{stamp(NOW)}</lastmod></url>" for language in ("de", "en")) + "</urlset>")
    monkeypatch.setattr(sys.modules[__name__], "MULTILINGUAL", newer)
    requested.clear()
    ctx = multilingual_site(requested)
    jobs = list(sitemaps.SitemapSource().search(query, ctx))
    new = next(job for job in jobs if job.source_job_id.endswith("/103"))
    # Named by its address, dated to its first sight, for the person's AI to look at; its
    # page wasn't opened, nor the old unmatched job's.
    assert new.title == "elektrischer entwickler" and new.title_unmatched
    assert new.date_precision == "day" and new.country == "DE" and new.company == "Example Group"
    assert not [path for path in requested if path.endswith(("/103", "/102"))]
    full = sitemaps.SitemapSource().load_details(new, ctx)
    assert full.title == "Elektronikentwickler" and full.location_text == "Kiel"
    assert full.source_job_id == new.source_job_id and full.description_is_complete
    assert requested[-1] == "/de/job/elektrischer_entwickler__m_w_d_/103"


def test_the_title_an_address_spells():
    assert sitemaps.title_of(
        "https://group.test/de/job/elektrischer_entwickler__m_w_d_/1191311") == (
        "elektrischer entwickler")
    assert sitemaps.title_of(
        "https://jobs.test/en-gb/job/Hardware%20Engineer%20(all%20genders)/9") == (
        "Hardware Engineer")
    assert sitemaps.job_key("https://group.test/de/job/x/1") == sitemaps.job_key(
        "https://group.test/en/job/x/1") == "group.test/job/x/1"


def test_one_address_per_job_keeps_the_most_wanted_language_at_its_newest_place():
    entries = [("https://a.test/fr/job/x/1", NOW), ("https://a.test/en-gb/job/x/1", NOW - DAY),
               ("https://a.test/careers/y", NOW - DAY), ("https://a.test/de/job/x/1", None),
               ("https://b.test/de/job/x/1", None)]
    assert sitemaps.one_address_per_job(entries, ["de", "en"]) == [
        ("https://a.test/de/job/x/1", NOW), ("https://a.test/careers/y", NOW - DAY),
        ("https://b.test/de/job/x/1", None)]
    assert sitemaps.one_address_per_job(entries, ["en"])[0] == ("https://a.test/en-gb/job/x/1", NOW)


def test_the_directory_check_looks_at_a_few_pages_for_the_countries():
    recruiter = Employer("Recruit Group", "sitemap", "https://recruit.test/sitemap.xml", ())
    source = sitemaps.SitemapSource()
    ctx = site([])
    survey = source.survey(recruiter, ctx)
    assert survey.counts["GB"] == 4 and survey.sample  # its towns aren't all the towns
    assert source.readable(recruiter, ctx)


def test_countries_and_address_words():
    assert sitemaps.country_code("UK") == "GB" and sitemaps.country_code("Deutschland") == "DE"
    assert sitemaps.country_code("Atlantis") is None and sitemaps.country_code(None) is None
    assert "graduate electronics engineer" in sitemaps.words_of(
        "https://recruit.test/jobs/27724/graduate-electronics-engineer")
    assert "Hardwareentwickler" in sitemaps.words_of(
        "https://jobs.test/stellen/Hardwareentwickler%20%28m-w-d%29")


def test_old_reader_cache_is_refreshed_then_complete_requirements_reach_scoring():
    address = 'https://recruit.test/jobs/99/hardware-engineer'
    company = Employer('Example Devices', 'sitemap', 'https://recruit.test/sitemap.xml', ('GB',))
    data = {'@type': 'JobPosting', 'title': 'Hardware Engineer', 'description': 'Design boards.',
            'qualifications': 'German C1 required. Certification preferred, not required.',
            'eligibilityToWorkRequirement': 'Work permission required; no sponsorship.',
            'datePosted': NOW.isoformat(),
            'jobLocation': {'address': {'addressLocality': 'London', 'addressCountry': 'GB'}}}
    body = '<script type="application/ld+json">' + json.dumps(data) + '</script>'
    legacy = sitemaps.to_found_job(address, body, company)
    jobstore.remember_ad(
        dataclasses.replace(legacy, description='Design boards.'), reader_version=1)
    requested = []

    def handler(request):
        requested.append(request.url.path)
        return httpx.Response(404) if request.url.path == '/robots.txt' \
            else httpx.Response(200, text=body)

    ctx = SourceContext(
        PoliteClient(min_intervals={}, transport=httpx.MockTransport(handler)),
        KeyStore(), SourceReport('sitemap', 'Original'), lambda: False, lambda _: None)
    try:
        source = sitemaps.SitemapSource()
        found = source._from_page(address, company, ctx)
        prompt = scoring._job_block('J0', JobGroup([found]))
        assert 'German C1 required.' in prompt and 'no sponsorship.' in prompt
        assert 'Certification preferred, not required.' in prompt
        assert 'only the start' not in prompt
        assert requested == ['/robots.txt', '/jobs/99/hardware-engineer']
        requested.clear()
        assert source._from_page(address, company, ctx) == found
        assert requested == []
    finally:
        ctx.http.close()


def test_requirements_without_an_original_body_remain_partial_for_scoring():
    body = '<script type="application/ld+json">' + json.dumps({
        '@type': 'JobPosting', 'title': 'Teacher', 'skills': 'Classroom assessment',
    }) + '</script>'
    found = sitemaps.to_found_job('https://school.example/job/1', body,
                                Employer('Example School', 'sitemap', '', ('IE',)))
    assert 'Classroom assessment' in found.description
    assert not found.description_is_complete
    assert 'only the start' in scoring._job_block('J0', JobGroup([found]))
