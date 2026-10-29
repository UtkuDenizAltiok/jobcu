"""Fictional API contracts only: no provider, job-site or AI traffic."""

import dataclasses
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest

from jobcu import applications, db, jobstore, pipeline, pool
from jobcu.countries import COUNTRIES
from jobcu.dedupe import JobGroup
from jobcu.keystore import KeyStore
from jobcu.keywords import SearchTerm
from jobcu.settings import Settings, save_settings
from jobcu.sources import disabled_sources, jsearch
from jobcu.sources.base import (
    FoundJob,
    JobQuery,
    JobSource,
    SourceContext,
    SourceError,
    SourceReport,
)
from jobcu.sources.budget import BudgetExhausted, Limits
from jobcu.sources.http import PoliteClient, RequestStopped

NOW = datetime.now(UTC)
FULL = (
    "Fictional vacancy: develop analogue circuits, document the design and test prototypes. "
    "Experience with schematic design and laboratory measurements required. Full-time role."
)
MAIN = "https://board.example.test/jobs/fictional-1"
EMPLOYER = "https://careers.fictional.example.test/jobs/fictional-1"


def term(text="Hardware Engineer", language="en", kind="job_title"):
    return SearchTerm(text=text, language=language, kind=kind)


def query(countries=None, terms=None, hours=24):
    return JobQuery(countries or ["DE"], [], terms or [term()], hours, NOW)


def receipt(remaining=190):
    return {
        "status": "OK",
        "data": {
            "api_id": "jsearch",
            "plan": {"is_free": True},
            "status": "active",
            "quotas": [
                {
                    "name": "Requests",
                    "limit": 200,
                    "used": 200 - remaining,
                    "remaining": remaining,
                    "reset_at": (NOW + timedelta(days=20)).isoformat(),
                }
            ],
        },
    }


def item(identity="fictional-1", **changes):
    return {
        "job_id": identity,
        "job_title": "Hardware Engineer",
        "employer_name": "Fictional Instruments",
        "job_apply_link": MAIN,
        "job_country": "DE",
        "job_city": "Berlin",
        "job_description": FULL,
        "job_posted_at_datetime_utc": (NOW - timedelta(hours=1)).isoformat(),
        **changes,
    }


def page(jobs=(), cursor=None):
    return httpx.Response(
        200, json={"status": "OK", "data": {"jobs": list(jobs), "cursor": cursor}}
    )


@pytest.fixture
def setup(monkeypatch):
    save_settings(Settings(source_opt_ins=["jsearch"]))
    monkeypatch.setattr(
        jsearch, "share_of_month", lambda *a, **k: Limits(per_search=12, per_month=200)
    )
    monkeypatch.setattr(jsearch, "share_until", lambda *a, **k: 12)
    clients = []

    def create(handler=None, account=None):
        requests = []
        keys = KeyStore()
        keys.set(jsearch.KEY_API_KEY, "fictional-key-1234567890")

        def respond(request):
            requests.append(request)
            assert request.url.host == "api.openwebninja.com"
            assert request.headers["x-api-key"] == "fictional-key-1234567890"
            assert request.method == "GET"
            if request.url.path == "/usage":
                assert dict(request.url.params) == {"api_id": "jsearch"}
                return httpx.Response(200, json=receipt() if account is None else account)
            return handler(request) if handler else page()

        http = PoliteClient(
            min_intervals={"api.openwebninja.com": 0},
            sleep=lambda _: None,
            transport=httpx.MockTransport(respond),
        )
        clients.append(http)
        ctx = SourceContext(
            http, keys, SourceReport("jsearch", "JSearch"), lambda: False, lambda _: None
        )
        return jsearch.JSearchSource(), ctx, requests

    yield create
    for http in clients:
        http.close()


def reserved():
    with db.connect() as conn:
        return conn.execute(
            "SELECT COALESCE(SUM(count), 0) FROM source_requests WHERE source = 'jsearch'"
        ).fetchone()[0]


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse", "Primary Teacher"])
def test_existing_terms_and_all_countries_are_supported_without_profile_upload(title):
    plans = jsearch.plan_queries(query(list(COUNTRIES), [term(title)]))
    assert {p.country for p in plans} == set(COUNTRIES)
    assert [p.country for p in plans[:7]] == list(jsearch.PRIORITY)
    assert all(p.text == f"{title} in {COUNTRIES[p.country].name}" for p in plans)
    assert all(p.language == "en" for p in plans)


