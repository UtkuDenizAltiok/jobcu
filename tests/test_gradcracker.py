"""Gradcracker, with made-up pages shaped like the real ones (2026-11-25)."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.settings import Settings
from jobcu.sources import OPT_IN_SOURCES, TERMS_NOTES, disabled_sources, gradcracker
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.http import PoliteClient

START = datetime(2026, 11, 25, 8, 0, tzinfo=UTC)
SITE = gradcracker.SITE
EE = f"{SITE}/search/electronic-electrical/electronic-electrical-graduate-jobs"
SITEMAP = f"""<?xml version="1.0"?><urlset>
<url><loc>{SITE}/about-us</loc></url>
<url><loc>{EE}</loc></url>
<url><loc>{EE.replace("graduate-jobs", "graduate-jobs-in-bristol")}</loc></url>
<url><loc>{SITE}/search/electronic-electrical/electronic-electrical-work-placements-internships</loc></url>
<url><loc>{SITE}/search/civil-building/civil-infrastructure-graduate-jobs</loc></url>
</urlset>"""


def card(number, title, employer="Fake Systems", location="Bristol", deadline="Ongoing"):
    slug = title.lower().replace(" ", "-")
    return f"""
    <article wire:key="{number}" data-search-result="{number}" data-search-position="1">
      <figure><a href="{SITE}/hub/1/fake"><img src="x.jpg" alt="{employer}"></a></figure>
      <header><h2><a href="{SITE}/hub/1/fake/graduate-job/{number}/{slug}">{title}</a></h2>
        <h3>Electronics, Electrical.</h3></header>
      <dl><div><dt>Deadline</dt><dd>{deadline}</dd></div>
          <div><dt>Salary</dt><dd>£32,000</dd></div>
          <div><dt>Location</dt><dd>{location}</dd></div></dl>
    </article>"""


def list_page(*cards):
    return f"<html><body><main>{''.join(cards)}</main></body></html>"


JOB_PAGE = """<html><body><h1>Graduate Power Electronics Engineer</h1>
<div data-type="overview"><ul>
  <li><div>Deadline</div> December 12th, 2026</li>
  <li><div>Salary</div> £34,000</li>
  <li><div>Location</div> Bristol</li></ul></div>
