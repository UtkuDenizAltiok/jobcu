"""Employers the person's AI finds, and the career systems Jobcu recognises (employers.py,
sources/careerlinks.py), with a made-up AI, made-up sites and made-up people."""

from collections import Counter
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from test_search import PROFILE

from jobcu import employers
from jobcu.ai.base import ResearchReply, Source, Usage
from jobcu.ai.client import AIClient
from jobcu.placenames import OTHER
from jobcu.profile import Profile
from jobcu.settings import Settings
from jobcu.sources.careerlinks import board_in, own_address_board, system_not_read
from jobcu.sources.careers import (
    CareerSystemSource,
    Employer,
    EmployerNotFound,
    Survey,
    found_employers,
)
from jobcu.sources.http import PoliteClient

NOW = datetime(2026, 9, 30, 18, 0, tzinfo=UTC)
NURSE = Profile.model_validate({
    **PROFILE, "summary": "Registered nurse, six years in intensive care",
    "field": "Critical care nursing", "skills": ["Ventilation"], "technical_areas": [],
    "target_roles": ["ICU Staff Nurse"], "target_fields": ["Intensive care"]})


@pytest.mark.parametrize(("text", "expected"), [
    ("https://moog.wd5.myworkdayjobs.com/en-US/MOOG_External_Career_Site/job/x",
     ("workday", "https://moog.wd5.myworkdayjobs.com/MOOG_External_Career_Site")),
    ("https://acme.wd3.myworkdayjobs.com/wday/cxs/acme/Careers/jobs", None),
    # Workday's newer address names no server.
    ("https://acme.myworkdayjobs.com/en-US/careers/job/Hamburg/x_R1",
     ("workday", "https://acme.myworkdayjobs.com/careers")),
    ("https://acme.myworkdayjobs.com/wday/cxs/acme/careers/jobs", None),
    ("https://edbz.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/jobs",
     ("oracle", "edbz.fa.us2.oraclecloud.com/CX")),
    ("https://job-boards.eu.greenhouse.io/acme/jobs/1", ("greenhouse", "acme")),
    ('<script src="https://boards.greenhouse.io/embed/job_board/js?for=acme">',
     ("greenhouse", "acme")),
    ("https://jobs.eu.lever.co/cirrus", ("lever", "eu/cirrus")),
    ("https://jobs.lever.co/acme/123", ("lever", "acme")),
    ("https://apply.workable.com/smart-wires/", ("workable", "smart-wires")),
    ("https://apply.workable.com/j/ABC123", None),
    ("https://klinik.dvinci-hr.com/de/jobs", ("dvinci", "klinik")),
    ("https://mtuaero.dvinci-easy.com/de/jobs/61631/x", ("dvinci", "mtuaero.dvinci-easy.com")),
    ("https://acme.teamtailor.com/jobs", ("teamtailor", "acme")),
    ("https://jobs.smartrecruiters.com/AcmeGroup1/744000161874185-hardware-engineer",
     ("smartrecruiters", "AcmeGroup1")),
    ("https://careers.smartrecruiters.com/AcmeGroup1", ("smartrecruiters", "AcmeGroup1")),
    ("https://jobs.smartrecruiters.com/api/x", None),
    ("https://jobs.example.com/careers?domain=example.com",
     ("eightfold", "jobs.example.com/example.com")),
    ("https://www.example.com/careers", None),
])
def test_career_systems_are_recognised_in_addresses_and_pages(text, expected):
    assert board_in(text) == expected


def test_a_page_can_be_the_career_site_itself_or_use_a_system_not_read_yet():
    page = '<link href="https://rmkcdn.successfactors.com/abc/style.css">'
    assert own_address_board("https://jobs.example.com/", page) == (
        "successfactors", "jobs.example.com")
    assert own_address_board("https://www.example.com/", "<html></html>") is None
    assert system_not_read("https://acme.taleo.net/careersection/2/jobsearch.ftl") == "Taleo"
    assert board_in("https://acme.softgarden.io/job/1") == ("softgarden", "acme")
    assert board_in("https://acme-gmbh.jobs.personio.de/job/1") == ("personio", "acme-gmbh")
    assert board_in("https://acme.jobs.personio.com/") == ("personio", "acme.jobs.personio.com")
    assert system_not_read("https://www.example.com/") is None


