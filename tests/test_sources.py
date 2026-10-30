import socket
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.location import Place
from jobcu.sources import adzuna, bundesagentur, reed
from jobcu.sources.base import JobQuery, SourceContext, SourceError, SourceReport
from jobcu.sources.budget import BudgetExhausted, Limits, RequestBudget
from jobcu.sources.http import Blocked, PoliteClient, SourceTermsDenied, terms_denial

NOW = datetime.now(UTC)


def term(text, language="en", kind="job_title"):
    return SearchTerm(text=text, language=language, kind=kind)


def context(handler, source_id="test"):
    keys = KeyStore()
    keys.set("adzuna_app_id", "fake-id-123")
    keys.set("adzuna_app_key", "fake-key-1234567890")
    keys.set("reed_api_key", "fake-reed-key-123456")
    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    report = SourceReport(source_id, source_id)
    return SourceContext(http, keys, report, lambda: False, lambda message: None)


# --- Adzuna ---------------------------------------------------------------------------


def test_adzuna_asks_for_titles_in_the_title_first_then_specialist_words_anywhere():
    terms = [term("Hardware Engineer"), term("Hardware Design Engineer"),
             term("Embedded Hardware Engineer"), term("PCB Design Engineer"),
             term("Hardwareentwickler", "de"), term("Hardware Engineer", "de"),
             term("Leistungselektronik", "de", "field_or_skill"),
             term("Schaltungsentwicklung", "de", "field_or_skill"),
             term("power electronics", kind="field_or_skill"),
             term("Power Electronics", "de", "field_or_skill"), term("Ingénieur hardware", "fr")]
    assert adzuna.plan_searches(terms, "DE") == [
        # "Hardware Design Engineer" and "Embedded Hardware Engineer" are found by the first.
        {"title_only": "Hardware Engineer"},
        {"title_only": "PCB Design Engineer"},
        {"title_only": "Hardwareentwickler"},
        {"what_or": "Leistungselektronik Schaltungsentwicklung"},
        {"what_phrase": "power electronics"},
    ]


def adzuna_item(job_id, created):
    return {"id": job_id, "title": "Hardware Engineer", "created": created,
            "company": {"display_name": "Acme"}, "location": {"display_name": "Berlin"},
            "redirect_url": f"https://www.adzuna.de/land/ad/{job_id}",
            "contract_type": "permanent", "contract_time": "full_time", "description": "Short"}


def test_adzuna_reads_by_relevance_and_keeps_only_jobs_inside_the_window():
    fresh = (NOW - timedelta(hours=2)).isoformat()
    old = (NOW - timedelta(hours=30)).isoformat()  # inside Adzuna's whole days, outside 24 h
    requests = []

    def handler(request):
        requests.append(dict(request.url.params))
        page = int(request.url.path.rsplit("/", 1)[1])
        if page == 1:
            results = [adzuna_item("old", old)] + [adzuna_item(str(i), fresh) for i in range(49)]
        else:
            results = [adzuna_item(f"p2-{i}", fresh) for i in range(10)]
        return httpx.Response(200, json={"count": 60, "results": results})

    ctx = context(handler, "adzuna")
    query = JobQuery(["DE"], [], [term("Hardwareentwickler", "de")], 24, NOW)
    jobs = list(adzuna.AdzunaSource().search(query, ctx))
    assert len(jobs) == 59 and len(requests) == 2
    assert requests[0]["sort_by"] == "relevance"
    assert requests[0]["title_only"] == "Hardwareentwickler"
    assert jobs[0].job_types == ["full_time_permanent"] and jobs[0].date_precision == "exact"
    assert not jobs[0].description_is_complete