<div class="body-content"><h2>Overview</h2><p>Design inverters and DC-DC converters.</p>
  <ul><li>Degree in electrical engineering</li></ul></div></body></html>"""


def query(*titles, started=START):
    return JobQuery(countries=["GB"], places=[], posted_within_hours=24, started_at=started,
                    terms=[SearchTerm(text=t, language="en", kind="job_title") for t in titles])


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("gradcracker", "Gradcracker"),
                         lambda: False, lambda message: None)


def site(lists, asked, robots="User-agent: *\nAllow: /\nDisallow: /keyword-search\n"):
    def handler(request):
        url = str(request.url)
        asked.append(url)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots)
        if request.url.path == "/sitemap.xml":
            return httpx.Response(200, text=SITEMAP)
        if url in lists:
            return httpx.Response(200, text=lists[url])
        return httpx.Response(404)
    return handler


def test_the_named_area_is_read_whole_and_only_jobs_new_on_it_are_passed_on(monkeypatch):
    monkeypatch.setattr(gradcracker, "PAGE_SIZE", 2)
    first = {EE: list_page(card(1, "Graduate Electrical Engineer"),
                           card(2, "Graduate Electronics Engineer")),
             f"{EE}?page=2": list_page(card(3, "Graduate Civil Engineer"))}
    asked = []
    source = gradcracker.GradcrackerSource()
    # The list's first reading proves no job's date: nothing is passed on.
    assert list(source.search(query("Power Electronics Engineer"),
                              context(site(first, asked)))) == []
    assert f"{EE}?page=2" in asked
    assert not any("civil-building" in url or "placements" in url for url in asked)

    # A day later two jobs are new on the list: they come, dated that day.
    later = START + timedelta(days=1)
    second = {EE: list_page(card(4, "Graduate Power Electronics Engineer", deadline="December "
                                 "12th, 2026"), card(5, "Graduate Test Technician")),
              f"{EE}?page=2": list_page(card(1, "Graduate Electrical Engineer"),
                                        card(2, "Graduate Electronics Engineer")),
              f"{EE}?page=3": list_page(card(3, "Graduate Civil Engineer"))}
    jobs = list(gradcracker.GradcrackerSource().search(
        query("Power Electronics Engineer", started=later), context(site(second, []))))
    assert [job.title for job in jobs] == ["Graduate Power Electronics Engineer",
                                           "Graduate Test Technician"]
    power, other = jobs
    assert (power.country, power.date_precision, power.posted_at.date()) == (
        "GB", "day", later.date())
    assert power.company == "Fake Systems" and power.location_text == "Bristol"
    assert power.closes_at == datetime(2026, 12, 12, 23, 59, tzinfo=UTC)
    assert power.url.endswith("/graduate-job/4/graduate-power-electronics-engineer")
    # A title the search words miss goes to the person's AI for a look, like a career site's.
    assert not power.title_unmatched and other.title_unmatched


def test_words_that_name_no_area_read_no_list():
    asked = []
    jobs = list(gradcracker.GradcrackerSource().search(
        query("ICU Staff Nurse", "Sous-chef"), context(site({}, asked))))
    assert jobs == [] and not any("/search/" in url for url in asked)


def test_a_list_the_site_s_robots_txt_closes_is_not_read():
    asked = []
    list(gradcracker.GradcrackerSource().search(
        query("Electronics Engineer"),
        context(site({EE: list_page(card(1, "Graduate Electronics Engineer"))}, asked,
                     robots="User-agent: *\nDisallow: /search/\n"))))
    assert EE not in asked


def test_a_job_page_gives_the_full_ad_and_its_facts():
    def handler(request):
        return httpx.Response(200, text=JOB_PAGE)

    [job] = gradcracker.parse_cards(list_page(card(4, "Graduate Power Electronics Engineer")))
    full = gradcracker.GradcrackerSource().load_details(job, context(handler))
    assert "Design inverters and DC-DC converters." in full.description
    assert "Degree in electrical engineering" in full.description
    assert full.description_is_complete and full.salary_text == "£34,000"
    assert full.closes_at == datetime(2026, 12, 12, 23, 59, tzinfo=UTC)


@pytest.mark.parametrize(("location", "country"), [
    ("Bristol", "GB"), ("Various locations", "GB"), ("Remote (UK)", "GB"),
    ("Geneva (Switzerland)", "CH"), ("Dublin, Cork and Galway (Hybrid)", "IE"),
])
def test_a_job_of_a_uk_list_is_in_the_uk_unless_its_place_names_another_country(location,
                                                                                 country):
    assert gradcracker.country_of(location) == country


def test_the_areas_follow_the_search_words_for_any_kind_of_work():
    lists = [EE, f"{SITE}/search/technology-it/hardware-graduate-jobs",
             f"{SITE}/search/technology-it/software-systems-graduate-jobs",
             f"{SITE}/search/mechanical-manufacturing/mechanical-engineering-graduate-jobs"]
    pick = gradcracker.chosen_lists
    assert pick(lists, query("Power Electronics Engineer", "Hardware Design Engineer")) == [
        lists[0], lists[1]]
    assert pick(lists, query("Software Engineer")) == [lists[2]]
    assert pick(lists, query("Graduate Engineer")) == []  # no field named
    assert pick(lists, query("ICU Staff Nurse")) == []


def test_it_is_read_only_for_a_person_who_accepts_the_site_terms():
    assert "gradcracker" in OPT_IN_SOURCES and "scraping" in TERMS_NOTES["gradcracker"]
    assert "gradcracker" in disabled_sources(Settings())
    assert "gradcracker" not in disabled_sources(Settings(source_opt_ins=["gradcracker"]))