def test_the_ai_s_lines_are_read_whatever_their_decoration():
    text = ("Here they are:\n"
            "Beacon Hospital | IE | https://beacon.teamtailor.com\n"
            "* **Mater Private** | ie | [careers](https://www.materprivate.ie/careers) |\n"
            "St. Vincent's | Dublin | careers.svuh.ie\n"
            "no address here | IE |\n"
            "| Name | Country | Address |\n"
            "|---|---|---|\n"
            "| Bon Secours | IE | https://bonsecours.wd3.myworkdayjobs.com/Careers |\n"
            "12. Hermitage Clinic | IE | hermitageclinic.ie/careers\n")
    assert employers.parse_lines(text, "IE") == [
        ("Beacon Hospital", "IE", "https://beacon.teamtailor.com"),
        ("Mater Private", "IE", "https://www.materprivate.ie/careers"),
        ("St. Vincent's", "IE", "careers.svuh.ie"),
        ("Bon Secours", "IE", "https://bonsecours.wd3.myworkdayjobs.com/Careers"),
        ("Hermitage Clinic", "IE", "hermitageclinic.ie/careers"),
    ]


class FinderAI:
    """Answers the search for employers with made-up hospitals."""

    can_search_the_web = True

    def __init__(self, answer):
        self.answer = answer
        self.asked: list[str] = []

    def research(self, **request):
        self.asked.append(request["prompt"])
        return ResearchReply(self.answer, [Source("https://search.test", "Search")],
                             Usage(100, 50, web_searches=3))

    def complete_json(self, **request):
        raise AssertionError("not used")

    def list_models(self):
        return []


class FakeTeamtailor(CareerSystemSource):
    id = "teamtailor"
    name = "Teamtailor"
    system = "teamtailor"
    lists = {"beacon": {"IE": 12, OTHER: 0}, "gone": None, "abroad": {OTHER: 5}}

    def survey(self, employer, ctx):
        counts = self.lists.get(employer.board)
        if counts is None:
            raise EmployerNotFound("No job list")
        survey = Survey(counts=Counter(counts))
        if counts.get("IE"):
            survey.towns["IE"] = {"Dublin"}
        return survey


def ai_client(adapter):
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "m"
    return AIClient(settings, adapter=adapter, sleep=lambda seconds: None)


def web(pages):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        page = pages.get(f"{request.url.host}{request.url.path}")
        return httpx.Response(200, text=page) if page is not None else httpx.Response(404)

    return PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))


def test_the_ai_names_employers_and_jobcu_keeps_the_lists_it_can_read(monkeypatch):
    monkeypatch.setattr(employers, "career_sources", lambda: [FakeTeamtailor()])
    ai = FinderAI("Beacon Hospital | IE | https://www.beacon.test/careers/nursing\n"
                  "Old Clinic | IE | https://gone.teamtailor.com\n"
                  "Big Group | IE | https://abroad.teamtailor.com\n"
                  "Bosch | IE | https://jobs.bosch.test/\n"
                  "Nowhere | IE | https://www.nowhere.test/jobs/nurses\n")
    pages = {
        # The address the AI gave doesn't exist; the page one level up links to the job list.
        "www.beacon.test/careers/": '<a href="https://beacon.teamtailor.com/jobs">Jobs</a>',
        "jobs.bosch.test/": '<a href="https://jobs.smartrecruiters.com/BoschGroup">Jobs</a>',
    }
    client = ai_client(ai)
    found = employers.find(client, web(pages), NURSE, ["IE"], [], now=NOW)
    assert found.looked and found.named == 5
    assert found.new == ["Beacon Hospital"] and found.read == 1
    assert found.not_read == {"SmartRecruiters": ["Bosch"]} and found.known == 0
    [beacon] = found_employers()
    assert (beacon.system, beacon.board, beacon.countries) == ("teamtailor", "beacon", ("IE",))
    assert beacon.towns == {"IE": ("Dublin",)} and beacon.found_by_ai and not beacon.elsewhere
    assert "Place: Ireland" in ai.asked[0] and "intensive care" in ai.asked[0]
    # The search's own allowance of web look-ups is untouched.
    assert client.web_searches_used == 0

    # A week later the AI isn't asked again; the employers found are read all the same.
    again = employers.find(client, web(pages), NURSE, ["IE"], [], now=NOW + timedelta(days=7))
    assert not again.looked and again.read == 1 and again.since == NOW
    assert len(ai.asked) == 1
    # After REFRESH_DAYS, or for other work, it looks again.
    employers.find(client, web(pages), NURSE, ["IE"], [], now=NOW + timedelta(days=15))
    chef = NURSE.model_copy(update={"field": "Professional cooking", "target_roles": ["Sous-chef"]})
    employers.find(client, web(pages), chef, ["IE"], [], now=NOW + timedelta(days=15))
    assert len(ai.asked) == 3


