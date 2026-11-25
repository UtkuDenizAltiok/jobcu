"""Employers' own job list pages (sources/listpages.py), with made-up employers' sites."""

import dataclasses
import json
import re
from datetime import UTC, datetime, timedelta

import httpx

from jobcu import db, listmemory
from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.sources import careers, listpages
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

NOW = datetime.now(UTC)
DAY = timedelta(days=1)


def posting(title, town, country="DE", posted=NOW - timedelta(hours=5)):
    data = {"@type": "JobPosting", "title": title, "datePosted": posted.isoformat(),
            "description": f"<p>{title}: design power converters.</p>",
            "hiringOrganization": {"name": "Example Elektronik GmbH"},
            "jobLocation": {"address": {"addressLocality": town, "addressCountry": country}}}
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def card(number, title, towns):
    # A rexx-like list: the link carries the title, the towns follow it; every link has the
    # visitor's session number.
    return (f'<div class="joboffer"><a href="/{title.replace(" ", "-")}-de-j{number}.html'
            f'?sid=abc{number}">{title} (m/w/d)</a><div class="place">{towns}</div></div>')


FIRST = ("<html><body>" + card(11, "Hardwareentwickler Leistungselektronik", "Musterstadt")
         + card(12, "Buchhalter", "Beispielhausen")
         + '<a href="/stellenangebote.html?start=0&sid=abc">1</a>'
         + '<a href="/stellenangebote.html?start=2&sid=abc">2</a>'
         + '<a href="/stellenangebote.html?filter=7&sid=abc">Vertrieb</a></body></html>')
SECOND = ("<html><body>" + card(13, "Elektronikentwickler", "Musterstadt")
          + '<a href="/stellenangebote.html?start=0&sid=abc">1</a></body></html>')
PAGES = {
    "/Hardwareentwickler-Leistungselektronik-de-j11.html":
        posting("Hardwareentwickler Leistungselektronik (m/w/d)", "Musterstadt"),
    "/Buchhalter-de-j12.html": posting("Buchhalter (m/w/d)", "Beispielhausen"),
    "/Elektronikentwickler-de-j13.html": posting("Elektronikentwickler (m/w/d)", "Musterstadt"),
    "/Systemingenieur-Elektrotechnik-de-j14.html":
        posting("Systemingenieur Elektrotechnik (m/w/d)", "Musterstadt"),
}


def site(requested, pages=None):
    pages = pages or {"": FIRST, "start=2": SECOND}

    def handler(request):
        path, query = request.url.path, request.url.query.decode()
        requested.append(f"{path}?{query}" if query else path)
        if path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /bewerbung/\n")
        if path == "/stellenangebote.html":
            page = "start=2" if "start=2" in query else "" if "filter" not in query else None
            if page is None:
                return httpx.Response(200, text="<html>filtered</html>")
            return httpx.Response(200, text=pages.get(page, FIRST))
        if path in PAGES:
            return httpx.Response(200, text=PAGES[path])
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("listpage", "Lists"), lambda: False,
                         lambda message: None)


EMPLOYER = Employer("Example Elektronik", "listpage", "https://jobs.example.test/stellenangebote.html",
                    ("DE",), jobs=r"-j(\d+)\.html")
TERMS = [SearchTerm(text="Hardwareentwickler", language="de", kind="job_title"),
         SearchTerm(text="Elektronikentwickler", language="de", kind="job_title")]


def test_matching_jobs_are_read_from_every_list_page_without_session_numbers(monkeypatch):
    monkeypatch.setattr(careers, "load_directory", lambda: (EMPLOYER,))
    requested = []
    jobs = list(listpages.ListPageSource().search(JobQuery(["DE"], [], TERMS, 24, NOW),
                                                  site(requested)))
    assert sorted(job.title for job in jobs) == ["Elektronikentwickler (m/w/d)",
                                                 "Hardwareentwickler Leistungselektronik (m/w/d)"]
    first = next(job for job in jobs if "j11" in job.url)
    assert first.url == ("https://jobs.example.test/"
                         "Hardwareentwickler-Leistungselektronik-de-j11.html")
    assert first.source == "listpage" and first.country == "DE" and first.description_is_complete
    assert first.company == "Example Elektronik GmbH" and first.location_text == "Musterstadt"
    # The second list page was read once; the first page's repeat and the filter weren't
    # followed, and the unrelated job's page wasn't opened.
    assert requested.count("/stellenangebote.html?start=2") == 1
    assert not any("filter" in path for path in requested)
    assert "/Buchhalter-de-j12.html" not in requested