def test_languages_and_countries_are_interleaved_before_pagination():
    plans = jsearch.plan_queries(
        query(
            ["GB", "DE"],
            [
                term("Circuit Design"),
                term("Hardwareentwickler", "de"),
                term("Circuit Design"),
                term("Power Electronics"),
            ],
        )
    )
    assert [(p.country, p.language) for p in plans[:4]] == [
        ("DE", "de"),
        ("GB", "en"),
        ("DE", "en"),
        ("GB", "en"),
    ]
    assert len(plans) == 5
    assert jsearch.plan_queries(query(["GB", "DE"]), offset=1)[0].country == "GB"


def test_own_language_and_broad_titles_come_first_and_reworded_ones_once():
    plans = jsearch.plan_queries(query(["DE"], [
        term("Power Electronics Engineer"),
        term("Leistungselektronik Ingenieur", "de"),
        term("Ingenieur Leistungselektronik", "de"),  # the same words: one query
        term("Hardwareentwickler", "de"),
        term("Leistungselektronik", "de", kind="field_or_skill"),
    ]))
    assert [(p.language, p.text) for p in plans] == [
        ("de", "Hardwareentwickler in Germany"),
        ("de", "Leistungselektronik Ingenieur in Germany"),
        ("de", "Leistungselektronik in Germany"),
        ("en", "Power Electronics Engineer in Germany"),
    ]


def test_queries_that_came_back_empty_twice_wait_and_productive_ones_go_first():
    plans = jsearch.plan_queries(query(["DE", "GB"], [
        term("Hardwareentwickler", "de"), term("Elektronikentwickler", "de"),
        term("Hardware Engineer"), term("Electronics Engineer")]))
    by_text = {p.text: p for p in plans}
    for _ in range(2):
        jsearch.remember_yield(by_text["Hardwareentwickler in Germany"], 0)
    jsearch.remember_yield(by_text["Electronics Engineer in United Kingdom"], 7)
    jsearch.remember_yield(by_text["Hardware Engineer in Germany"], 0)  # once: still worth one
    ordered = [(p.country, p.text) for p in jsearch.by_yield(plans)]
    assert ordered[:2] == [("DE", "Elektronikentwickler in Germany"),
                           ("GB", "Electronics Engineer in United Kingdom")]
    assert ordered[-1] == ("DE", "Hardwareentwickler in Germany")
    assert [c for c, _ in ordered] == ["DE", "GB", "DE", "GB", "DE", "DE"]  # turns kept


def test_a_search_remembers_what_each_query_s_first_page_brought(setup):
    def respond(request):
        if request.url.params.get("cursor"):
            return page([item("second-page")])
        empty = "Circuit" in request.url.params["query"]
        return page([] if empty else [item()], None if empty else "next")

    source, ctx, _ = setup(respond)
    two = query(terms=[term("Hardware Engineer"), term("Circuit Designer")])
    list(source.search(two, ctx))
    remembered = {p.text: jsearch.preparation.read(
        jsearch.YIELD_KIND, jsearch._yield_key(p), jsearch.QueryYield)
        for p in jsearch.plan_queries(two)}
    assert remembered["Hardware Engineer in Germany"].jobs == 1  # the first page only
    assert remembered["Circuit Designer in Germany"].empty_in_a_row == 1


def test_disabled_or_unconfigured_sources_never_make_account_calls(setup):
    source, ctx, requests = setup()
    save_settings(Settings())
    assert "jsearch" in disabled_sources(Settings())
    with pytest.raises(SourceError, match="switched off"):
        list(source.search(query(), ctx))
    save_settings(Settings(source_opt_ins=["jsearch"], sources_disabled=["jsearch"]))
    with pytest.raises(SourceError, match="switched off"):
        list(source.search(query(), ctx))
    save_settings(Settings(source_opt_ins=["jsearch"]))
    ctx.keys.delete(jsearch.KEY_API_KEY)
    with pytest.raises(SourceError, match="Free key"):
        list(source.search(query(), ctx))
    assert requests == [] and reserved() == 0


def test_no_usable_terms_does_not_consume_an_account_check(setup):
    source, ctx, requests = setup()
    assert list(source.search(JobQuery(["DE"], [], [], 24, NOW), ctx)) == []
    assert not requests