class FakeSmartRecruiters(FakeTeamtailor):
    id = system = "smartrecruiters"
    name = "Company career sites (SmartRecruiters)"
    read: list = []

    def survey(self, employer, ctx):
        self.read.append(employer.board)
        return Survey(counts=Counter({"IE": 4}))


def test_the_ai_s_employers_are_checked_only_on_readers_the_person_uses(monkeypatch):
    FakeSmartRecruiters.read = []
    monkeypatch.setattr(employers, "career_sources",
                        lambda: [FakeTeamtailor(), FakeSmartRecruiters()])
    ai = FinderAI("Acme Devices | IE | https://jobs.smartrecruiters.com/AcmeDevices1\n")
    client = ai_client(ai)
    # Its site's terms not accepted: the list isn't read, and the employer is named as one on a
    # system the person doesn't use.
    found = employers.find(client, web({}), NURSE, ["IE"], [], now=NOW, systems={"teamtailor"})
    assert found.new == [] and found.not_read == {"SmartRecruiters": ["Acme Devices"]}
    assert FakeSmartRecruiters.read == []
    # Accepted: checked and kept like any other.
    found = employers.find(client, web({}), NURSE, ["IE"], [], now=NOW + timedelta(days=15),
                           systems={"teamtailor", "smartrecruiters"})
    assert found.new == ["Acme Devices"] and FakeSmartRecruiters.read == ["AcmeDevices1"]


def test_refused_web_research_does_not_record_a_successful_employer_refresh():
    from jobcu.ai.base import AIWebSearchUnavailable

    class Refused(FinderAI):
        def research(self, **request):
            raise AIWebSearchUnavailable("Web research unavailable")

    with pytest.raises(AIWebSearchUnavailable):
        employers.find(ai_client(Refused("")), web({}), NURSE, ["IE"], [], now=NOW)
    # Billing or model changes take effect on the next search, not in two weeks.
    working = FinderAI("")
    found = employers.find(ai_client(working), web({}), NURSE, ["IE"], [], now=NOW)
    assert found.looked and len(working.asked) == 1


def test_a_careers_page_without_a_system_leads_to_its_job_list_or_job_host():
    import threading

    pages = {
        # Only a link to the job search, one level deeper, shows the system.
        "www.drives.test/karriere": '<a href="/karriere/jobs">Aktuelle Stellenangebote</a>',
        "www.drives.test/karriere/jobs":
            '<a href="https://drives.wd3.myworkdayjobs.com/Careers">Suche</a>',
        # Nothing on the corporate page; the company's own job host runs SuccessFactors.
        "www.radar.test/careers": "<h1>Careers</h1><p>Join us.</p>",
        "jobs.radar.test/": '<script src="https://rmkcdn.successfactors.com/x.js"></script>',
    }
    http, robots, lock = web(pages), {}, threading.Lock()
    assert employers._board_from_page(http, "https://www.drives.test/karriere", robots, lock) == (
        ("workday", "https://drives.wd3.myworkdayjobs.com/Careers"), None)
    assert employers._board_from_page(http, "https://www.radar.test/careers", robots, lock) == (
        ("successfactors", "jobs.radar.test"), None)
    assert employers._job_hosts("https://www.ward.co.uk/x") == [
        "jobs.ward.co.uk", "careers.ward.co.uk", "job.ward.co.uk"]
    assert "jobs.hensoldt.net" not in employers._job_hosts("https://jobs.hensoldt.net/")