def test_a_new_title_the_search_words_miss_goes_to_the_title_check_with_its_town(monkeypatch):
    monkeypatch.setattr(careers, "load_directory", lambda: (EMPLOYER,))
    query = JobQuery(["DE"], [], TERMS, 24, NOW)
    list(listpages.ListPageSource().search(query, site([])))  # the list's first reading
    with db.connect() as conn:  # that reading was yesterday
        conn.execute("UPDATE list_readings SET read_at = ?",
                     ((NOW - timedelta(hours=20)).isoformat(timespec="seconds"),))
    newer = SECOND.replace("</body>", card(14, "Systemingenieur Elektrotechnik", "Musterstadt")
                           + "</body>")
    requested = []
    ctx = site(requested, {"": FIRST, "start=2": newer})
    jobs = list(listpages.ListPageSource().search(query, ctx))
    new = next(job for job in jobs if "j14" in job.url)
    assert new.title == "Systemingenieur Elektrotechnik (m/w/d)" and new.title_unmatched
    assert new.location_text == "Musterstadt" and new.date_precision == "day"
    assert "/Systemingenieur-Elektrotechnik-de-j14.html" not in requested
    full = listpages.ListPageSource().load_details(new, ctx)
    assert full.description_is_complete and full.source_job_id == new.source_job_id
    # The old unrelated job isn't new: it doesn't go to the title check again.
    assert not any("j12" in job.url for job in jobs)


DATA_PAGE = ("<html><div :results-data='" + json.dumps([
    {"filterterms": ["term-land-3"], "href": "/de/career/stellen.cfm?fuseaction=einzel&jid=501"
     "&t=Ingenieur%20Hardware", "location": "Paderborn", "title": "Ingenieur (m/w/d) Hardware"},
    {"href": "/de/career/stellen.cfm?fuseaction=einzel&jid=502", "location": "Zagreb, Croatia",
     "title": "Technical Writer (m/f)"}]).replace('"', "&quot;") + "'></div>"
    '<a href="/de/career/stellen.cfm?fuseaction=liste">Alle</a></html>')

ICON_PAGE = """<html>
<div class="job-name">Data Strategist (w/m/d)</div>
<div class="job-location">Example GmbH, Winterbach</div>
<a href="https://example.mhm.test/1786-data-strategist-w-m-d/job.html" class="job-link"
   aria-label="Data Strategist (w/m/d) (opens in a new tab)"><img src="arrow.svg"></a>
<div class="job-name">Versuchsingenieur (w/m/d)</div>
<div class="job-location">Example GmbH, Musterstadt</div>
<a href="https://example.mhm.test/1540-versuchsingenieur-w-m-d/job.html" class="job-link"
   aria-label="Versuchsingenieur (w/m/d) (opens in a new tab)"><img src="arrow.svg"></a>
</html>"""


def test_job_addresses_are_found_in_the_pages_own_data_and_behind_icon_links():
    jobs, more = listpages.listed_jobs(DATA_PAGE, "https://www.example.test/de/career/stellen.cfm",
                                       re.compile(r"fuseaction=einzel&jid=(\d+)"))
    assert [(job.key, job.title, job.around) for job in jobs] == [
        ("www.example.test#501", "Ingenieur (m/w/d) Hardware", "Paderborn"),
        ("www.example.test#502", "Technical Writer (m/f)", "Zagreb, Croatia")]
    assert more == []
    jobs, _ = listpages.listed_jobs(ICON_PAGE, "https://www.example.test/de/stellenangebote",
                                    re.compile(r"mhm\.test/(\d+)-"))
    assert [job.title for job in jobs] == ["Data Strategist (w/m/d)", "Versuchsingenieur (w/m/d)"]
    assert jobs[1].around.endswith("Example GmbH, Musterstadt")
    assert "Winterbach" in jobs[0].around and "Winterbach" not in jobs[1].around


def test_session_numbers_are_left_out_of_addresses():
    assert listpages.without_session("https://a.test/j1.html?sid=9b5d&lang=de") == (
        "https://a.test/j1.html?lang=de")
    assert listpages.without_session("https://a.test/x.cfm?CFID=1&CFTOKEN=2&jid=5") == (
        "https://a.test/x.cfm?jid=5")
    assert listpages.without_session("https://a.test/j1.html") == "https://a.test/j1.html"


def test_the_directory_carries_the_job_page_pattern_of_list_page_employers():
    for entry in careers.load_directory():
        if entry.system == "listpage":
            assert entry.jobs and re.compile(entry.jobs).groups == 1, entry.name