@pytest.mark.parametrize(
    "broken",
    [
        "paid",
        "wrong_service",
        "inactive",
        "quotas_missing",
        "duplicate_quota",
        "unknown_limit",
        "boolean_count",
        "inconsistent",
        "expired",
        "missing_period",
    ],
)
def test_incomplete_or_paid_account_stops_before_vacancies_and_cannot_be_bypassed(setup, broken):
    account = receipt()
    data, quota = account["data"], account["data"]["quotas"][0]
    if broken == "paid":
        data["plan"]["is_free"] = False
    elif broken == "wrong_service":
        data["api_id"] = "another-service"
    elif broken == "inactive":
        data["status"] = "past_due"
    elif broken == "quotas_missing":
        data.pop("quotas")
    elif broken == "duplicate_quota":
        data["quotas"].append(dict(quota))
    elif broken == "unknown_limit":
        quota.update(limit=1000, used=810)
    elif broken == "boolean_count":
        quota["used"] = True
    elif broken == "inconsistent":
        quota["remaining"] -= 1
    elif broken == "expired":
        quota["reset_at"] = (NOW - timedelta(days=1)).isoformat()
    else:
        quota.pop("reset_at")
    source, ctx, requests = setup(account=account)
    with pytest.raises(SourceError):
        list(source.search(query(), ctx))
    with pytest.raises(SourceError, match="earlier"):
        source.load_details(jsearch.to_found_job(item()), ctx)
    assert len(requests) == 1 and ctx.report.requests == reserved() == 0  # checks are free


def test_empty_provider_allowance_is_not_replaced_by_local_allowance(setup):
    source, ctx, requests = setup(account=receipt(0))
    assert list(source.search(query(), ctx)) == []
    assert ctx.report.status == "partial" and "allowance" in ctx.report.message
    assert len(requests) == 1


def test_monthly_exhaustion_does_not_send_account_or_details_requests(setup):
    source, ctx, requests = setup()
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO source_requests VALUES (?, 'jsearch', 200)", (NOW.strftime("%Y-%m-%d"),)
        )
    list(source.search(query(), ctx))
    with pytest.raises(BudgetExhausted):
        source.load_details(jsearch.to_found_job(item()), ctx)
    assert requests == [] and reserved() == 200


@pytest.mark.parametrize("code", [301, 401, 402, 403, 429, 500, 503])
def test_service_errors_are_specific_single_attempts_and_never_follow_redirects(setup, code):
    source, ctx, requests = setup(
        lambda r: httpx.Response(
            code, headers={"location": "https://unrelated.example.test/secret"}, json={}
        )
    )
    with pytest.raises(SourceError):
        list(source.search(query(), ctx))
    with pytest.raises(SourceError, match="earlier"):
        source.load_details(jsearch.to_found_job(item()), ctx)
    assert [r.url.path for r in requests] == ["/usage", "/jsearch/search-v2"]
    assert ctx.report.requests == reserved() == 1


@pytest.mark.parametrize("failure", ["read", "connect", "json", "shape"])
def test_ambiguous_failures_are_not_repeated_or_spent_again(setup, failure):
    def fail(request):
        if failure in {"read", "connect"}:
            raise (httpx.ReadError if failure == "read" else httpx.ConnectError)(
                "Fictional connection problem", request=request
            )
        return (
            httpx.Response(200, text="invalid JSON")
            if failure == "json"
            else (httpx.Response(200, json={"status": "OK", "data": []}))
        )

    source, ctx, requests = setup(fail)
    two_queries = query(terms=[term("Hardware Engineer"), term("Circuit Designer")])
    with pytest.raises(SourceError):
        list(source.search(two_queries, ctx))
    # A broken connection skips its own query; only a second one in a row stops the source.
    searches = 2 if failure in {"read", "connect"} else 1
    assert len(requests) == 1 + searches and ctx.report.requests == reserved() == searches
    assert len({str(r.url) for r in requests}) == len(requests)  # nothing sent twice


def test_after_one_broken_connection_the_other_queries_still_bring_their_jobs(setup):
    def respond(request):
        if "Hardware" in request.url.params["query"]:
            raise httpx.ReadTimeout("Fictional stall", request=request)
        return page([item(job_title="Circuit Designer")])

    source, ctx, requests = setup(respond)
    jobs = list(source.search(
        query(terms=[term("Hardware Engineer"), term("Circuit Designer")]), ctx))
    assert [job.title for job in jobs] == ["Circuit Designer"]
    assert ctx.report.status == "partial" and "interrupted" in ctx.report.message
    assert [r.url.path for r in requests] == ["/usage", "/jsearch/search-v2", "/jsearch/search-v2"]