def test_a_site_that_never_answers_costs_two_short_tries_and_a_hiccup_loses_nothing():
    import threading

    asked = Counter()

    def handler(request):
        asked[request.url.host] += 1
        if request.url.host == "www.silent.test":
            raise httpx.ReadTimeout("no answer", request=request)
        if request.url.host == "www.shaky.test":
            if asked["www.shaky.test"] == 1:  # one passing hiccup
                raise httpx.ReadTimeout("slow once", request=request)
            if request.url.path == "/robots.txt":
                return httpx.Response(404)
            return httpx.Response(
                200, text='<a href="https://shaky.wd3.myworkdayjobs.com/Careers">Jobs</a>')
        if request.url.host == "careers.redirect.test":
            # A job host that sends tools on to a main site that never answers.
            if request.url.path == "/robots.txt":
                return httpx.Response(404)
            return httpx.Response(302, headers={"location": "https://www.redirect.test/careers"})
        if request.url.host == "www.redirect.test":
            raise httpx.ReadTimeout("no answer", request=request)
        raise httpx.ConnectError("no such host", request=request)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler), resolve=lambda host: [])
    robots, lock = {}, threading.Lock()
    assert employers._board_from_page(
        http, "https://www.silent.test/careers", robots, lock) == (None, None)
    assert asked["www.silent.test"] == 2  # robots.txt twice, then the site counts as closed
    assert employers._board_from_page(http, "https://www.shaky.test/careers", robots, lock) == (
        ("workday", "https://shaky.wd3.myworkdayjobs.com/Careers"), None)
    assert employers._look(http, "https://careers.redirect.test/", robots, lock) is None
    assert not robots["www.redirect.test"].allows("https://www.redirect.test/jobs")


def test_employers_found_are_read_with_the_directory_s_and_forgotten_when_gone(monkeypatch):
    from jobcu.sources.careers import forget_found_employer, save_found_employer

    save_found_employer(Employer("Beacon Hospital", "teamtailor", "beacon", ("IE",),
                                 found_by_ai=True), NOW)
    source = FakeTeamtailor()

    def found(countries):
        return [e.name for e in source.employers(countries) if e.found_by_ai]

    assert found(["IE"]) == ["Beacon Hospital"] and found(["DE"]) == []
    forget_found_employer(found_employers()[0])
    assert found(["IE"]) == []


# --- Career sites learned from the links of a search's jobs (employers.learn) -----------------


class CountingTeamtailor(FakeTeamtailor):
    """FakeTeamtailor that counts the lists it reads; "shy" refuses for now."""

    read: Counter = Counter()

    def survey(self, employer, ctx):
        from jobcu.sources.http import Blocked

        type(self).read[employer.board] += 1
        if employer.board == "shy":
            raise Blocked("shy.teamtailor.com")
        return super().survey(employer, ctx)


def job_from_a_job_site(link, company, source="jsearch"):
    from jobcu.sources.base import FoundJob

    return FoundJob(source=source, source_job_id=link, url="https://www.jobsite.test/ad/1",
                    title="ICU Staff Nurse", company=company,
                    application_options=[{"url": link, "source": company}])


def test_career_sites_named_by_job_links_are_learned_once_and_read_from_the_next_search(
        monkeypatch):
    CountingTeamtailor.read = Counter()
    monkeypatch.setattr(employers, "career_sources", lambda: [CountingTeamtailor()])
    jobs = [job_from_a_job_site("https://beacon.teamtailor.com/jobs/1-nurse", "Beacon Hospital"),
            job_from_a_job_site("https://beacon.teamtailor.com/jobs/2-nurse", "Beacon Hospital"),
            job_from_a_job_site("https://abroad.teamtailor.com/jobs/3", "Big Group"),
            job_from_a_job_site("https://gone.teamtailor.com/jobs/4", "Old Clinic"),
            # A career site's own job names a list Jobcu reads already.
            job_from_a_job_site("https://mine.teamtailor.com/jobs/5", "Mine", source="teamtailor")]
    http = web({})
    assert employers.learn(jobs, http, {"teamtailor"}, now=NOW) == ["Beacon Hospital"]
    [beacon] = found_employers()
    assert (beacon.board, beacon.countries, beacon.found_by_ai) == ("beacon", ("IE",), True)
    assert set(CountingTeamtailor.read) == {"beacon", "abroad", "gone"}

    # The next searches don't check the same sites again: the usable one is read with the
    # directory's employers, the others wait a month.
    assert employers.learn(jobs, http, {"teamtailor"}, now=NOW + timedelta(days=1)) == []
    assert sum(CountingTeamtailor.read.values()) == 3
    employers.learn(jobs, http, {"teamtailor"},
                    now=NOW + timedelta(days=employers.LEARN_AGAIN_DAYS + 1))
    assert CountingTeamtailor.read == Counter({"beacon": 1, "abroad": 2, "gone": 2})


