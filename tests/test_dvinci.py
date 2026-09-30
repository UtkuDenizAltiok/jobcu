"""d.vinci career sites, with made-up employers and answers."""

from datetime import UTC, datetime

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.sources import all_sources, dvinci
from jobcu.sources.base import SourceContext, SourceError, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.http import PoliteClient

EMPLOYER = Employer("Klinikum Beispiel", "dvinci", "klinikum-beispiel", ("DE",))


def publication(number, position="Pflegefachperson (m/w/d)", period="UNLIMITED",
                times=("FULL_TIME",), created="2026-09-23T08:00:00.000Z", start=None,
                places=({"name": "Beispielstadt", "latitude": 49.2, "longitude": 11.4,
                         "country": {"isoA2": "DE"}},), kind="DEFAULT"):
    return {
        "id": number, "position": position, "startDate": start,
        "jobPublicationURL": f"https://klinikum-beispiel.dvinci-hr.com/de/jobs/{number}/x",
        "introduction": "<p>Unser Klinikum.</p>", "tasks": "<ul><li>Pflege</li></ul>",
        "profile": "<p>Examen in der Pflege</p>", "weOffer": "<p>Tarif TVöD</p>",
        "closingText": None,
        "jobOpening": {"createdDate": created, "locations": list(places), "type": kind,
                       "contractPeriod": {"internalName": period},
                       "workingTimes": [{"internalName": t} for t in times]},
    }


def context(handler):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), SourceReport("dvinci", "d.vinci"),
                         lambda: False, lambda message: None)


def test_reads_an_employers_publications():
    def handler(request):
        assert request.url.host == "klinikum-beispiel.dvinci-hr.com"
        if request.url.path == "/robots.txt":
            return httpx.Response(404)
        assert request.url.path == "/jobPublication/list.json"
        return httpx.Response(200, json=[publication(1), publication(2, position="")])

    jobs = list(dvinci.DvinciSource().list_jobs(EMPLOYER, context(handler)))
    assert [job.source_job_id for job in jobs] == ["klinikum-beispiel/1"]
    job = jobs[0]
    assert job.company == "Klinikum Beispiel" and job.country == "DE"
    assert job.location_text == "Beispielstadt" and (job.latitude, job.longitude) == (49.2, 11.4)
    # No publication date: the opening's creation counts.
    assert job.posted_at == datetime(2026, 9, 23, 8, tzinfo=UTC)
    assert job.description_is_complete
    assert job.description == "Unser Klinikum.\n\n• Pflege\n\nExamen in der Pflege\n\nTarif TVöD"
    assert job.job_types == ["full_time_permanent"]


def test_contracts_and_working_times_give_job_types():
    def types(**extra):
        return dvinci.to_found_job(publication(1, **extra), EMPLOYER).job_types

    assert types(times=("FULL_TIME", "PART_TIME")) == ["full_time_permanent", "part_time"]
    assert types(period="LIMITED") == ["fixed_term"]
    assert types(times=("PART_TIME",)) == ["part_time"]
    assert types(kind="APPRENTICESHIP") == ["internship_or_working_student"]


def test_a_job_in_several_countries_leaves_the_country_open():
    places = ({"name": "Munich", "country": {"isoA2": "DE"}},
              {"name": "Vienna", "country": {"isoA2": "AT"}})
    job = dvinci.to_found_job(publication(1, places=places), EMPLOYER)
    assert job.country is None and job.location_text == "Munich, Vienna"
    assert job.latitude is None


def test_it_is_one_of_the_career_systems_with_employers_in_the_directory():
    assert any(isinstance(source, dvinci.DvinciSource) for source in all_sources())
    assert len(dvinci.DvinciSource().employers(["DE"])) >= 2


def test_a_dvinci_easy_portal_is_read_at_its_own_host_and_robots_txt_is_respected():
    easy = Employer("MTU Aero Engines", "dvinci", "mtuaero.dvinci-easy.com", ("DE",))
    asked = []

    def handler(request):
        asked.append(f"{request.url.host}{request.url.path}")
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, json=[publication(1)])

    assert len(list(dvinci.DvinciSource().list_jobs(easy, context(handler)))) == 1
    assert asked == ["mtuaero.dvinci-easy.com/robots.txt",
                     "mtuaero.dvinci-easy.com/jobPublication/list.json"]

    def closed(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /jobPublication/\n")
        raise AssertionError("the list must not be asked for")

    with pytest.raises(SourceError):
        list(dvinci.DvinciSource().list_jobs(easy, context(closed)))