def test_a_broad_adzuna_search_gets_a_fair_part_and_can_t_crowd_out_the_rest(monkeypatch):
    monkeypatch.setattr(adzuna, "share_of_month", lambda source, limits, **kw: Limits(
        per_search=6, per_day=240, per_month=2400))
    fresh = (NOW - timedelta(hours=2)).isoformat()
    asked = []

    def handler(request):  # every search matches endless ads
        params = dict(request.url.params)
        asked.append("title" if "title_only" in params else "phrase")
        return httpx.Response(200, json={"count": 5000, "results": [
            adzuna_item(f"{len(asked)}-{i}", fresh) for i in range(50)]})

    query = JobQuery(["DE"], [], [term("Hardwareentwickler", "de"),
                                  term("power electronics", kind="field_or_skill")], 24, NOW)
    list(adzuna.AdzunaSource().search(query, context(handler, "adzuna")))
    assert asked == ["title"] * 3 + ["phrase"] * 3


def test_what_one_country_doesn_t_need_goes_to_the_next(monkeypatch):
    monkeypatch.setattr(adzuna, "share_of_month", lambda source, limits, **kw: Limits(
        per_search=8, per_day=240, per_month=2400))
    fresh = (NOW - timedelta(hours=2)).isoformat()
    asked = []

    def handler(request):  # Germany has three ads; the UK has endless ones
        country = request.url.path.split("/")[-3]
        asked.append(country)
        count = 3 if country == "de" else 50
        return httpx.Response(200, json={"results": [
            adzuna_item(f"{len(asked)}-{i}", fresh) for i in range(count)]})

    query = JobQuery(["DE", "GB"], [], [term("Hardware Engineer")], 24, NOW)
    list(adzuna.AdzunaSource().search(query, context(handler, "adzuna")))
    assert asked == ["de"] + ["gb"] * 7


def test_a_country_with_more_search_words_gets_a_bigger_share():
    asked = []

    def handler(request):  # every search matches endless ads
        asked.append(request.url.path.split("/")[-3])
        return httpx.Response(200, json={"results": [
            adzuna_item(f"{len(asked)}-{i}", (NOW - timedelta(hours=2)).isoformat())
            for i in range(50)]})

    # Germany: two titles in German and English; the UK: the English one only.
    terms = [term("Hardware Engineer"), term("Hardwareentwickler", "de")]
    assert len(adzuna.plan_searches(terms, "DE")) == 2
    assert len(adzuna.plan_searches(terms, "GB")) == 1
    query = JobQuery(["DE", "GB"], [], terms, 24, NOW)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(adzuna, "share_of_month", lambda source, limits, **kw: Limits(
            per_search=9, per_day=240, per_month=2400))
        list(adzuna.AdzunaSource().search(query, context(handler, "adzuna")))
    assert asked.count("de") == 6 and asked.count("gb") == 3  # 2:1, not 4:5


def test_adzuna_may_use_up_to_100_requests_when_the_month_allows():
    from jobcu.sources.budget import share_of_month

    limits = share_of_month("adzuna", adzuna.LIMITS, most=adzuna.MOST_PER_SEARCH)
    assert limits.per_search == 100  # nothing used yet this month in this fictional database


def test_adzuna_passes_place_and_distance():
    seen = {}

    def handler(request):
        seen.update(request.url.params)
        return httpx.Response(200, json={"results": []})

    place = Place(name="Munich", local_name="München", country="DE", kind="city", radius_km=50)
    query = JobQuery(["DE"], [place], [term("Hardwareentwickler", "de")], 24, NOW)
    list(adzuna.AdzunaSource().search(query, context(handler, "adzuna")))
    assert seen["where"] == "München" and seen["distance"] == "50"


def test_one_failing_adzuna_search_leaves_the_others_running():
    fresh = (NOW - timedelta(hours=2)).isoformat()
    asked = []

    def handler(request):
        params = dict(request.url.params)
        asked.append(params.get("title_only") or params.get("what_phrase"))
        if params.get("title_only") == "Hardware Engineer":
            return httpx.Response(503, json={})  # what Adzuna answered on 2026-09-23
        return httpx.Response(200, json={"results": [adzuna_item(str(len(asked)), fresh)]})

    ctx = context(handler, "adzuna")
    query = JobQuery(["DE"], [], [term("Hardware Engineer"), term("Hardwareentwickler", "de"),
                                  term("power electronics", kind="field_or_skill")], 24, NOW)
    jobs = list(adzuna.AdzunaSource().search(query, ctx))
    # The failing one is retried politely first, then the others are asked for as usual.
    assert list(dict.fromkeys(asked)) == ["Hardware Engineer", "Hardwareentwickler",
                                          "power electronics"]
    assert len(jobs) == 2 and ctx.report.status == "partial"
    assert "code 503" in ctx.report.message


