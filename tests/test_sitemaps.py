"""Job sitemaps with JobPosting pages (sources/sitemaps.py), with a made-up recruiter's site."""

import dataclasses
import json
import re
import sys
from datetime import UTC, datetime, timedelta

import httpx

from jobcu import jobstore, listmemory, scoring
from jobcu.dedupe import JobGroup
from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.placenames import OTHER
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


MOTORS_PATTERN = r"/[^/?#]+-\d{4,}-([0-9a-z]{6,})$"
MOTORS_INDEX = """<?xml version="1.0"?><sitemapindex>
<sitemap><loc>https://jobs.motors.test/de-sitemap.xml</loc></sitemap>
<sitemap><loc>https://jobs.motors.test/en-sitemap.xml</loc></sitemap></sitemapindex>"""


def motors_sitemap(language, written):
    # Each language's page has its own number; the vacancy's code is the same in all of them.
    jobs = [("payroll-assistant", 1002, "abc0001x2"),
            ("hardware-engineer-power-electronics", 1001, "abc0001x1")]
    return ("<?xml version='1.0'?><urlset>"
            f"<url><loc>https://jobs.motors.test/{language}</loc><lastmod>{written}</lastmod></url>"
            + "".join(f"<url><loc>https://jobs.motors.test/{language}/{slug}-"
                      f"{number + (7 if language == 'en' else 0)}-{code}</loc>"
                      f"<lastmod>{written}</lastmod></url>" for slug, number, code in jobs)
            + "</urlset>")


def motors_site(requested):
    written = NOW.isoformat()  # every page dated to the moment the sitemap was written

    def handler(request):
        path = request.url.path
        requested.append(path)
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if path == "/sitemap.xml":
            return httpx.Response(200, text=MOTORS_INDEX)
        if path.endswith("-sitemap.xml"):
            return httpx.Response(200, text=motors_sitemap(path[1:3], written))
        if path.endswith("abc0001x1"):
            return httpx.Response(200, text=page("Hardware Engineer Power Electronics",
                                                 "Stuttgart", "DE", NOW - timedelta(hours=6)))
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("sitemap", "Sitemaps"), lambda: False,
                         lambda message: None)


def test_a_site_whose_job_addresses_speak_of_no_job_is_read_by_its_pattern(monkeypatch):
    motors = Employer("Example Motors", "sitemap", "https://jobs.motors.test/sitemap.xml",
                      ("DE",), jobs=MOTORS_PATTERN)
    monkeypatch.setattr(careers, "load_directory", lambda: (motors,))
    terms = [SearchTerm(text="Hardware Engineer", language="en", kind="job_title")]
    requested = []
    jobs = list(sitemaps.SitemapSource().search(JobQuery(["DE"], [], terms, 24, NOW),
                                                motors_site(requested)))
    # Its job pages say nothing of jobs in their addresses: the pattern finds them. The
    # vacancy is opened once, in the searched country's language, and its code names it.
    assert [job.title for job in jobs] == ["Hardware Engineer Power Electronics"]
    assert jobs[0].country == "DE"
    opened = [path for path in requested if not path.endswith((".xml", ".txt"))]
    assert opened == ["/de/hardware-engineer-power-electronics-1001-abc0001x1"]
    pattern = re.compile(MOTORS_PATTERN)
    address = "https://jobs.motors.test/en/payroll-assistant-1009-abc0001x2"
    assert sitemaps.job_key(address, pattern) == "jobs.motors.test#abc0001x2"
    assert sitemaps.title_of(address, pattern) == "payroll assistant"


def test_the_directory_check_samples_the_whole_list_when_its_dates_cant_order_it(monkeypatch):
    motors = Employer("Example Motors", "sitemap", "https://jobs.motors.test/sitemap.xml", (),
                      jobs=MOTORS_PATTERN)
    monkeypatch.setattr(sitemaps, "SURVEY_PAGES", 1)
    requested = []
    survey = sitemaps.SitemapSource().survey(motors, motors_site(requested))
    # The list's first page (the payroll job's, gone) isn't the only one looked at: the page
    # from the middle of the list shows the German job.
    assert survey.counts["DE"] == 1
    assert [path for path in requested if not path.endswith((".xml", ".txt"))] == [
        "/en/hardware-engineer-power-electronics-1008-abc0001x1"]