def test_the_lists_own_place_wins_over_a_page_that_gives_the_head_office():
    from jobcu.placenames import OTHER
    from jobcu.sources.base import FoundJob

    page = FoundJob(source="listpage", source_job_id="1", url="https://a.test/1",
                    title="Technical Writer", location_text="Paderborn", country="DE")
    placed = listpages.ListPageSource()._placed
    assert placed(page, "Paderborn").country == "DE"
    abroad = placed(page, "Zagreb, Croatia - Remote")
    assert abroad.location_text == "Zagreb, Croatia - Remote" and abroad.country != "DE"
    # A place the town list doesn't know, which isn't the page's town either: abroad.
    assert placed(page, "Atlantis City").country == OTHER
    small = dataclasses.replace(page, location_text="Kleindorf")
    assert placed(small, "Kleindorf").country == "DE"  # the page's own small town
    assert placed(page, None) is page


SCRIPTED = """<html><style>.card{display:flex}</style>
<a href="/acme/jobs/11111111-2222-3333-4444-555555555555"><style>.t{color:red}</style>
Senior Electronics Engineer</a><span>Electronics</span><span>Galway, Ireland</span>
<a href="/acme/jobs/66666666-7777-8888-9999-000000000000">Office Manager</a>
<span>Operations</span><span>Galway, Ireland</span></html>"""


def scripted_site(requested):
    def handler(request):
        requested.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /internal/\n")
        if request.url.path == "/acme/jobs":
            return httpx.Response(200, text=SCRIPTED)
        return httpx.Response(200, text="<html><div id='app'></div></html>")  # built by scripts

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("listpage", "Lists"), lambda: False,
                         lambda message: None)


def test_a_listed_job_whose_page_carries_no_job_data_comes_with_the_lists_title_and_place(
        monkeypatch):
    acme = Employer("Acme Photonics", "listpage", "https://ats.example.test/acme/jobs", ("IE",),
                    jobs=r"/acme/jobs/([0-9a-f-]{36})")
    monkeypatch.setattr(careers, "load_directory", lambda: (acme,))
    terms = [SearchTerm(text="Electronics Engineer", language="en", kind="job_title")]
    jobs = list(listpages.ListPageSource().search(JobQuery(["IE"], [], terms, 24, NOW),
                                                  scripted_site([])))
    assert [(job.title, job.country) for job in jobs] == [("Senior Electronics Engineer", "IE")]
    assert jobs[0].location_text == "Electronics Galway, Ireland" and not jobs[0].description
    assert jobs[0].date_precision == "unknown"  # the list's first reading proves no day
    # The directory check counts such jobs by the list's places too.
    survey = listpages.ListPageSource().survey(acme, scripted_site([]))
    assert survey.counts["IE"] == 2 and survey.sample


FUSION_LIST = """<html><div class="job"><h3><a href="/job/electrical-engineer-power-supplies/">
Electrical Engineer, Power Supplies</a></h3><div>Example Fusion Culham, Oxfordshire</div></div>
<div class="job"><h3><a href="/job/graduate-electronics-engineer/">Graduate Electronics Engineer
</a></h3><div>Example Fusion Culham, Oxfordshire</div></div></html>"""
FUSION_AD = ("<p>You design the power supplies of our experiments, from the circuit to the "
             "tested converter, with a team of engineers and physicists. You take part in "
             "commissioning on site and write the test reports.</p><ul><li>A degree in "
             "electrical engineering</li><li>Power electronics experience</li></ul><p>Site "
             "Location:</p><p>Benefits</p><p>We offer a pension, flexible hours, training and a "
             "modern laboratory. Apply with your CV; we answer every application within two "
             "weeks.</p>")


def fusion_site(requested):
    def handler(request):
        requested.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /wp-admin/\n")
        if request.url.path == "/current-vacancies/":
            return httpx.Response(200, text=FUSION_LIST)
        if request.url.path.startswith("/job/"):
            title = request.url.path.split("/")[2].replace("-", " ").title()
            return httpx.Response(200, text=f"<html><main><h1>{title}</h1>{FUSION_AD}</main>"
                                            "</html>")
        return httpx.Response(404)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("listpage", "Lists"), lambda: False,
                         lambda message: None)