def test_adzuna_gives_up_when_every_search_fails():
    ctx = context(lambda request: httpx.Response(503, json={}), "adzuna")
    terms = [term(f"Title {i}") for i in range(5)]
    with pytest.raises(SourceError, match="code 503"):
        list(adzuna.AdzunaSource().search(JobQuery(["DE"], [], terms, 24, NOW), ctx))


def test_adzuna_rejected_keys_fail_only_this_source():
    ctx = context(lambda request: httpx.Response(401, json={}), "adzuna")
    query = JobQuery(["GB"], [], [term("Hardware")], 24, NOW)
    with pytest.raises(SourceError, match="didn't accept"):
        list(adzuna.AdzunaSource().search(query, ctx))


# --- Reed -----------------------------------------------------------------------------


def test_reed_keeps_fresh_jobs_and_reads_full_ads_on_request():
    today = NOW.strftime("%d/%m/%Y")
    old = (NOW - timedelta(days=10)).strftime("%d/%m/%Y")

    def handler(request):
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"totalResults": 2, "results": [
                {"jobId": 1, "jobTitle": "Electronics Engineer", "employerName": "Acme",
                 "locationName": "Bristol", "date": today, "jobDescription": "Short",
                 "jobUrl": "https://www.reed.co.uk/jobs/1"},
                {"jobId": 2, "jobTitle": "Old job", "employerName": "Acme",
                 "locationName": "Bristol", "date": old, "jobDescription": "Short"},
            ]})
        return httpx.Response(200, json={
            "jobId": 1,
            "datePosted": today,
            "jobDescription": "<p>Full <b>ad</b></p><ul><li>PCB</li></ul>",
            "contractType": "Permanent", "fullTime": True, "partTime": False,
            "externalUrl": "https://careers.acme.example/1", "minimumSalary": 45000,
            "maximumSalary": 55000,
        })

    source = reed.ReedSource()
    ctx = context(handler, "reed")
    query = JobQuery(["GB"], [], [term("Electronics Engineer")], 24, NOW)
    jobs = list(source.search(query, ctx))
    assert [j.source_job_id for j in jobs] == ["1"]
    full = source.load_details(jobs[0], ctx)
    assert full.description_is_complete and "• PCB" in full.description
    assert full.job_types == ["full_time_permanent"]
    assert full.salary_text == "£45,000 – £55,000"
    assert full.employer_url == "https://careers.acme.example/1"


# --- Bundesagentur ----------------------------------------------------------------------


def test_bundesagentur_reads_country_types_and_first_publication_date():
    item = {
        "referenznummer": "10001-1", "stellenangebotsTitel": "Hardwareentwickler (m/w/d)",
        "firma": "Acme GmbH", "stellenangebotsart": "ARBEIT", "vertragsdauer": "BEFRISTET",
        "arbeitszeitVollzeit": True, "datumErsteVeroeffentlichung": NOW.date().isoformat(),
        "stellenlokationen": [{"adresse": {"ort": "Linz", "land": "ÖSTERREICH"},
                               "breite": 48.3, "laenge": 14.3}],
    }

    # Archived/saved evidence remains readable while automated source access is paused.
    job = bundesagentur.to_found_job(item)
    assert job.country == "AT" and job.job_types == ["fixed_term"]
    assert job.url.endswith("/jobdetail/10001-1")
    full = bundesagentur.to_found_job(item, {**item, "stellenangebotsBeschreibung": "Full ad text"})
    assert full.description == "Full ad text" and full.description_is_complete