@pytest.mark.parametrize(
    "hours,window", [(6, "3days"), (24, "3days"), (72, "3days"), (168, "week")]
)
def test_current_cursor_contract_and_conservative_date_window(setup, hours, window):
    def respond(request):
        params = dict(request.url.params)
        assert params["num_pages"] == "1" and params["date_posted"] == window
        assert set(params) <= {"query", "country", "language", "num_pages", "date_posted", "cursor"}
        assert params["country"] == "de" and params["language"] == "en"
        if "cursor" not in params:
            return page([item()], "next-fictional")  # short page is not end-of-results
        assert params["cursor"] == "next-fictional"
        return page([item("fictional-2")])

    source, ctx, requests = setup(respond)
    assert len(list(source.search(query(hours=hours), ctx))) == 2
    assert len(requests) == 3 and reserved() == 2


def test_repeated_cursor_is_stopped_and_received_jobs_are_kept(setup):
    source, ctx, requests = setup(lambda _: page([item()], "same-cursor"))
    assert len(list(source.search(query(), ctx))) == 1
    assert len(requests) == 3 and ctx.report.status == "partial"


def test_infinite_pagination_is_bounded_and_later_countries_get_a_turn(setup):
    count = 0

    def respond(request):
        nonlocal count
        count += 1
        return page([item(str(count))], f"next-{count}")

    source, ctx, requests = setup(respond)
    list(source.search(query(["DE", "IE", "GB"]), ctx))
    assert [r.url.params["country"] for r in requests[1:4]] == ["de", "ie", "gb"]
    assert len(requests) == 10  # account + 3 pages each; two units reserved for full ads
    assert ctx.report.status == "partial"


def test_credits_are_spread_until_the_account_renews_not_to_the_month_s_end(setup, monkeypatch):
    from jobcu.sources import budget

    # The calendar month would allow 40 now; 60 credits must last the 20 days to renewal.
    monkeypatch.setattr(jsearch, "share_of_month", lambda *a, **k: Limits(per_search=40))
    monkeypatch.setattr(jsearch, "share_until", budget.share_until)
    source, ctx, requests = setup(lambda r: page([item()], "next"), account=receipt(60))
    list(source.search(query(["DE", "IE", "GB"]), ctx))
    assert len(requests) == 4  # the free account check + 60 / 20 days = 3 at one search a day
    assert budget.share_until(60, NOW + timedelta(days=20), fewest=2, most=40,
                              now=lambda: NOW) == 3
    assert budget.share_until(500, NOW + timedelta(hours=5), fewest=2, most=40,
                              now=lambda: NOW) == 40


def test_query_allowance_is_shared_with_selected_details(setup, monkeypatch):
    monkeypatch.setattr(
        jsearch, "share_of_month", lambda *a, **k: Limits(per_search=6, per_month=200)
    )

    def respond(request):
        if request.url.path.endswith("job-details"):
            return httpx.Response(200, json={"status": "OK", "data": [item()]})
        return page([item(job_description="Summary...")], "next")

    source, ctx, requests = setup(respond)
    jobs = list(source.search(query(terms=[term(), term("Nurse"), term("Teacher")]), ctx))
    source.load_details(jobs[0], ctx)
    source.load_details(jobs[0], ctx)
    with pytest.raises(BudgetExhausted):
        source.load_details(jobs[0], ctx)
    assert len(requests) == 7 and ctx.report.requests == reserved() == 6  # + the free check


def test_stop_never_reserves_or_sends_an_extra_request(setup):
    source, ctx, requests = setup()
    ctx.should_stop = lambda: True
    with pytest.raises(RequestStopped):
        list(source.search(query(), ctx))
    assert not requests and reserved() == 0


def test_source_failure_preserves_completed_pages_and_does_not_stop_other_feeds(setup, monkeypatch):
    def respond(request):
        return httpx.Response(503) if request.url.params.get("cursor") else page([item()], "next")

    source, ctx, requests = setup(respond)

    class Other(JobSource):
        id, name, kind = "fictional", "Fictional feed", "employer"

        def search(self, query, context):
            yield FoundJob(self.id, "other", EMPLOYER, "Primary Teacher")

    monkeypatch.setattr(pipeline, "all_sources", lambda: [source, Other()])
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    result = pipeline.collect(query(), ctx.http, ctx.keys, [], run)
    assert {j.source for j in result.jobs} == {"jsearch", "fictional"}
    assert [(r.status, r.jobs_found) for r in result.reports] == [("failed", 1), ("ok", 1)]
    assert len(requests) == 3