def test_pages_new_on_the_list_are_opened_first_when_the_sitemap_dates_them_all_alike(
        monkeypatch):
    motors = Employer("Example Motors", "sitemap", "https://jobs.motors.test/sitemap.xml",
                      ("DE",), jobs=MOTORS_PATTERN)
    monkeypatch.setattr(careers, "load_directory", lambda: (motors,))
    monkeypatch.setattr(sitemaps, "MAX_PAGES", 1)
    # The list had the payroll job three days ago; the engineer's job is new on it.
    listmemory.note("sitemap", motors.board, ["jobs.motors.test#abc0001x2"],
                    now=NOW - 3 * DAY)
    terms = [SearchTerm(text="Hardware Engineer", language="en", kind="job_title"),
             SearchTerm(text="Payroll Assistant", language="en", kind="job_title")]
    requested = []
    jobs = list(sitemaps.SitemapSource().search(JobQuery(["DE"], [], terms, 24, NOW),
                                                motors_site(requested)))
    # In the sitemap's own order the old payroll job's page came first and took the one page.
    assert [job.title for job in jobs] == ["Hardware Engineer Power Electronics"]
    assert not any("payroll" in path for path in requested)


CARS_PATTERN = r"job-description-copy\.(\d+)\.html$"
CARS_AD = ("<p>You design power converters for electric drives, from the first circuit to the "
           "validated board, and test them in our laboratory with the team.</p><ul><li>A degree in "
           "electrical engineering</li><li>Experience with gate drivers and magnetics</li></ul>"
           "<p>We offer flexible hours, a modern laboratory, training and a team that enjoys its "
           "work. Apply with your CV; we answer every application within two weeks.</p>")


def cars_page(title, town):
    return (f"<html><body><nav>Jobs Benefits</nav><main><div>Drive Development</div><div>{town}"
            f"</div><div>24.11.2026</div><h1>{title}</h1>{CARS_AD}</main></body></html>")


def cars_site(requested, numbers):
    def handler(request):
        path = request.url.path
        requested.append(path)
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if path == "/sitemap.xml":
            return httpx.Response(200, text="<?xml version='1.0'?><urlset>" + "".join(
                f"<url><loc>https://cars.test/en/jobfinder/job-description-copy.{n}.html</loc>"
                "</url>" for n in numbers) + "<url><loc>https://cars.test/en/benefits.html</loc>"
                "</url></urlset>")
        if path.endswith(".103.html"):
            return httpx.Response(200, text=cars_page("Hardware Engineer Power Electronics",
                                                      "Munich"))
        if path.endswith(".105.html"):
            return httpx.Response(200, text=cars_page("Praktikum Marketing", "Munich"))
        if path.endswith(".104.html"):  # a filled job's page leads back to the job finder
            return httpx.Response(302, headers={"Location": "https://cars.test/en/jobfinder.html"})
        if path == "/en/jobfinder.html":
            return httpx.Response(200, text=cars_page("Job finder", "Munich"))
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("sitemap", "Sitemaps"), lambda: False,
                         lambda message: None)


def test_a_site_whose_addresses_name_no_title_opens_only_the_pages_new_on_its_list(monkeypatch):
    cars = Employer("Example Cars", "sitemap", "https://cars.test/sitemap.xml", ("DE",),
                    True, jobs=CARS_PATTERN, titles=False)
    monkeypatch.setattr(careers, "load_directory", lambda: (cars,))
    # The list's reading half a day ago had the first two jobs.
    listmemory.note("sitemap", cars.board, ["cars.test#101", "cars.test#102"],
                    now=NOW - timedelta(hours=12))
    terms = [SearchTerm(text="Hardware Engineer", language="en", kind="job_title")]
    requested = []
    jobs = list(sitemaps.SitemapSource().search(JobQuery(["DE"], [], terms, 24, NOW),
                                                cars_site(requested, range(101, 106))))
    # The pages without job data were read as text: title, town and ad, dated by the list's
    # first sight; the title the search words miss goes to the person's AI.
    by_title = {job.title: job for job in jobs}
    assert sorted(by_title) == ["Hardware Engineer Power Electronics", "Praktikum Marketing"]
    engineer = by_title["Hardware Engineer Power Electronics"]
    assert (engineer.location_text, engineer.country, engineer.company) == (
        "Munich", "DE", "Example Cars")
    # First seen when the reader ran: today, also after a midnight since NOW was taken.
    assert engineer.date_precision == "day"
    assert engineer.posted_at.date() in {NOW.date(), datetime.now(UTC).date()}
    assert engineer.description_is_complete and "gate drivers" in engineer.description
    assert not engineer.title_unmatched and by_title["Praktikum Marketing"].title_unmatched
    # The jobs listed before weren't opened; the page that led back to the job finder wasn't
    # taken for an ad.
    opened = [path for path in requested if "job-description" in path]
    assert sorted(opened) == [f"/en/jobfinder/job-description-copy.{n}.html"
                              for n in (103, 104, 105)]