def test_bundesagentur_names_a_state_given_only_as_a_code():
    # Search 9: cards showed "BADEN_WUERTTEMBERG" as the place.
    item = {"referenznummer": "10001-2", "stellenangebotsTitel": "Elektroniker (m/w/d)",
            "stellenlokationen": [{"adresse": {"region": "BADEN_WUERTTEMBERG",
                                               "land": "DEUTSCHLAND"}}]}
    assert bundesagentur.to_found_job(item).location_text == "Baden-Württemberg"
    assert bundesagentur.state_name("THUERINGEN") == "Thüringen"
    assert bundesagentur.state_name("UEBERREGIONAL") == "Ueberregional"
    assert bundesagentur.state_name(None) is None


def test_bundesagentur_terms_hold_prevents_requests_unless_accepted_even_when_called_directly():
    def unexpected(request):
        pytest.fail("A restricted source must not receive a request")
    ctx = context(unexpected, "bundesagentur")
    query = JobQuery(["DE"], [], [term("Hardwareentwickler", "de")], 24, NOW)
    source = bundesagentur.BundesagenturSource()
    assert source.unavailable_reason(None) is None  # an opt-in now: off until switched on
    with pytest.raises(SourceError, match="don't allow automated"):
        list(source.search(query, ctx))
    assert ctx.report.requests == 0


@pytest.mark.parametrize("redirect", [False, True])
def test_terms_held_agency_hosts_cannot_be_requested_directly_or_through_redirects(redirect):
    held = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
    seen = []
    def handler(request):
        seen.append(str(request.url))
        assert request.url.host != "rest.arbeitsagentur.de"
        return (httpx.Response(302, headers={"Location": held})
                if request.url.path == "/redirect" else httpx.Response(200, text="Allowed ad"))
    ctx = context(handler)
    try:
        with pytest.raises(SourceTermsDenied, match="don't allow automated"):
            ctx.http.get("https://jobs.example.test/redirect" if redirect else held)
        assert seen == (["https://jobs.example.test/redirect"] if redirect else [])
        assert ctx.http.get("https://jobs.example.test/allowed").status_code == 200
        assert terms_denial("https://arbeitsagentur.de.example.test/jobs") is None
    finally:
        ctx.http.close()


# --- Budgets and polite requests --------------------------------------------------------


def test_daily_request_limit_is_kept():
    budget = RequestBudget("adzuna", "Adzuna", Limits(per_day=2))
    budget.spend()
    budget.spend()
    with pytest.raises(BudgetExhausted, match="today"):
        budget.spend()
    # Another search on the same day is limited too.
    with pytest.raises(BudgetExhausted):
        RequestBudget("adzuna", "Adzuna", Limits(per_day=2)).spend()


def test_polite_client_waits_as_asked_and_remembers_answers():
    calls, sleeps = [], []
    now = [100.0]

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "7"})
        return httpx.Response(200, json={"ok": True})

    http = PoliteClient(min_intervals={}, sleep=sleep, clock=lambda: now[0],
                        transport=httpx.MockTransport(handler))
    assert http.get("https://example.test/a").json() == {"ok": True}
    assert sleeps[0] == 7.0  # waited as the site asked
    http.get("https://example.test/a")
    assert len(calls) == 2  # the second request came from memory


@pytest.mark.parametrize(("exists", "attempts"), [(False, 1), (True, 4)])
def test_a_host_that_doesn_t_exist_isn_t_tried_again(exists, attempts):
    # Search 11: seven addresses guessed for employers' job lists cost 15 seconds of retries each.
    calls = []

    def handler(request):
        calls.append(1)
        raise httpx.ConnectError("no address")

    def resolve(host):
        if not exists:
            raise socket.gaierror(socket.EAI_NONAME, "unknown host")
        return [("address",)]

    http = PoliteClient(min_intervals={}, sleep=lambda s: None, resolve=resolve,
                        transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.ConnectError):
        http.get("https://jobs.nowhere.test/")
    assert len(calls) == attempts  # a real network hiccup is still tried again