def test_older_copy_and_lookup_country_are_evidence_not_new_publication_or_workplace(setup):
    source, ctx, _ = setup(
        lambda _: page(
            [
                item(
                    job_posted_at_datetime_utc=(NOW - timedelta(days=10)).isoformat(),
                    job_country=None,
                )
            ]
        )
    )
    (job,) = list(source.search(query(), ctx))
    assert job.older_copy and job.country is None
    assert job.source_context == {"country": "de", "language": "en"}
    assert pipeline.make_groups(pipeline.Collected([job], [], {"jsearch": source})) == []


@pytest.mark.parametrize(
    "stamp,precision",
    [
        (None, "unknown"),
        ("2026-10-15", "day"),
        ("2026-10-15T00:00:00Z", "day"),
        ("2026-10-15T09:01:00Z", "exact"),
    ],
)
def test_nullable_and_day_dates_are_not_claimed_as_exact_freshness(stamp, precision):
    job = jsearch.to_found_job(item(job_posted_at_datetime_utc=stamp, job_posted_at="3 hours ago"))
    assert job.date_precision == precision
    if stamp is None:
        assert job.posted_at is None


def test_fulltime_coordinates_ai_estimates_and_missing_fields_are_not_invented():
    job = jsearch.to_found_job(
        item(
            job_latitude=52.5,
            job_longitude=13.4,
            job_employment_types=["FULLTIME"],
            job_is_remote=False,
            job_country=None,
            job_description=None,
            job_min_salary=90000,
            job_visa_sponsorship=True,
            job_required_skills=["invented"],
            job_posted_at_timestamp=True,
            job_posted_at_datetime_utc=None,
        )
    )
    assert job.latitude is job.longitude is job.country is job.work_mode is None
    assert job.job_types == ["full_time_permanent", "fixed_term"]
    assert not job.description_is_complete and not job.description and job.posted_at is None
    assert job.salary_text is None and job.closes_at is None


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "https://localhost/job",
        "http://127.1/job",
        "http://127.0.0.1/job",
        "http://10.0.0.1/job",
        "http://0x7f.0.0.1/job",
        "https://host.internal./job",
        "https://user:pass@example.test/job",
        "https://[invalid",
        "https://example.test:999/job",
        "https://example.test/with space",
        "https://a.test\\b/job",
    ],
)
def test_unsafe_supplied_links_are_not_offered(url):
    assert jsearch.to_found_job(item(job_apply_link=url)) is None


def test_application_options_keep_supplied_links_and_require_support_for_direct_claims():
    job = jsearch.to_found_job(
        item(
            job_apply_is_direct=True,  # a board flag alone is not proof
            employer_website="https://fictional.example.test",
            apply_options=[
                {"publisher": "Fictional Instruments", "apply_link": EMPLOYER, "is_direct": True},
                {"publisher": "Other board", "apply_link": MAIN, "is_direct": False},
                {"publisher": "Bad", "apply_link": "http://127.0.0.1/x", "is_direct": True},
            ],
        )
    )
    assert job.employer_url == EMPLOYER
    main, others = applications.links(JobGroup([job]), {"jsearch": "JSearch"})
    assert main == {"source": "Employer's site", "url": EMPLOYER}
    assert [o["url"] for o in others] == [MAIN]
    generic = jsearch.to_found_job(
        item(
            job_apply_link="https://fictional.example.test/careers",
            employer_website="https://fictional.example.test",
            job_apply_is_direct=True,
        )
    )
    assert generic.employer_url is None


def test_blocked_primary_and_reported_option_leave_a_usable_alternative():
    alternate = "https://other.example.test/jobs/fictional-1"
    job = jsearch.to_found_job(
        item(
            job_apply_link="https://cv-library.co.uk/job/fictional-1",
            apply_options=[
                {"publisher": "One", "apply_link": MAIN},
                {"publisher": "Two", "apply_link": alternate},
            ],
        )
    )
    group = JobGroup([job])
    assert applications.links(group, {}, {MAIN})[0]["url"] == alternate
    assert applications.exclusion_key(group, {MAIN}) is None
    assert applications.exclusion_key(group, {MAIN, alternate}) == "application_route"