def test_a_page_read_as_text_takes_the_one_country_of_the_employer_where_its_place_is():
    cars = Employer("Example Cars", "sitemap", "https://cars.test/sitemap.xml", ("CH", "DE"),
                    True, jobs=CARS_PATTERN, titles=False)
    # A district's name alone doesn't tell the country; among the employer's countries only
    # Germany has it.
    job = sitemaps.FoundJob(source="sitemap", source_job_id="x", url="x", title="Engineer",
                            location_text="Zuffenhausen")
    assert sitemaps._in_own_country(job, cars).country == "DE"
    assert sitemaps._in_own_country(dataclasses.replace(job, location_text="Atlanta"),
                                    cars).country is None


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


LIGHTS = f"""<?xml version="1.0"?><urlset>
<url><loc>https://jobs.lights.test/en/job/Process-Engineer-d_m_f-Shanghai/31</loc>
<lastmod>{stamp(NOW)}</lastmod></url>
<url><loc>https://jobs.lights.test/en/job/Design-Engineer-d_m_f-Regensburg/30</loc>
<lastmod>{stamp(NOW - 2 * DAY)}</lastmod></url>
<url><loc>https://jobs.lights.test/en/job/Test-Technician-Exeter/29</loc>
<lastmod>{stamp(NOW - 3 * DAY)}</lastmod></url>
<url><loc>https://jobs.lights.test/en/job/Buyer-Shanghai/28</loc>
<lastmod>{stamp(NOW - 4 * DAY)}</lastmod></url>
</urlset>"""


def test_the_directory_check_counts_countries_only_the_ends_of_job_addresses_name(monkeypatch):
    # A large site's newest pages can all be abroad; the addresses of its other job pages end
    # in their towns, so the check sees the employer hires in Germany and the UK too without
    # opening those pages.
    monkeypatch.setattr(sitemaps, "SURVEY_PAGES", 1)
    requested = []

    def handler(request):
        requested.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=LIGHTS)
        if request.url.path.endswith("/31"):
            return httpx.Response(200, text=page("Process Engineer", "Shanghai", "CN", NOW))
        return httpx.Response(404)

    ctx = SourceContext(PoliteClient(min_intervals={}, sleep=lambda s: None,
                                     transport=httpx.MockTransport(handler)),
                        KeyStore(), SourceReport("sitemap", "Sitemaps"), lambda: False,
                        lambda message: None)
    lights = Employer("Example Lights", "sitemap", "https://jobs.lights.test/sitemap.xml", ())
    survey = sitemaps.SitemapSource().survey(lights, ctx)
    assert survey.counts["DE"] == 1 and survey.counts["GB"] == 1
    assert survey.counts[OTHER] == 1  # the page abroad; the addresses abroad add nothing more
    assert survey.sample and not survey.towns
    assert requested.count("/sitemap.xml") == 1  # read once
    assert [path for path in requested if "/job/" in path] == [
        "/en/job/Process-Engineer-d_m_f-Shanghai/31"]


def test_the_country_the_end_of_a_job_address_names():
    assert sitemaps.address_countries(
        "https://jobs.test/en/job/Design-Engineer-d_m_f-Regensburg/24800") == {"DE"}
    assert sitemaps.address_countries(
        "https://recruit.test/job-details/power-electronics-engineer-london") == {"GB"}
    assert sitemaps.address_countries(
        "https://jobs.test/en/job/Senior-Engineer-Frankfurt-am-Main/1") == {"DE"}
    assert sitemaps.address_countries(
        "https://jobs.test/en/job/Sales-Engineer-Mexico-City/2") == {OTHER}
    # No town at its end, or nothing but a town: no country.
    assert not sitemaps.address_countries(
        "https://recruit.test/jobs/27724/graduate-electronics-engineer")
    assert not sitemaps.address_countries("https://jobs.test/en/job/Regensburg/5")


FRAMED = f"""<?xml version="1.0"?><urlset>
<url><loc>https://portal.frames.test/jobs/search</loc></url>
<url><loc>https://portal.frames.test/jobs/12/power-electronics-engineer/job</loc>
<lastmod>{stamp(NOW)}</lastmod></url></urlset>"""