def test_a_site_that_refuses_for_now_is_tried_again_a_week_later(monkeypatch):
    CountingTeamtailor.read = Counter()
    monkeypatch.setattr(employers, "career_sources", lambda: [CountingTeamtailor()])
    jobs = [job_from_a_job_site("https://shy.teamtailor.com/jobs/1", "Shy Clinic")]
    http = web({})
    assert employers.learn(jobs, http, {"teamtailor"}, now=NOW) == []
    employers.learn(jobs, http, {"teamtailor"}, now=NOW + timedelta(days=3))
    assert CountingTeamtailor.read["shy"] == 1
    employers.learn(jobs, http, {"teamtailor"},
                    now=NOW + timedelta(days=employers.LEARN_RETRY_DAYS + 1))
    assert CountingTeamtailor.read["shy"] == 2


def test_the_most_linked_sites_are_checked_first_and_only_on_readers_the_person_uses(
        monkeypatch):
    CountingTeamtailor.read = Counter()
    monkeypatch.setattr(employers, "career_sources", lambda: [CountingTeamtailor()])
    monkeypatch.setattr(employers, "LEARN_PER_SEARCH", 1)
    jobs = [job_from_a_job_site("https://abroad.teamtailor.com/jobs/1", "Big Group"),
            *(job_from_a_job_site(f"https://beacon.teamtailor.com/jobs/{n}", "Beacon Hospital")
              for n in range(3))]
    http = web({})
    # Teamtailor switched off (or a system whose terms the person hasn't accepted): nothing.
    assert employers.learn(jobs, http, set(), now=NOW) == []
    assert not CountingTeamtailor.read
    assert employers.learn(jobs, http, {"teamtailor"}, now=NOW) == ["Beacon Hospital"]
    assert CountingTeamtailor.read == Counter({"beacon": 1})


@pytest.mark.parametrize(("link", "expected"), [
    ("https://jobs.example.test/job/Friedrichshafen-Hardware-Engineer-88046/1234567801/",
     ("successfactors", "jobs.example.test")),
    ("https://acme.jobs.hr.cloud.test/job/Bremen-Engineer-28195/1458085833/",
     ("successfactors", "acme.jobs.hr.cloud.test")),
    ("https://moog.wd5.myworkdayjobs.com/en-US/MOOG_External_Career_Site/job/Cork/x_R1",
     ("workday", "https://moog.wd5.myworkdayjobs.com/MOOG_External_Career_Site")),
    ("https://www.example.test/job/123/", None),  # too short a number for a vacancy
    ("https://www.jobsite.test/ad/1", None),
])
def test_a_job_link_names_the_career_site_it_belongs_to(link, expected):
    from jobcu.sources.careerlinks import board_in_job_link

    assert board_in_job_link(link) == expected


def test_a_search_learns_sites_beside_its_steps_and_says_what_it_found(monkeypatch):
    from jobcu import search
    from jobcu.settings import SearchForm

    asked = {}

    def learn(jobs, http, systems, now=None):
        asked["systems"] = systems
        return ["Beacon Hospital"]

    monkeypatch.setattr(search.employers, "learn", learn)
    run = search.SearchRun(id=1, form=SearchForm(), started_at=NOW.isoformat())
    search._learn_career_sites(run, Settings(), [], web({}))
    run.learning.join(timeout=5)
    assert any("Beacon Hospital" in note and "next search" in note for note in run.notes)
    # Readers whose site terms the person hasn't accepted are never used to learn.
    assert "workday" in asked["systems"] and "smartrecruiters" not in asked["systems"]
    assert "phenom" not in asked["systems"] and "avature" not in asked["systems"]
    # A reader the person switched on, accepting its site's terms, learns like the others.
    accepted = Settings()
    accepted.source_opt_ins = ["smartrecruiters"]
    run = search.SearchRun(id=2, form=SearchForm(), started_at=NOW.isoformat())
    search._learn_career_sites(run, accepted, [], web({}))
    run.learning.join(timeout=5)
    assert "smartrecruiters" in asked["systems"] and "phenom" not in asked["systems"]


