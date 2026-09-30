"""Oracle Recruiting Cloud career sites, with made-up employers and answers."""

from datetime import UTC, date, datetime

import httpx
import pytest

from jobcu.freshness import day_at_utc
from jobcu.keystore import KeyStore
from jobcu.sources import all_sources, oracle
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

HOST = "abcd.fa.em2.oraclecloud.com"
EMPLOYER = Employer("Beispiel Power", "oracle", f"{HOST}/CX_1", ("DE", "IE"))
START = datetime(2026, 9, 27, 18, 35, tzinfo=UTC)


def requisition(number, title="Power Electronics Engineer", day="2026-09-30",
                place="Munich, Bayern, Germany", country="DE", others=()):
    return {"Id": str(number), "Title": title, "PostedDate": day, "PrimaryLocation": place,
            "PrimaryLocationCountry": country, "WorkplaceType": None,
            "secondaryLocations": [{"Name": name, "CountryCode": code} for name, code in others]}


def page(*jobs, total=None):
    return {"items": [{"TotalJobsCount": len(jobs) if total is None else total,
                       "requisitionList": list(jobs)}]}


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("oracle", "Oracle"),
                         lambda: False, lambda message: None)


def not_found(request):
    return httpx.Response(404)  # no robots.txt: nothing is closed


def test_reads_the_newest_jobs_until_they_are_older_than_the_window():
    asked = []

    def handler(request):
        if request.url.path == "/robots.txt":
            return not_found(request)
        asked.append(request.url.params["finder"])
        assert request.url.host == HOST
        assert request.url.path == "/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        return httpx.Response(200, json=page(
            requisition(1),
            requisition(2, title="Hardware Engineer", place="Cork, Co. Cork, Ireland",
                        country="IE", others=[("Allen, TX, United States", "US")]),
            requisition(3, title="Old Job", day="2026-09-20"),
            requisition(4, title="Older Still", day="2026-09-19"), total=250))

    jobs = list(oracle.OracleSource().list_jobs(EMPLOYER, context(handler), start=START))
    assert [job.title for job in jobs] == ["Power Electronics Engineer", "Hardware Engineer"]
    assert asked == ["findReqs;siteNumber=CX_1,limit=100,offset=0,sortBy=POSTING_DATES_DESC"]
    first, second = jobs
    assert first.source_job_id == f"{HOST}/CX_1/1" and first.company == "Beispiel Power"
    assert first.url == f"https://{HOST}/hcmUI/CandidateExperience/en/sites/CX_1/job/1"
    assert first.country == "DE" and first.location_text == "Munich, Bayern, Germany"
    assert first.posted_at == day_at_utc(date(2026, 9, 30))
    assert first.date_precision == "day"
    # Places in two countries leave the country to the place names ("Cork" is Ireland).
    assert second.country is None
    assert second.location_text == "Cork, Co. Cork, Ireland; Allen, TX, United States"


def test_pages_on_while_the_jobs_are_new():
    offsets = []

    def handler(request):
        if request.url.path == "/robots.txt":
            return not_found(request)
        offsets.append(request.url.params["finder"].split("offset=")[1].split(",")[0])
        return httpx.Response(200, json=page(
            *[requisition(len(offsets) * 1000 + i) for i in range(oracle.PAGE_SIZE)],
            total=150))

    jobs = list(oracle.OracleSource().list_jobs(EMPLOYER, context(handler), start=START))
    assert offsets == ["0", "100"] and len(jobs) == 200


def test_the_job_s_own_record_gives_the_full_ad_the_exact_time_and_the_working_time():
    def handler(request):
        if request.url.path == "/robots.txt":
            return not_found(request)
        if request.url.path.endswith("recruitingCEJobRequisitionDetails"):
            assert request.url.params["finder"] == 'ById;Id="1",siteNumber=CX_1'
            return httpx.Response(200, json={"items": [{
                "ExternalDescriptionStr": "<p>Design SiC inverters.</p>",
                "ExternalResponsibilitiesStr": "<ul><li>Bring-up</li></ul>",
                "ExternalQualificationsStr": "<p>MSc in electrical engineering</p>",
                "ExternalPostedStartDate": "2026-09-30T15:05:42+00:00",
                "JobSchedule": "Full time", "WorkplaceType": "On-site"}]})
        return httpx.Response(200, json=page(requisition(1)))

    source = oracle.OracleSource()
    ctx = context(handler)
    job = source.load_details(next(source.list_jobs(EMPLOYER, ctx)), ctx)
    assert job.description == ("Design SiC inverters.\n\n• Bring-up\n\n"
                               "MSc in electrical engineering")
    assert job.description_is_complete and job.date_precision == "exact"
    assert job.posted_at == datetime(2026, 9, 30, 15, 5, 42, tzinfo=UTC)
    assert job.job_types == ["full_time_permanent", "fixed_term"]


def test_a_site_whose_robots_txt_closes_the_list_is_not_read():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /hcmRestApi/")
        raise AssertionError("the job list must not be asked for")

    with pytest.raises(SourceError):
        list(oracle.OracleSource().list_jobs(EMPLOYER, context(handler)))


def test_it_is_one_of_the_career_systems_with_employers_in_the_directory():
    assert any(isinstance(source, oracle.OracleSource) for source in all_sources())