def test_a_job_page_showing_its_ad_in_a_frame_of_its_own_site_is_read_through_the_frame(
        monkeypatch):
    # An iCIMS-like career site: the job page has no job data and embeds a video and, from its
    # own site, the frame that shows the ad with its JobPosting data.
    requested = []

    def handler(request):
        requested.append(str(request.url))
        path = request.url.path
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /jobs/*login\n")
        if path == "/sitemap.xml":
            return httpx.Response(200, text=FRAMED)
        if path == "/jobs/12/power-electronics-engineer/job":
            if request.url.params.get("in_iframe") == "1":
                return httpx.Response(200, text=page("Power Electronics Engineer", "Bedlington",
                                                     "UK", NOW - timedelta(hours=2)))
            return httpx.Response(200, text=(
                '<html><iframe src="//video.example/embed/1"></iframe><iframe src="https://'
                'portal.frames.test/jobs/12/power-electronics-engineer/job?in_iframe=1&amp;x=1">'
                "</iframe></html>"))
        return httpx.Response(404)

    framed = Employer("Example Frames", "sitemap", "https://portal.frames.test/sitemap.xml",
                      ("GB",), jobs=r"/jobs/(\d+)/[^/]+/job$")
    monkeypatch.setattr(careers, "load_directory", lambda: (framed,))
    terms = [SearchTerm(text="Power Electronics Engineer", language="en", kind="job_title")]
    ctx = SourceContext(PoliteClient(min_intervals={}, sleep=lambda s: None,
                                     transport=httpx.MockTransport(handler)),
                        KeyStore(), SourceReport("sitemap", "Sitemaps"), lambda: False,
                        lambda message: None)
    jobs = list(sitemaps.SitemapSource().search(JobQuery(["GB"], [], terms, 24, NOW), ctx))
    assert [(job.title, job.country) for job in jobs] == [("Power Electronics Engineer", "GB")]
    # The person's link is the job's page, not the frame.
    assert jobs[0].url == "https://portal.frames.test/jobs/12/power-electronics-engineer/job"
    assert "Design SMPS." in jobs[0].description
    assert not any("video.example" in address for address in requested)
    assert ("https://portal.frames.test/jobs/12/power-electronics-engineer/job?in_iframe=1&x=1"
            in requested)


def test_the_frame_a_page_embeds_from_its_own_site():
    page_text = ('<iframe src="https://www.googletagmanager.com/ns.html"></iframe>'
                 "<iframe class='x' src='/jobs/5/x/job?in_iframe=1'></iframe>")
    assert sitemaps.own_frame(page_text, "https://a.test/jobs/5/x/job") == (
        "https://a.test/jobs/5/x/job?in_iframe=1")
    assert sitemaps.own_frame('<iframe src="https://a.test/p"></iframe>',
                              "https://a.test/p") is None
    assert sitemaps.own_frame("<p>No frames.</p>", "https://a.test/p") is None


def posting_page(*countries, town="Olathe"):
    places = [{"address": {"addressLocality": town, "addressCountry": country}}
              for country in countries]
    return ('<script type="application/ld+json">' + json.dumps(
        {"@type": "JobPosting", "title": "Power Electronics Engineer", "datePosted":
         NOW.date().isoformat(), "description": "Design fictional converters.",
         "jobLocation": places}) + "</script>")


def test_a_job_whose_page_names_a_country_outside_the_supported_ones_is_abroad():
    # A UK employer's site also lists its American jobs: one in Olathe ("US") isn't placed in
    # the UK because the employer's directory entry names only the UK.
    uk_only = Employer("Example Modules", "sitemap", "https://modules.test/sitemap.xml",
                       ("GB",), jobs=r"/jobs/(\d+)/[^/]+/job$")
    address = "https://modules.test/jobs/6294/power-electronics-engineer/job"
    for written in ("US", "USA", "United States", "MX"):
        job = sitemaps.to_found_job(address, posting_page(written), uk_only)
        assert job.country == OTHER
        query = JobQuery(["GB"], [], [SearchTerm(text="Power Electronics Engineer",
                                                 language="en", kind="job_title")], 24, NOW)
        assert careers.keep_job(job, uk_only, query, NOW - DAY) is None
    # A job offered in several places is in the first supported one they name; three-letter
    # codes name supported countries too; no country, or none as a country, decides nothing.
    assert sitemaps.to_found_job(address, posting_page("US", "GB", town="Bedlington"),
                                 uk_only).country == "GB"
    assert sitemaps.to_found_job(address, posting_page("DEU"), uk_only).country == "DE"
    assert sitemaps.to_found_job(address, posting_page("EMEA"), uk_only).country is None
    assert sitemaps.to_found_job(address, posting_page(), uk_only).country is None


def test_countries_and_address_words():
    assert sitemaps.country_code("UK") == "GB" and sitemaps.country_code("Deutschland") == "DE"
    assert sitemaps.country_code("GBR") == "GB" and sitemaps.country_code("IRL") == "IE"
    assert sitemaps.country_code("Atlantis") is None and sitemaps.country_code(None) is None
    assert sitemaps.abroad("US") and sitemaps.abroad("Mexico") and not sitemaps.abroad("Remote")
    assert not sitemaps.abroad("NA")  # written for "not available" more often than for Namibia
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