def test_another_address_of_a_list_jobcu_reads_is_not_learned_again(monkeypatch):
    from jobcu.sources.careers import save_found_employer

    checked = []

    class Anything(CareerSystemSource):
        id = system = "personio"
        name = "Personio"

        def survey(self, employer, ctx):
            checked.append(employer.board)
            return Survey(counts=Counter({"DE": 3}))

    class AnyOracle(Anything):
        id = system = "oracle"
        name = "Oracle"

    monkeypatch.setattr(employers, "career_sources", lambda: [Anything(), AnyOracle()])
    save_found_employer(Employer("Acme", "personio", "acme", ("DE",), found_by_ai=True), NOW)
    save_found_employer(Employer("Big", "oracle", "abcd.fa.us2.oraclecloud.com/CX", ("DE",),
                                 found_by_ai=True), NOW)
    jobs = [job_from_a_job_site("https://acme.jobs.personio.com/job/1", "Acme"),
            job_from_a_job_site("https://abcd.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/"
                                "en/sites/jobsearch/job/2", "Big"),
            job_from_a_job_site("https://other.jobs.personio.de/job/3", "Other")]
    assert employers.learn(jobs, web({}), {"personio", "oracle"}, now=NOW) == ["Other"]
    assert checked == ["other"]


def test_a_list_named_by_several_addresses_in_one_search_is_checked_once(monkeypatch):
    checked = []

    class AnyOracle(CareerSystemSource):
        id = system = "oracle"
        name = "Oracle"

        def survey(self, employer, ctx):
            checked.append(employer.board)
            return Survey(counts=Counter({"GB": 21}))

    monkeypatch.setattr(employers, "career_sources", lambda: [AnyOracle()])
    base = "https://abcd.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites"
    jobs = [job_from_a_job_site(f"{base}/Aerospace/job/1", "Big"),
            job_from_a_job_site(f"{base}/Aerospace/job/2", "Big"),
            job_from_a_job_site(f"{base}/CX_1/job/3", "Big")]
    assert employers.learn(jobs, web({}), {"oracle"}, now=NOW) == ["Big"]
    assert checked == ["abcd.fa.ocs.oraclecloud.com/Aerospace"]  # the most linked address


def test_a_stopped_search_leaves_the_sites_it_did_not_check_for_the_next_search(monkeypatch):
    from jobcu.sources.http import RequestStopped

    asked = []

    class Stopping(CareerSystemSource):
        id = system = "teamtailor"
        name = "Teamtailor"

        def survey(self, employer, ctx):
            asked.append(employer.board)
            raise RequestStopped("Search stopped before another source request.")

    monkeypatch.setattr(employers, "career_sources", lambda: [Stopping()])
    jobs = [job_from_a_job_site("https://first.teamtailor.com/jobs/1", "First"),
            job_from_a_job_site("https://second.teamtailor.com/jobs/2", "Second")]
    with pytest.raises(RequestStopped):
        employers.learn(jobs, web({}), {"teamtailor"}, now=NOW)
    assert len(asked) == 1
    # Nothing counts as checked: the next search looks at both.
    monkeypatch.setattr(employers, "career_sources", lambda: [CountingTeamtailor()])
    CountingTeamtailor.read = Counter()
    employers.learn(jobs, web({}), {"teamtailor"}, now=NOW + timedelta(hours=1))
    assert set(CountingTeamtailor.read) == {"first", "second"}