def test_a_job_page_without_job_data_takes_the_lists_place_and_its_first_sight(monkeypatch):
    fusion = Employer("Example Fusion", "listpage", "https://careers.fusion.test/current-vacancies/",
                      ("GB",), jobs=r"careers\.fusion\.test/job/([^/?#]+)/?$")
    monkeypatch.setattr(careers, "load_directory", lambda: (fusion,))
    # The list had the first job three days ago and still half a day ago.
    for hours in (72, 12):
        listmemory.note("listpage", fusion.board,
                        ["careers.fusion.test#electrical-engineer-power-supplies"],
                        now=NOW - timedelta(hours=hours))
    terms = [SearchTerm(text="Electronics Engineer", language="en", kind="job_title"),
             SearchTerm(text="Electrical Engineer", language="en", kind="job_title")]
    jobs = list(listpages.ListPageSource().search(JobQuery(["GB"], [], terms, 24, NOW),
                                                  fusion_site([])))
    by_title = {job.title: job for job in jobs}
    graduate = by_title["Graduate Electronics Engineer"]
    # Its page names no place (an empty label isn't followed into the next line) and no day:
    # the list's text places it, its first sight dates it.
    assert (graduate.location_text, graduate.country) == (
        "Example Fusion Culham, Oxfordshire", "GB")
    assert graduate.date_precision == "day" and graduate.posted_at.date() == NOW.date()
    assert graduate.description_is_complete and "power supplies" in graduate.description
    # The job the list had before the window began is an older copy, not a new job.
    assert by_title["Electrical Engineer Power Supplies"].older_copy


def test_a_next_page_named_only_in_a_data_attribute_is_followed():
    page = ('<table><tr><td><a href="/Vacancies/18826/Description/31">Systemingenieur (m/w/d)</a>'
            '</td></tr></table><span data-pagination-next-href="?tc1152481=p2&amp;_search_token'
            '1152481=99#connectortable_1152481" data-pagination-to="10"></span>')
    jobs, more = listpages.listed_jobs(page, "https://career.example.test/Jobs/All",
                                       re.compile(r"/Vacancies/(\d+)/Description"))
    assert [job.key for job in jobs] == ["career.example.test#18826"]
    assert more == ["https://career.example.test/Jobs/All?tc1152481=p2&_search_token1152481=99"]


ROWS = """<table>
<tr><td><p>D: Example Defence GmbH | Online seit: 25.11.2026</p>
<p><a href="/Vacancies/501/Description/31">Entwicklungsingenieur (m/w/d) Hardware</a></p>
<p>| Stellennummer: 501 | Art: Vollzeit | Erlangen (DE) | Example Defence GmbH</p></td></tr>
<tr><td><p>A: Example Aviation Gilching | Online seit: 24.11.2026</p>
<p><a href="/Vacancies/502/Description/31">Systemingenieur (m/w/d)</a></p>
<p>| Stellennummer: 502 | Dresden (DE), Gilching (DE) | Example Aviation GmbH</p></td></tr>
</table>"""


def test_a_jobs_place_comes_from_its_own_row_not_the_next_ones():
    jobs, _ = listpages.listed_jobs(ROWS, "https://career.example.test/Jobs/All",
                                    re.compile(r"/Vacancies/(\d+)/Description"))
    assert [(job.title, job.around) for job in jobs] == [
        ("Entwicklungsingenieur (m/w/d) Hardware", "Erlangen, Germany"),
        ("Systemingenieur (m/w/d)", "Dresden, Germany")]


def test_the_day_a_list_states_for_a_job_dates_it():
    jobs, _ = listpages.listed_jobs(ROWS, "https://career.example.test/Jobs/All",
                                    re.compile(r"/Vacancies/(\d+)/Description"))
    assert [job.posted.date().isoformat() for job in jobs] == ["2026-11-25", "2026-11-24"]
    bare = listpages.ListPageSource()._title_only(jobs[0], {}, None)
    assert bare.date_precision == "day" and bare.posted_at == jobs[0].posted
    assert listpages._listed_day("Eintritt ab 01.01.2027") is None  # a start date isn't one


ACTION_LIST = """<html><div class="intro"><p>Email your CV to our HR team, Exampleton.</p></div>
<div id="jobslist">
<h4>Power Electronics Design Engineer</h4><p class="posted">Location : Exampleton</p>
<a class="btn" href="/uk/about/example-job/2291">View job details</a>
<h4>Test Engineering Team Leader</h4><p class="posted">Location : Otherford</p>
<a class="btn" href="/uk/about/example-job/2289">View job details</a>
</div></html>"""


def test_a_link_that_only_says_view_job_details_takes_the_title_of_the_heading_before_it():
    jobs, _ = listpages.listed_jobs(ACTION_LIST, "https://www.example.test/uk/about/recruitment",
                                    re.compile(r"/uk/about/example-job/(\d+)$"))
    assert [(job.title, job.around) for job in jobs] == [
        ("Power Electronics Design Engineer", "Location : Exampleton"),
        ("Test Engineering Team Leader", "Location : Otherford")]
    for words in ("View job details", "Read more", "Mehr erfahren", "Zur Stelle", "Details",
                  "Apply now", "Voir l'offre"):
        assert listpages._ACTION.fullmatch(words), words
    for title in ("Hardware Engineer", "Details Engineer", "Applications Engineer"):
        assert not listpages._ACTION.fullmatch(title), title
