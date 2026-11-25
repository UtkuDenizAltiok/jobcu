"""Avature career sites: lists a few jobs a page, per country, and job pages with Avature's label
and value fields. Made-up sites, jobs and answers."""

import json
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.settings import Settings
from jobcu.sources import OPT_IN_SOURCES, TERMS_NOTES, avature, disabled_sources
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer, keep_job
from jobcu.sources.http import PoliteClient

HOST = "careers.fake.example"
LIST_DE = f"https://{HOST}/en_US/jobs/SearchJobs/?99%5B%5D=111&listFilterMode=1"
EMPLOYER = Employer("FakeCo", "avature", f"{HOST}/en_US/jobs", ("DE", "GB"), True,
                    lists={"DE": LIST_DE, "GB": f"https://{HOST}/en_US/jobs/SearchJobsUK"})


def item(job_id, title, place="Erlangen , Bavaria , Germany"):
    return (f'<article class="article article--result"><h3 class="article__header__text__title">'
            f'<a href="https://{HOST}/en_US/jobs/JobDetail/{job_id}">{title}</a></h3>'
            f'<div class="article__header__text__subtitle"><span>{place}</span> • '
            f'Job ID: {job_id} • Engineering</div></article>')


def list_page(jobs, offset, total, page_size=2):
    links = "".join(
        f'<a href="https://{HOST}/en_US/jobs/SearchJobs/?99=%5B111%5D&amp;listFilterMode=1&amp;'
        f'folderRecordsPerPage={page_size}&amp;folderOffset={n}">{n // page_size + 1}</a>'
        for n in range(0, total, page_size) if n != offset)
    return f"<div>{total} results</div>{''.join(jobs)}<nav>{links}</nav>"


def job_page(posted="23-Nov-2026", places=("Erlangen - Bavaria - Germany",),
             ad="<p>Design power converters for fictional machines.</p>"):
    def field(label, value):
        name = f'<div class="article__content__view__field__label">{label}</div>' if label else ""
        return (f'<div class="article__content__view__field ">{name}'
                f'<div class="article__content__view__field__value">{value}</div></div>')
    return ('<div class="article__content__view">' + field("Job ID", "1") +
            field("Posted since", posted) + field("Job type", "Full-time") +
            field("Work mode", "Hybrid (Remote/Office)") + field("Employment type", "Permanent") +
            field("Location(s)", "<br>".join(places)) + field("", ad) + "</div>")


class Site:
    """A fictional Avature site: a German list two jobs a page, job pages, robots.txt."""

    def __init__(self, listed, robots="User-agent: *\nAllow: /\n", pages=None):
        self.listed, self.robots, self.pages = listed, robots, pages or {}
        self.opened: list[str] = []
        self.list_reads = 0

    def __call__(self, request):
        path = request.url.path
        if path == "/robots.txt":
            return httpx.Response(200, text=self.robots)
        if "/JobDetail/" in path:
            job_id = path.rsplit("/", 1)[-1]
            self.opened.append(job_id)
            return httpx.Response(200, text=self.pages.get(job_id, job_page()))
        self.list_reads += 1
        offset = int(dict(request.url.params).get("folderOffset", 0))
        jobs = self.listed[offset:offset + 2]
        return httpx.Response(200, text=list_page(jobs, offset, len(self.listed)))


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("avature", "avature"), lambda: False,
                         lambda message: None)


TERMS = [SearchTerm(text="power electronics", language="en", kind="job_title"),
         SearchTerm(text="Leistungselektronik", language="de", kind="job_title")]


def test_a_country_list_is_read_whole_by_following_its_own_page_links():
    site = Site([item(1, "Power Electronics Engineer"), item(2, "Accountant"),
                 item(3, "Leistungselektronik Entwickler"),
                 item(4, "Sales Manager", place="Multiple Locations")])
    jobs = avature.AvatureSource()._list(EMPLOYER, "DE", context(site))
    assert [job.title for job in jobs] == ["Power Electronics Engineer", "Accountant",
                                          "Leistungselektronik Entwickler", "Sales Manager"]
    assert site.list_reads == 2
    assert jobs[0].location_text == "Erlangen, Bavaria, Germany" and jobs[0].country == "DE"
    # A job "in multiple locations" is on every country's list: its page tells its country.
    assert jobs[3].country is None and jobs[3].location_text is None


def test_matching_titles_are_read_from_their_pages_and_new_unmatched_titles_go_to_the_ai():
    now = datetime.now(UTC)
    listed = [item(1, "Power Electronics Engineer"), item(2, "Accountant")]
    source = avature.AvatureSource()
    site = Site(listed)
    first = list(source.list_jobs(EMPLOYER, context(site), countries=["DE"],
                                  start=now - timedelta(hours=24), terms=TERMS))
    # The first reading dates no listed job, so only the matching title, read from its page.
    assert [job.title for job in first] == ["Power Electronics Engineer"]
    full = first[0]
    assert full.description_is_complete and "power converters" in full.description
    assert full.posted_at.date() == date(2026, 11, 23) and full.date_precision == "day"
    assert full.location_text == "Erlangen, Bavaria, Germany" and full.country == "DE"
    assert full.work_mode == "hybrid" and full.job_types == ["full_time_permanent"]

    # A day later a new job is on the list: its title goes to the person's AI, dated by first
    # sight, and the page already read isn't opened again.
    from jobcu import listmemory
    listmemory.note(source.id, f"{EMPLOYER.board}#DE", [f"https://{HOST}/en_US/jobs/JobDetail/1",
                                                       f"https://{HOST}/en_US/jobs/JobDetail/2"],
                    now - timedelta(hours=20))
    site = Site([*listed, item(5, "Testing Lead")])
    later = list(avature.AvatureSource().list_jobs(
        EMPLOYER, context(site), countries=["DE"], start=now - timedelta(hours=24), terms=TERMS))
    assert [job.title for job in later] == ["Power Electronics Engineer", "Testing Lead"]
    assert site.opened == []
    new = keep_job(later[1], EMPLOYER, _query(now), now - timedelta(hours=24))
    assert new.title_unmatched and new.date_precision == "day"
    # The person's AI kept it: its page gives its ad and day.
    site.pages["5"] = job_page(posted="24-Nov-2026", ad="<p>Lead the fictional test bench.</p>")
    loaded = avature.AvatureSource().load_details(new, context(site))
    assert loaded.description == "Lead the fictional test bench."
    assert loaded.posted_at.date() == date(2026, 11, 24)