def test_details_use_saved_locale_and_preserve_earlier_dates_text_and_options(setup):
    def respond(request):
        assert dict(request.url.params) == {
            "job_id": "fictional-1",
            "country": "de",
            "language": "en",
        }
        return httpx.Response(
            200,
            json={
                "status": "OK",
                "data": [
                    item(
                        job_description="Newer summary...",
                        job_country=None,
                        job_posted_at_datetime_utc=NOW.isoformat(),
                    )
                ],
            },
        )

    source, ctx, requests = setup(respond)
    original = jsearch.to_found_job(item(job_country=None))
    original.source_context = {"country": "de", "language": "en"}
    original.application_options = [{"source": "Original", "url": EMPLOYER}]
    full = source.load_details(original, ctx)
    assert full.description == FULL and full.description_is_complete
    assert full.posted_at == original.posted_at and full.country is None
    assert full.application_options == original.application_options
    assert original.description == FULL and len(requests) == 2


def test_unmatched_details_stop_source_and_preserve_original(setup):
    source, ctx, requests = setup(
        lambda _: httpx.Response(200, json={"status": "OK", "data": [item("different-id")]})
    )
    original = jsearch.to_found_job(item(job_description="Original summary..."))
    with pytest.raises(SourceError, match="did not match"):
        source.load_details(original, ctx)
    assert original.description == "Original summary..." and len(requests) == 2


