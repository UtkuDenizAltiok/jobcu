"""FreeHire, with made-up answers (never the real site)."""

from datetime import UTC, datetime, timedelta

import httpx

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.location import Place
from jobcu.sources import date_lags, freehire
from jobcu.sources.base import JobQuery, SourceContext, SourceReport
from jobcu.sources.http import PoliteClient

NOW = datetime.now(UTC).replace(microsecond=0)


def term(text, language="en", kind="job_title"):
    return SearchTerm(text=text, language=language, kind=kind)


def stamp(hours_ago):
    return (NOW - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")


def ad(slug, title="Hardware Engineer", source="greenhouse", location="Munich, Germany",
       countries=("de",), posted=2, first=1, **extra):
    return {"public_slug": slug, "title": title, "company": "FakeCo GmbH", "source": source,
            "url": f"https://jobs.example.com/{slug}?utm_source=freehire.me",
            "location": location, "countries": list(countries), "cities": [],
            "description": "<p>Design power converters</p><ul><li>PCB layout</li></ul>",
            "posted_at": stamp(posted) if posted is not None else None,
            "created_at": stamp(first), "reality": {"class": "fresh"}, **extra}


def context(handler, report=None):
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    return SourceContext(http, KeyStore(), report or SourceReport("freehire", "FreeHire"),
                         lambda: False, lambda message: None)


def answering(jobs, originals=("greenhouse", "workday"), seen=None, facets_status=200):
    def handler(request):
        if seen is not None:
            seen.append(request)
        if request.url.path.endswith("/jobs/facets"):
            facets = {"data": {"total": 9, "facets": {"source": dict.fromkeys(originals, 3)}}}
            return httpx.Response(facets_status, json=facets)
        page = jobs(request) if callable(jobs) else jobs
        return httpx.Response(200, json={"data": page, "meta": {"total": len(page)}})
    return handler


def query(terms=None, countries=("DE",), hours=24, places=()):
    return JobQuery(list(countries), list(places), terms or [term("Hardware Engineer")], hours,
                    NOW)


def test_titles_and_field_words_become_few_searches_in_the_languages_searched():
    terms = [term("Hardware Engineer"), term("Embedded Hardware Engineer"),
             term("Power Electronics Engineer"), term("Electronics Engineer"),
             term("PCB Designer"), term("Test Engineer"), term("Circuit Designer"),
             term("Hardwareentwickler", "de"), term("Ingeniero de hardware", "es"),
             term("power electronics", kind="field_or_skill"),
             term("Power Electronics", kind="field_or_skill"),
             term('"SiC" -inverters', kind="field_or_skill")]
    searches = freehire.plan_searches(terms, ["DE"])
    assert searches == [
        # "Embedded Hardware Engineer" is found by "Hardware Engineer" and "Power Electronics
        # Engineer" by "Electronics Engineer"; Spanish isn't searched.
        {"q": 'title:"Hardware Engineer" OR title:"Electronics Engineer" OR '
              'title:"PCB Designer" OR title:"Test Engineer" OR title:"Circuit Designer"'},
        {"q": 'title:"Hardwareentwickler"'},
        {"q": '"power electronics" OR "SiC inverters"', "q_fields": "title,description"},
    ]
    assert freehire.plan_searches([term("Hardwareentwickler", "de")], ["GB"]) == []


def test_employer_originals_are_complete_ads_and_board_copies_are_not():
    seen = []
    jobs = [ad("a"), ad("b", source="adzuna", title="Hardware Engineer &amp; Tester"),
            ad("c", source="arbeitnow")]
    found = list(freehire.FreeHireSource().search(query(), context(answering(jobs, seen=seen))))
    by_id = {job.source_job_id: job for job in found}
    assert set(by_id) == {"a", "b", "c"}
    original = by_id["a"]
    assert original.description_is_complete and original.employer_url == original.url
    assert original.description == "Design power converters\n• PCB layout"
    assert original.country == "DE" and original.company == "FakeCo GmbH"
    copy = by_id["b"]
    assert not copy.description_is_complete and copy.employer_url is None
    assert copy.title == "Hardware Engineer & Tester"
    search = seen[1].url.params
    assert seen[0].url.path == "/api/v1/jobs/facets"
    assert seen[1].url.path == "/api/v1/agent/jobs/search"
    assert search.get_list("countries") == ["de"]
    # 24 hours plus FreeHire's two-day lag, in whole days of its first sight.
    assert search["open_within_days"] == "3"


def test_without_its_source_list_every_ad_is_still_found_as_a_board_copy():
    jobs = [ad("a")]
    found = list(freehire.FreeHireSource().search(
        query(), context(answering(jobs, facets_status=503))))
    assert [job.source_job_id for job in found] == ["a"]
    assert not found[0].description_is_complete and found[0].employer_url is None


def test_a_restated_date_never_makes_an_old_ad_fresh():
    jobs = [
        # The board says yesterday, but FreeHire saw this vacancy three weeks ago.
        ad("restated", posted=20, first=24 * 21),
        # FreeHire's own flag for a refreshed date.
        ad("flagged", posted=3, first=3, reality={"fake_freshness": True}),
        # Listed a day late: counts from its own date, within the lag.
        ad("late", posted=40, first=2),
        ad("day", posted=None, first=1),
    ]
    found = {job.source_job_id: job for job in freehire.FreeHireSource().search(
        query(), context(answering(jobs)))}
    assert set(found) == {"restated", "late", "day"}
    assert found["restated"].older_copy and found["restated"].date_precision == "exact"
    assert found["restated"].posted_at == NOW - timedelta(hours=24 * 21)
    assert not found["late"].older_copy
    assert found["late"].posted_at == NOW - timedelta(hours=40)
    # Its first sight alone can't date an ad.
    assert found["day"].posted_at is None and found["day"].date_precision == "unknown"
    assert date_lags()["freehire"] == freehire.LAG_HOURS


def test_a_whole_day_counts_as_a_day():
    item = ad("d")
    item["posted_at"] = (NOW - timedelta(days=1)).date().isoformat() + "T00:00:00Z"
    job = freehire.to_found_job(item, ["DE"], frozenset({"greenhouse"}))
    assert job.date_precision == "day"


def test_country_names_and_places():
    jobs = [ad("munich"), ad("berlin", location="Berlin, Germany"),
            ad("both", location="Kassel, DE, 34123", countries=("de", "us")),
            ad("london", location="London, United Kingdom", countries=("gb",)),
            ad("nowhere", location="", countries=("fr",))]
    munich = Place(name="Munich", local_name="München", country="DE", kind="city", radius_km=None)
    found = list(freehire.FreeHireSource().search(
        query(countries=("DE", "GB"), places=[munich]), context(answering(jobs))))
    assert {job.source_job_id: job.country for job in found} == {"munich": "DE", "london": "GB"}


def test_the_occupation_eures_adds_to_german_titles_is_left_out():
    def title(text, country="DE"):
        item = ad("e", title=text, source="eures", countries=(country.lower(),),
                  location="Dresden, Germany" if country == "DE" else "Cork, Ireland")
        return freehire.to_found_job(item, [country], frozenset()).title

    assert title("Senior Engineer (m/w/d) (Embedded-Systems-Entwickler/in)") == \
        "Senior Engineer (m/w/d)"
    assert title("Bautechniker (m/w/d), Köln (Techniker/in - Elektrotechnik (Informations- und "
                 "Kommunikationstechnik))") == "Bautechniker (m/w/d), Köln"
    assert title("Hardwareentwickler (m/w/d)") == "Hardwareentwickler (m/w/d)"
    assert title("Hardwareentwickler (Elektronik") == "Hardwareentwickler (Elektronik"
    assert title("Hardware Engineer (Cork)", "IE") == "Hardware Engineer (Cork)"
    # Merged with the agency's own ad once the occupation is gone.
    from jobcu.dedupe import group_duplicates
    from jobcu.sources.base import FoundJob

    eures = freehire.to_found_job(
        ad("e", title="Senior Engineer (m/w/d) (Hardwareentwickler/in)", source="eures",
           location="Dresden, Germany"), ["DE"], frozenset())
    agency = FoundJob(source="bundesagentur", source_job_id="1-2", url="https://example.com/1",
                      title="Senior Engineer (m/w/d)", company="FakeCo GmbH",
                      location_text="Dresden", country="DE")
    assert len(group_duplicates([eures, agency], {"bundesagentur": "job_board",
                                                  "freehire": "aggregator"})) == 1


def test_a_career_system_address_is_not_a_company_name():
    item = ad("x")
    item["company"] = "jobs.example-group.com"
    assert freehire.to_found_job(item, ["DE"], frozenset()).company is None


def test_reads_further_pages_only_while_they_are_full():
    pages = {"0": [ad(f"p{i}") for i in range(freehire.PAGE_SIZE)], "50": [ad("last")]}
    seen = []

    def jobs(request):
        return pages.get(request.url.params["offset"], [])

    def handler(request):
        if not request.url.path.endswith("/jobs/facets"):
            seen.append(request.url.params["offset"])
            page = jobs(request)
            return httpx.Response(200, json={"data": page, "meta": {"total": 51}})
        return httpx.Response(200, json={"data": {"facets": {"source": {"greenhouse": 1}}}})

    found = list(freehire.FreeHireSource().search(query(), context(handler)))
    assert len(found) == freehire.PAGE_SIZE + 1
    assert seen == ["0", "50"]


def test_slow_down_answer_ends_the_source_as_partial():
    report = SourceReport("freehire", "FreeHire")

    def handler(request):
        if request.url.path.endswith("/jobs/facets"):
            return httpx.Response(200, json={"data": {"facets": {"source": {}}}})
        return httpx.Response(429, headers={"Retry-After": "0"})

    assert list(freehire.FreeHireSource().search(query(), context(handler, report))) == []
    assert report.status == "partial" and "slow down" in report.message