@pytest.mark.parametrize("error", [socket.gaierror(socket.EAI_AGAIN, "temporary lookup failure"),
                                  OSError("temporary resolver failure")])
def test_temporary_dns_failure_keeps_permitted_source_retryable(error):
    calls, lookups = [], []

    def handler(request):
        calls.append(1)
        if len(calls) <= 2:
            raise httpx.ConnectError("connection interrupted")
        return httpx.Response(200, json={"jobs": ["fictional vacancy"]})

    def resolve(host):
        lookups.append(host)
        if len(lookups) == 1:
            raise error
        return [("address",)]

    http = PoliteClient(min_intervals={}, sleep=lambda s: None, resolve=resolve,
                        transport=httpx.MockTransport(handler))
    try:
        assert http.get("https://example.test/jobs").json() == {"jobs": ["fictional vacancy"]}
    finally:
        http.close()
    assert len(calls) == 3 and len(lookups) == 2


@pytest.mark.parametrize("page", [
    "<html>Please complete the CAPTCHA</html>",
    # Amazon CloudFront's firewall, as Adzuna's pages answered (2026-09-23).
    "<H1>403 ERROR</H1> The request could not be satisfied. Request blocked.",
])
def test_bot_protection_is_never_worked_around(page):
    def handler(request):
        return httpx.Response(403, text=page)

    http = PoliteClient(min_intervals={}, sleep=lambda s: None,
                        transport=httpx.MockTransport(handler))
    with pytest.raises(Blocked):
        http.get("https://example.test/")


# --- Sharing a free monthly allowance -------------------------------------------------


def test_adzuna_budget_shares_what_is_left_of_the_month():
    from datetime import datetime

    from jobcu import db
    from jobcu.settings import Settings, save_settings
    from jobcu.sources.budget import Limits, share_of_month

    settings = Settings()
    settings.limits.searches_per_month = 24  # the owner's plan
    save_settings(settings)
    limits = Limits(per_day=240, per_month=2400)

    def on(day: str, used_this_month: int = 0, used_today: int = 0, done: int = 0,
           hours: int = 24) -> int:
        with db.connect() as conn:
            conn.execute("DELETE FROM source_requests")
            conn.execute("DELETE FROM searches")
            if used_this_month:
                conn.execute(
                    "INSERT INTO source_requests (day, source, count) VALUES (?, 'adzuna', ?)",
                    (day[:8] + "01", used_this_month - used_today),
                )
            if used_today:
                conn.execute(
                    "INSERT INTO source_requests (day, source, count) VALUES (?, 'adzuna', ?)",
                    (day, used_today),
                )
            conn.executemany(
                "INSERT INTO searches (started_at, status, form_json) VALUES (?, 'finished', ?)",
                [(day[:8] + "01T19:00:00.000Z", '{"posted_within_hours": 24}')] * done)
        when = datetime.fromisoformat(day + "T12:00:00+00:00")
        return share_of_month("adzuna", limits, hours=hours, most=100,
                              now=lambda: when).per_search

    # 2,400 requests over the 24 planned searches: 100 each, and three parts for 72 hours
    # (within today's own allowance of 240).
    assert on("2026-09-01") == 100
    assert on("2026-09-01", hours=72) == 240
    # Ten searches done with 1,400 used: the 1,000 left over the 14 still planned.
    assert on("2026-09-20", used_this_month=1400, done=10) == 71
    # Ahead of plan (22 done by the 20th): the rest must last the month, at least 25.
    assert on("2026-09-20", used_this_month=2200, done=22) == 25
    # Never more than today's own allowance has left.
    assert on("2026-09-20", used_this_month=1000, used_today=230) == 10
    assert on("2026-09-20", used_this_month=1000, used_today=240) == 0