def test_shorter_unmarked_detail_text_cannot_erase_richer_complete_evidence(setup):
    richer = FULL + " Fluent fictional language and four years of experience are required."
    source, ctx, _ = setup(lambda _: httpx.Response(
        200, json={"status": "OK", "data": [item(job_description="Develop circuits.")]}
    ))
    original = jsearch.to_found_job(item(job_description=richer, job_country=None))
    original.source_context = {"country": "de", "language": "en"}
    full = source.load_details(original, ctx)
    assert full.description == richer and full.description_is_complete
    assert full.country == "DE" and original.country is None


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse", "Primary Teacher"])
@pytest.mark.parametrize("missing", ["country", "town"])
def test_complete_list_text_still_recovers_missing_workplace_metadata(setup, title, missing):
    source, ctx, requests = setup(lambda _: httpx.Response(
        200, json={"status": "OK", "data": [item(job_title=title)]}
    ))
    changes = {"job_country": None} if missing == "country" else {"job_city": None}
    job = jsearch.to_found_job(item(job_title=title, **changes))
    job.source_context = {"country": "de", "language": "en"}
    groups = [JobGroup([job])]
    collected = pipeline.Collected([job], [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    recovered = groups[0].copies[0]
    assert recovered.country == "DE" and recovered.location_text == "Berlin"
    assert recovered.description == FULL and len(requests) == 2
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert len(requests) == 2


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse", "Primary Teacher"])
@pytest.mark.parametrize("other_complete", [False, True])
def test_complete_text_cannot_skip_a_missing_publication_date(setup, title, other_complete):
    from jobcu.filters import apply_rules

    old = NOW - timedelta(days=8)
    source, ctx, requests = setup(lambda _: httpx.Response(200, json={"status": "OK",
        "data": [item(job_title=title, job_posted_at_datetime_utc=old.isoformat())]}))
    job = jsearch.to_found_job(item(job_title=title, job_posted_at_datetime_utc=None))
    copies = [job]
    if other_complete:
        copies.append(dataclasses.replace(job, source="other", source_job_id="other-id",
            url="https://other.example.test/vacancy", posted_at=NOW - timedelta(hours=1)))
    groups = [JobGroup(copies)]
    collected = pipeline.Collected(copies, [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].posted_at == old and len(requests) == 2
    assert groups[0].best_description_copy.description == FULL
    outcome = apply_rules(groups, [None], started_at=NOW, posted_within_hours=24,
        job_types=["full_time"], exclude_remote=False, countries=["DE"])
    assert outcome.kept == [] and outcome.left_out == {"too_old": 1}
    # A repeated list missing the same field uses the successful detail receipt.
    groups = [JobGroup([job])]
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].posted_at == old and len(requests) == 2


def test_complete_known_date_does_not_buy_details_for_an_unsupported_deadline(setup):
    source, ctx, requests = setup()
    job = jsearch.to_found_job(item())
    assert job.posted_at is not None and job.closes_at is None
    collected = pipeline.Collected([job], [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads([JobGroup([job])], [0], collected, ctx.http, ctx.keys, run)
    assert not requests and reserved() == 0


@pytest.mark.parametrize("reply", ["unknown", "failure", "exhausted"])
def test_missing_date_recovery_preserves_unknown_and_respects_source_failures(setup, reply):
    def handle(_):
        if reply == "failure":
            return httpx.Response(503, json={"status": "ERROR"})
        return httpx.Response(200, json={"status": "OK",
            "data": [item(job_posted_at_datetime_utc=None)]})

    source, ctx, requests = setup(handle, account=receipt(remaining=0 if reply == "exhausted"
                                                        else 190))
    job = jsearch.to_found_job(item(job_posted_at_datetime_utc=None))
    groups = [JobGroup([job])]
    collected = pipeline.Collected([job], [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].posted_at is None
    assert groups[0].best_description_copy.description == FULL
    assert reserved() <= 2
    if reply == "exhausted":
        assert len(requests) == 1
    elif reply == "unknown":
        pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
        assert len(requests) == 2


def test_cached_country_fills_the_same_workplace_without_replacing_fresh_complete_text(setup):
    source, ctx, requests = setup()
    known = jsearch.to_found_job(item())
    jobstore.remember_ad(known)
    fresh = jsearch.to_found_job(item(job_country=None, job_description=FULL + " New benefits."))
    fresh.source_context = {"country": "de", "language": "en"}
    groups = [JobGroup([fresh])]
    collected = pipeline.Collected([fresh], [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].copies[0].country == "DE" and not requests
    assert groups[0].copies[0].description == fresh.description


def test_cached_country_does_not_fill_a_changed_workplace_without_a_detail_read(setup):
    source, ctx, requests = setup(lambda _: httpx.Response(
        200, json={"status": "OK", "data": [item(job_country="IE", job_city="Cork")]}
    ))
    jobstore.remember_ad(jsearch.to_found_job(item()))
    fresh = jsearch.to_found_job(item(job_country=None, job_city="Cork"))
    fresh.source_context = {"country": "ie", "language": "en"}
    groups = [JobGroup([fresh])]
    collected = pipeline.Collected([fresh], [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].copies[0].country == "IE" and len(requests) == 2
    assert groups[0].copies[0].location_text == "Cork"


def test_missing_lookup_or_multi_id_cannot_consume_credits(setup):
    source, ctx, requests = setup()
    for job in [
        jsearch.to_found_job(item(job_country=None)),
        dataclasses.replace(jsearch.to_found_job(item()), source_job_id="one,two"),
    ]:
        with pytest.raises(SourceError):
            source.load_details(job, ctx)
    assert not requests


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse", "Primary Teacher"])
def test_same_vacancy_gets_one_group_and_supplied_full_text_needs_no_detail_call(setup, title):
    source, ctx, requests = setup()
    j = jsearch.to_found_job(item(job_title=title))
    board = dataclasses.replace(
        j,
        source="other",
        source_job_id="other-id",
        url="https://other-board.example.test/vacancies/other-id",
        description="Short summary",
        description_is_complete=False,
    )
    collected = pipeline.Collected([j, board], [ctx.report], {"jsearch": source})
    groups = pipeline.make_groups(collected)
    assert len(groups) == 1 and len(groups[0].copies) == 2
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].best_description_copy.description == FULL and not requests


def test_saved_pool_retains_locale_alternatives_scores_and_legacy_records():
    job = jsearch.to_found_job(item())
    job.source_context = {"country": "de", "language": "en"}
    job.application_options = [{"source": "Alternative", "url": EMPLOYER}]
    with db.connect() as conn:
        conn.execute("INSERT INTO searches (id, status, form_json) VALUES (1, 'finished', '{}')")
    saved = pool.Pool(1, [pool.PoolJob(JobGroup([job]), scored={"score": 71})], {})
    pool.save(saved)
    recovered = pool.load(1).jobs[0]
    assert recovered.scored == {"score": 71} and recovered.group.copies[0] == job
    jobstore.remember_ad(job)
    assert jobstore.remembered_ad(
        dataclasses.replace(job, description="Summary")
    ).application_options == (job.application_options)
    with db.connect() as conn:
        raw = json.loads(conn.execute("SELECT pool_json FROM search_pool").fetchone()[0])
        old = raw["jobs"][0]["group"]["copies"][0]
        old.pop("source_context")
        old.pop("application_options")
        conn.execute("UPDATE search_pool SET pool_json = ?", (json.dumps(raw),))
    legacy = pool.load(1).jobs[0]
    assert legacy.scored == {"score": 71}
    assert legacy.group.copies[0].source_context == {}


def test_account_button_checks_only_usage_and_does_not_enable_source(setup, monkeypatch):
    _, ctx, requests = setup()
    save_settings(Settings())
    monkeypatch.setattr(jsearch, "PoliteClient", lambda: ctx.http)
    result = jsearch.check_keys(ctx.keys)
    assert result.ok and "No job query" in result.message
    assert [r.url.path for r in requests] == ["/usage"] and reserved() == 0
    assert "jsearch" in disabled_sources(Settings())


def test_short_ad_reuses_saved_full_text_before_account_or_detail_calls(setup):
    source, ctx, requests = setup()
    complete = jsearch.to_found_job(item())
    jobstore.remember_ad(complete)
    short = dataclasses.replace(complete, description="Summary...", description_is_complete=False)
    groups = [JobGroup([short])]
    collected = pipeline.Collected([short], [ctx.report], {"jsearch": source})
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=lambda *a: None)
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].best_description_copy.description == FULL
    assert not requests and reserved() == 0


@pytest.mark.parametrize("title", ["Hardware Engineer", "Registered Nurse", "Primary Teacher"])
@pytest.mark.parametrize("location_answer", ["no", "unknown"])
def test_new_source_never_bypasses_failed_or_pending_location_gate(
    setup, monkeypatch, title, location_answer
):
    from test_search import PROFILE

    from jobcu import filters, search, travel
    from jobcu.location import Anchor, Condition, LocationPlan
    from jobcu.settings import SearchForm

    source, ctx, requests = setup()
    job = jsearch.to_found_job(item(job_title=title))
    condition = Condition(
        text="Within 50 minutes of a qualifying city",
        understood_as="…",
        kind="near",
        status="estimate",
        max_km=40,
        anchor=Anchor(min_share_of_country=0.003),
    )
    plan = LocationPlan(
        text="Fictional condition",
        understood_as="…",
        countries=["DE"],
        places=[],
        conditions=[condition],
        not_checked_yet=[],
        outside_supported_area=[],
        broad=False,
    )
    monkeypatch.setattr(travel, "answer", lambda *a: location_answer)
    monkeypatch.setattr(travel, "workplace_conflict", lambda *a: False)
    assert filters.condition_fit(condition, JobGroup([job])) == location_answer
    scored = []

    def score(client, profile, location, groups, indexes, **kwargs):
        if location_answer == "no":
            pytest.fail("Location-ineligible vacancies must not be scored")
        scored.extend(indexes)  # an unknown one: its own fit, shown while it waits
        return {i: {"score": 70, "parts": {}, "required_languages": [], "reasons": []}
                for i in indexes}

    monkeypatch.setattr(search.scoring, "score_groups", score)
    with db.connect() as conn:
        run_id = conn.execute(
            "INSERT INTO searches (status, form_json) VALUES ('running', '{}')"
        ).lastrowid
    run = search.SearchRun(run_id, SearchForm(), NOW.isoformat())
    saved = pool.Pool(
        run_id, [pool.PoolJob(JobGroup([job]), unrelated=False)], PROFILE, different_jobs=1
    )
    client = SimpleNamespace(web_research_unavailable_reason=lambda: "Fictional offline test")
    search._decide(
        run,
        client,
        ctx.keys,
        ctx.http,
        Settings(),
        plan,
        saved,
        pipeline.Collected([job], [ctx.report], {"jsearch": source}),
        [],
        lambda: None,
    )
    assert not run.result["jobs"]["cards"]  # never a match without the location evidence
    assert scored == ([0] if location_answer == "unknown" else [])
    assert not requests


def test_ads_listed_within_the_lag_are_found_not_older_copies(setup):
    # Google for Jobs lists ads days after their date: a 24-hour search would never count one.
    source, ctx, _ = setup(lambda _: page([
        item("late", job_posted_at_datetime_utc=(NOW - timedelta(hours=60)).isoformat()),
        item("old", job_posted_at_datetime_utc=(NOW - timedelta(hours=24 + 72 + 1)).isoformat()),
    ]))
    late, old = list(source.search(query(hours=24), ctx))
    assert not late.older_copy and old.older_copy
