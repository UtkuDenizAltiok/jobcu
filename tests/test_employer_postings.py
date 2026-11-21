"""The employer's own posting of a job that came only from job sites (employerpostings.py)."""

import json
from datetime import UTC, datetime, timedelta

import httpx

from jobcu import employerpostings
from jobcu.dedupe import group_duplicates
from jobcu.filters import first_posted_by_employer
from jobcu.keystore import KeyStore
from jobcu.sources import careers
from jobcu.sources import workday as wd
from jobcu.sources.base import FoundJob
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

NOW = datetime.now(UTC)
START = NOW - timedelta(hours=24)
BOARD = "https://fakeco.wd1.myworkdayjobs.com/External"
AD = ("Join our graduate programme in electronic engineering. You will design and test circuit "
      "boards for our sensing products, working with experienced engineers in our Limerick "
      "laboratory. A degree in electronic engineering is required.")


def board_copy(title="Graduate Electronics Engineer", location="Limerick", **extra):
    return FoundJob(source="jsearch", source_job_id="js-1", url="https://board.example/js-1",
                    title=title, company="FakeCo Ltd", country="IE", location_text=location,
                    posted_at=NOW - timedelta(hours=3), date_precision="exact",
                    description=AD, description_is_complete=True, **extra)


def group(*copies, kinds=None):
    kinds = kinds or {"jsearch": "aggregator"}
    return group_duplicates(list(copies), kinds)[0]


def site(listed, *, ad=AD, location="Limerick, Ireland", start_date=None, robots=None,
         asked=None):
    start_date = start_date or (NOW - timedelta(days=24)).date().isoformat()

    def handler(request):
        if asked is not None:
            asked.append((request.method, request.url.path))
        if request.url.path == "/robots.txt":
            if robots is not None:
                return robots
            return httpx.Response(200, text="User-agent: *\nAllow: /External/\n")
        if request.method == "POST":
            body = json.loads(request.content)
            assert body["searchText"]
            return httpx.Response(200, json={"total": len(listed), "jobPostings": listed})
        return httpx.Response(200, json={"jobPostingInfo": {
            "jobDescription": f"<p>{ad}</p>", "startDate": start_date, "location": location}})

    return handler


def listing(title, path="/job/Limerick/Graduate-Electronics-Engineer_R1"):
    return {"title": title, "externalPath": path, "locationsText": "Limerick, Ireland",
            "postedOn": "Posted 24 Days Ago"}


def find(groups, handler, monkeypatch, employers=None):
    employers = employers or (Employer("FakeCo", "workday", BOARD, ("IE",)),)
    monkeypatch.setattr(careers, "load_directory", lambda: employers)
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    try:
        return employerpostings.find(groups, list(range(len(groups))),
                                     {"workday": wd.WorkdaySource()}, http, KeyStore(), {},
                                     lambda: False, lambda m: None, START)
    finally:
        http.close()


def test_a_job_only_a_job_site_listed_gets_the_employers_own_posting(monkeypatch):
    # A graduate programme posted weeks ago that a job site listed again came in with the job
    # site's link and date only: Workday lists are read newest first and stop at older jobs.
    job = group(board_copy())
    found = find([job], site([listing("Graduate Electronics Engineer")]), monkeypatch)
    assert found == 1
    posting = job.copies[-1]
    assert posting.source == "workday" and posting.description_is_complete
    assert posting.url.startswith("https://fakeco.wd1.myworkdayjobs.com/External/job/")
    assert job.source_kinds["workday"] == "employer" and job.main is posting
    # Posted 24 days ago by the employer: a repost with the employer's date (filters.py).
    assert first_posted_by_employer(job, START) == posting.posted_at


def test_the_same_title_elsewhere_or_with_other_work_is_another_vacancy(monkeypatch):
    other_town = group(board_copy(location="Dublin"))
    assert find([other_town], site([listing("Graduate Electronics Engineer")]),
                monkeypatch) == 0
    # The same title in another country isn't this job either.
    abroad = group(board_copy())
    assert find([abroad], site([listing("Graduate Electronics Engineer")],
                               location="Munich, Germany"), monkeypatch) == 0
    # Nor a listing whose full ad is about different work.
    different = group(board_copy())
    other_ad = ("Sell our software licences to retail customers across the region, meeting "
                "monthly targets and keeping the sales pipeline up to date in our CRM tool.")
    assert find([different], site([listing("Graduate Electronics Engineer")], ad=other_ad),
                monkeypatch) == 0
    # Nor a different title.
    assert find([group(board_copy())], site([listing("Senior Firmware Architect")]),
                monkeypatch) == 0


def test_a_job_with_its_employers_copy_or_of_another_company_is_not_looked_up(monkeypatch):
    asked = []
    own = FoundJob(source="workday", source_job_id="w-1", url="https://x.example/w-1",
                   title="Graduate Electronics Engineer", company="FakeCo", country="IE",
                   location_text="Limerick", posted_at=NOW, date_precision="day")
    has_employer_copy = group(board_copy(), own, kinds={"jsearch": "aggregator",
                                                         "workday": "employer"})
    stranger = group(FoundJob(
        source="jsearch", source_job_id="js-2", url="https://board.example/js-2",
        title="Graduate Electronics Engineer", company="Other Industries", country="IE",
        location_text="Limerick", posted_at=NOW, date_precision="exact"))
    assert find([has_employer_copy, stranger], site([], asked=asked), monkeypatch) == 0
    assert asked == []


def test_a_site_that_refuses_jobcu_is_left_alone(monkeypatch):
    asked = []
    challenge = httpx.Response(429, text="<div class='captcha-box'>Security Check</div>")
    job = group(board_copy())
    assert find([job], site([listing("Graduate Electronics Engineer")], robots=challenge,
                            asked=asked), monkeypatch) == 0
    assert asked == [("GET", "/robots.txt")] and len(job.copies) == 1


def test_a_title_found_in_another_country_is_not_read(monkeypatch):
    # A title search answers from every country; the list's own place rules those out first.
    asked = []
    abroad = {**listing("Graduate Electronics Engineer", "/job/Austin/Graduate_R9"),
              "locationsText": "Austin, Texas, United States"}
    job = group(board_copy())
    assert find([job], site([abroad, listing("Graduate Electronics Engineer")], asked=asked),
                monkeypatch) == 1
    read = [path for method, path in asked if method == "GET" and path != "/robots.txt"]
    assert len(read) == 1 and not read[0].endswith("Graduate_R9")
    assert job.copies[-1].url.endswith("Graduate-Electronics-Engineer_R1")