def test_adzuna_salary_shows_the_currency_and_a_single_figure_once():
    item = {**adzuna_item("1", NOW.isoformat()), "salary_min": 75000, "salary_max": 75000,
            "salary_is_predicted": "0"}
    assert adzuna.to_found_job(item, "GB").salary_text == "£75,000"
    item = {**item, "salary_max": 90000.4}
    assert adzuna.to_found_job(item, "DE").salary_text == "€75,000 – €90,000"
    assert adzuna.to_found_job({**item, "salary_is_predicted": "1"}, "DE").salary_text is None


def test_the_share_follows_how_often_this_person_really_searches():
    from datetime import datetime, timedelta

    from jobcu import db
    from jobcu.sources.budget import Limits, searches_a_day, share_of_month

    now = datetime(2026, 9, 10, 12, tzinfo=UTC)
    limits = Limits(per_day=240, per_month=2400)
    # No searches yet, or one a day (the owner's use): the most a search may take.
    assert searches_a_day(now) == 1.0
    assert share_of_month("adzuna", limits, now=lambda: now).per_search == 60
    # Six a day for two weeks: the month's allowance is shared more thinly.
    with db.connect() as conn:
        for hours in range(0, 14 * 24, 4):
            conn.execute("INSERT INTO searches (started_at, status, form_json) "
                         "VALUES (?, 'finished', '{}')",
                         ((now - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),))
    assert searches_a_day(now) == 6.0
    assert share_of_month("adzuna", limits, now=lambda: now).per_search == 25


def test_a_planned_number_of_searches_a_month_shares_free_allowances_equally():
    from datetime import datetime, timedelta

    from jobcu import db
    from jobcu.settings import Settings, save_settings
    from jobcu.sources.budget import searches_a_day, share_until

    now = datetime(2026, 10, 18, 20, tzinfo=UTC)
    settings = Settings()
    settings.limits.searches_per_month = 24
    save_settings(settings)
    # The owner's plan wins over the habit; JSearch's 200 free credits from its renewal day
    # to the next: 8 for each of the 24 searches (8 left over for the last ones).
    assert searches_a_day(now) == 24 / (365.25 / 12)
    renews = now + timedelta(days=365.25 / 12)
    assert share_until(200, renews, fewest=2, most=40, now=lambda: now) == 8
    # 12 daily searches done since the renewal (behind the plan) with 69 credits used: the 131
    # left are divided over the 12 still planned, three parts for a 72-hour search.
    with db.connect() as conn:
        conn.executemany(
            "INSERT INTO searches (started_at, status, form_json) VALUES (?, 'finished', ?)",
            [((now - timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
              '{"posted_within_hours": 24}') for d in range(1, 13)])
    later_renewal = now + timedelta(days=12)
    assert share_until(131, later_renewal, fewest=2, most=40, now=lambda: now) == 10
    assert share_until(131, later_renewal, hours=72, fewest=2, most=40, now=lambda: now) == 32
    # Ahead of the plan, the planned pace over the days left decides, so the credits last.
    with db.connect() as conn:
        conn.executemany(
            "INSERT INTO searches (started_at, status, form_json) VALUES (?, 'finished', ?)",
            [((now - timedelta(days=d, hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
              '{"posted_within_hours": 24}') for d in range(1, 9)])
    assert share_until(131, later_renewal, fewest=2, most=40, now=lambda: now) == 13


def test_restrictive_terms_hold_until_the_person_accepts_them_for_that_source():
    ba = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
    assert terms_denial(ba) and terms_denial(ba, frozenset({"jsearch"}))
    assert terms_denial(ba, frozenset({"bundesagentur"})) is None
    assert terms_denial("https://jobs.sap.com/x", frozenset({"bundesagentur"}))  # never accepted

    def answer(request):
        return httpx.Response(200, json={"ergebnisliste": []})

    refused = PoliteClient(transport=httpx.MockTransport(answer), min_intervals={})
    with pytest.raises(SourceTermsDenied):
        refused.get(ba)
    accepted = PoliteClient(transport=httpx.MockTransport(answer), min_intervals={},
                            accepted_terms=frozenset({"bundesagentur"}))
    assert accepted.get(ba).status_code == 200