def _query(now):
    from jobcu.sources.base import JobQuery
    return JobQuery(countries=["DE"], places=[], terms=TERMS, posted_within_hours=24,
                    started_at=now)


def test_a_page_reads_avature_fields_and_the_standard_job_data_together():
    page = job_page(posted="05-Nov-2026", places=("Planegg - - Germany",
                                                   "Stuttgart - Baden-Wuerttemberg - Germany"))
    found = avature.read_page(page)
    assert found.places == "Planegg, Germany; Stuttgart, Baden-Wuerttemberg, Germany"
    assert found.posted.date() == date(2026, 11, 5)
    # A site whose fields have no day and whose standard job data has only a title and a day
    # (Siemens Energy's), with its place at the top of the ad.
    page = ('<script type="application/ld+json">' + json.dumps(
        {"@type": "JobPosting", "title": "Graduate Electrical Engineer",
         "datePosted": "2026-11-12"}) + "</script>" +
        '<div class="article__content__view__field "><div class="article__content__view__field__'
        'value"><p>Location</p><p>United Kingdom</p><p>West Midlands</p><p>Lincoln</p>'
        "<p>A Snapshot of Your Day</p><p>Fictional duties.</p></div></div>")
    found = avature.read_page(page)
    assert found.posted.date() == date(2026, 11, 12)
    assert found.places == "Lincoln, West Midlands, United Kingdom"
    assert "Fictional duties." in found.description


def test_an_ad_split_into_labelled_sections_is_read_whole_rather_than_the_cut_job_data():
    # A site that writes its ad under its own headings and cuts the standard job data to the
    # ad's first sentences (McLaren's, 2026-11-26).
    def field(label, value):
        return (f'<div class="article__content__view__field "><div class="article__content__'
                f'view__field__label">{label}</div><div class="article__content__view__field__'
                f'value">{value}</div></div>')
    duties = "<ul>" + "".join(f"<li>Design fictional converter stage {n}.</li>"
                              for n in range(8)) + "</ul>"
    page = ('<script type="application/ld+json">' + json.dumps(
        {"@type": "JobPosting", "title": "Power Electronics Engineer",
         "description": "Design fictional converters from concept to", "datePosted": "2026-11-20"})
        + "</script>" + field("Ref #", "1234") + field("Date posted", "Friday, November 20, 2026")
        + field("Department", "Fictional Drives") + field("Salary", ".")
        + field("What You&#039;ll Do", duties)
        + field("What You&#039;ll Bring", "<p>" + "A fictional degree in electronics. " * 6
                + "</p>"))
    found = avature.read_page(page)
    assert found.description.startswith("What You'll Do\n\n")
    assert "Design fictional converter stage 7." in found.description
    assert "What You'll Bring" in found.description
    assert "1234" not in found.description and "Fictional Drives" not in found.description
    assert found.posted.date() == date(2026, 11, 20)


@pytest.mark.parametrize("ad", ["Location\n\nYour tasks\n\nNurse the fictional patients.",
                                "About us\n\nGermany\n\nA fictional bakery."])
def test_an_ad_s_first_lines_are_a_place_only_under_a_location_heading_with_a_country(ad):
    assert avature._leading_place(ad) is None


def test_robots_txt_is_respected():
    site = Site([item(1, "Power Electronics Engineer")], robots="User-agent: *\nDisallow: /\n")
    with pytest.raises(SourceError):
        list(avature.AvatureSource().list_jobs(EMPLOYER, context(site), countries=["DE"],
                                               start=datetime.now(UTC), terms=TERMS))
    assert site.list_reads == 0


def test_the_directory_check_counts_each_country_s_list_but_not_jobs_on_every_list():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="")
        if request.url.path.endswith("SearchJobsUK"):
            return httpx.Response(200, text=list_page(
                [item(9, "Sales Lead", place="Multiple Locations")], 0, 1))
        return httpx.Response(200, text=list_page([item(1, "Engineer"), item(2, "Nurse")], 0, 37))
    survey = avature.AvatureSource().survey(EMPLOYER, context(handler))
    assert dict(survey.counts) == {"DE": 37} and survey.towns == {"DE": {"Erlangen"}}
    assert survey.sample  # the first page's towns: the directory records none of them


def test_it_is_read_only_for_a_person_who_accepts_the_site_terms():
    assert "avature" in OPT_IN_SOURCES and "terms" in TERMS_NOTES["avature"]
    assert "avature" in disabled_sources(Settings())
    assert "avature" not in disabled_sources(Settings(source_opt_ins=["avature"]))