def test_an_employers_own_list_of_plain_job_links_is_recognised_and_read(monkeypatch):
    import json as json_module

    from jobcu.sources.listpages import ListPageSource

    monkeypatch.setattr(employers, "career_sources", lambda: [ListPageSource()])

    def posting(title):
        data = {"@type": "JobPosting", "title": title, "datePosted": "2026-09-29",
                "description": "<p>Design power converters.</p>",
                "jobLocation": {"address": {"addressLocality": "Erlangen",
                                            "addressCountry": "DE"}}}
        return f'<script type="application/ld+json">{json_module.dumps(data)}</script>'

    listing = "".join(
        f'<li><a href="/stellen/{title.lower().replace(" ", "-")}-j{number}.html">{title}</a>'
        f'<span>Erlangen</span></li>'
        for number, title in ((4101, "Hardwareentwickler"), (4102, "Elektronikentwickler"),
                              (4103, "Einkäufer")))
    pages = {
        "www.antriebe.test/karriere": '<a href="/karriere/stellen">Offene Stellen</a>'
                                      '<a href="/news/2026/11/messe">Messe</a>',
        "www.antriebe.test/karriere/stellen": f"<ul>{listing}</ul>",
        "www.antriebe.test/stellen/hardwareentwickler-j4101.html": posting("Hardwareentwickler"),
        "www.antriebe.test/stellen/elektronikentwickler-j4102.html":
            posting("Elektronikentwickler"),
        "www.antriebe.test/stellen/einkäufer-j4103.html": posting("Einkäufer"),
    }
    ai = FinderAI("Example Antriebe | DE | https://www.antriebe.test/karriere\n")
    engineer = NURSE.model_copy(update={"field": "Power electronics",
                                        "target_roles": ["Hardware engineer"]})
    found = employers.find(ai_client(ai), web(pages), engineer, ["DE"], [], now=NOW)
    assert found.new == ["Example Antriebe"]
    [antriebe] = found_employers()
    assert (antriebe.system, antriebe.board) == ("listpage",
                                                 "https://www.antriebe.test/karriere/stellen")
    assert antriebe.jobs and antriebe.countries == ("DE",) and antriebe.found_by_ai


@pytest.mark.parametrize(("page", "base", "jobs"), [
    # rexx: the number follows a letter in the address's last part.
    ('<a href="/Hardware-Entwickler-mwd-de-j5301.html?sid=1">a</a>'
     '<a href="/Elektronikentwickler-mwd-de-j4973.html?sid=1">b</a>'
     '<a href="/Einkaeufer-mwd-de-j5338.html?sid=1">c</a><a href="/impressum.html">i</a>',
     "https://jobs.example.test/stellenangebote.html", 3),
    # The number in the query (dSPACE's job finder), in the page's own data.
    ('<div data=\'[{"href":"/career/stellen.cfm?fuseaction=einzel&jid=38208"},'
     '{"href":"/career/stellen.cfm?fuseaction=einzel&jid=38207"},'
     '{"href":"/career/stellen.cfm?fuseaction=einzel&jid=38206"}]\'></div>',
     "https://www.example.test/career/stellen.cfm", 3),
    # The title spelled before the number (Rheinmetall), and a bigger group of product pages
    # whose addresses don't speak of jobs.
    ("".join(f'<a href="/de/job/entwicklungsingenieur_elektronik_{n}__m_w_d_/{900000 + n}">j</a>'
             for n in range(3))
     + "".join(f'<a href="/de/produkte/{155000 + n}/sensor">p</a>' for n in range(6)),
     "https://www.example.test/de/karriere", 3),
    # JazzHR's codes of letters and digits, UUIDs on Rippling.
    ('<a href="/apply/cto8fD1zOl/Senior-Researcher">a</a><a href="/apply/aKRKovG8fV/PhD">b</a>'
     '<a href="/apply/JL3T0dCjY8/Postdoc">c</a>', "https://inst.example.test/apply", 3),
    ("".join(f'<a href="/acme/jobs/{n}1c621ab-52c6-4e4d-ab5b-cf96d3028902">t</a>'
             for n in range(4, 7)), "https://ats.example.test/acme/jobs", 3),
    # Too few links of one shape: no list.
    ('<a href="/jobs/123456">a</a><a href="/jobs/123457">b</a>', "https://x.example.test/", 0),
])
def test_a_list_of_job_links_is_recognised_by_the_shape_of_their_addresses(page, base, jobs):
    import re

    from jobcu.sources.listpages import listed_jobs, recognise

    found = recognise(base, page)
    if not jobs:
        assert found == []
        return
    pattern, sample = found[0]
    assert re.search(pattern, sample)
    assert len(listed_jobs(page, base, re.compile(pattern))[0]) == jobs
