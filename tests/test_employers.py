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
    assert system_not_read("https://jobs.smartrecruiters.com/BoschGroup") == "SmartRecruiters"
    assert board_in("https://acme.softgarden.io/job/1") == ("softgarden", "acme")
    assert board_in("https://acme-gmbh.jobs.personio.de/job/1") == ("personio", "acme-gmbh")
    assert board_in("https://acme.jobs.personio.com/") == ("personio", "acme.jobs.personio.com")
    assert system_not_read("https://www.example.com/") is None


def test_the_ai_s_lines_are_read_whatever_their_decoration():
    text = ("Here they are:\n"
            "Beacon Hospital | IE | https://beacon.teamtailor.com\n"
            "* **Mater Private** | ie | [careers](https://www.materprivate.ie/careers) |\n"
            "St. Vincent's | Dublin | careers.svuh.ie\n"
            "no address here | IE |\n")
    assert employers.parse_lines(text, "IE") == [
        ("Beacon Hospital", "IE", "https://beacon.teamtailor.com"),
        ("Mater Private", "IE", "https://www.materprivate.ie/careers"),
        ("St. Vincent's", "IE", "careers.svuh.ie"),
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
