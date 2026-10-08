"""Fictional temporal evidence, without vacancy traffic or provider calls."""

import dataclasses
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest

from jobcu import db, jobstore, pipeline
from jobcu.countries import COUNTRIES
from jobcu.dedupe import JobGroup
from jobcu.filters import apply_rules
from jobcu.freshness import freshness, window_start
from jobcu.keystore import KeyStore
from jobcu.settings import JOB_TYPES
from jobcu.sources.base import SourceContext, SourceReport
from jobcu.sources.careers import Employer
from jobcu.sources.greenhouse import GreenhouseSource, to_found_job
from jobcu.sources.http import PoliteClient

NOW = datetime(2026, 10, 9, 12, tzinfo=UTC)
START = window_start(NOW, 24)
EMPLOYER = Employer("Fictional Clinic", "greenhouse", "fictional", ("DE",))
RECENT = (NOW - timedelta(hours=2)).isoformat()
OLD = (NOW - timedelta(days=20)).isoformat()


def item(**fields):
    return {"id": 1, "title": "Nurse", "absolute_url": "https://example.test/job",
            "location": {"name": "Fictional town"}, "updated_at": RECENT, **fields}


def context(body):
    requests = []

    def handler(request):
        requests.append(str(request.url))
        assert request.url.path == "/v1/boards/fictional/jobs/1"
        return httpx.Response(200, json=body)

    http = PoliteClient(min_intervals={}, sleep=lambda _: None,
                        transport=httpx.MockTransport(handler))
    report = SourceReport("greenhouse", "Greenhouse")
    return SourceContext(http, KeyStore(), report, lambda: False, lambda _: None), requests


def rules(job):
    return apply_rules([JobGroup([job])], remembered_states=[None], started_at=NOW,
                       posted_within_hours=24, job_types=list(JOB_TYPES), exclude_remote=False,
                       countries=list(COUNTRIES))


@pytest.mark.parametrize("publication", [None, "", "not-a-date", 42, {}])
@pytest.mark.parametrize("updated", [RECENT, OLD])
def test_updates_never_prove_original_freshness_or_exclude_uncertain_jobs(publication, updated):
    job = to_found_job(item(first_published=publication, updated_at=updated), EMPLOYER)
    assert job.posted_at is None and job.date_precision == "unknown"
    assert freshness(job.posted_at, job.date_precision, START) == "unknown"
    assert rules(job).kept == [0]


def test_original_dates_and_timezones_still_decide_freshness():
    old = to_found_job(item(first_published=OLD), EMPLOYER)
    assert rules(old).left_out == {"too_old": 1}
    fresh = to_found_job(item(first_published="2026-10-09T12:00:00+02:00"), EMPLOYER)
    assert fresh.posted_at == datetime(2026, 10, 9, 10, tzinfo=UTC)
    assert fresh.date_precision == "exact" and rules(fresh).kept == [0]


def test_date_only_original_is_a_day_not_an_invented_exact_midnight():
    job = to_found_job(item(first_published="2026-10-08"), EMPLOYER)
    assert job.date_precision == "day"
    assert job.posted_at == datetime(2026, 10, 8, 12, tzinfo=UTC)
    assert rules(job).kept == [0]  # the day overlaps the last-24-hour boundary


@pytest.mark.parametrize("text", ["", "<p>Full fictional nursing requirements.</p>"])
def test_existing_detail_response_recovers_original_date_and_closed_deadline(text):
    job = to_found_job(item(), EMPLOYER)
    ctx, requests = context({"content": text, "first_published": RECENT,
                             "application_deadline": (NOW - timedelta(hours=1)).isoformat()})
    full = GreenhouseSource().load_details(job, ctx)
    assert full.posted_at == NOW - timedelta(hours=2)
    assert full.closes_at == NOW - timedelta(hours=1)
    assert full.description_is_complete is bool(text)
    assert rules(full).left_out == {"closed": 1} and len(requests) == 1


def test_details_can_establish_old_original_date_even_when_text_is_empty():
    ctx, requests = context({"first_published": OLD, "updated_at": RECENT})
    full = GreenhouseSource().load_details(to_found_job(item(), EMPLOYER), ctx)
    assert rules(full).left_out == {"too_old": 1}
    assert not full.description_is_complete and len(requests) == 1


def test_bad_details_keep_known_list_dates_and_do_not_invent_a_deadline():
    job = to_found_job(item(first_published=RECENT), EMPLOYER)
    ctx, _ = context({"content": "<p>Full ad.</p>", "first_published": False,
                      "application_deadline": "later"})
    full = GreenhouseSource().load_details(job, ctx)
    assert full.posted_at == job.posted_at and full.closes_at is None


@pytest.mark.parametrize("country", list(COUNTRIES))
def test_original_temporal_rules_keep_every_country_and_profession(country):
    title = ["Power Electronics Engineer", "Nurse", "Primary school teacher"][
        list(COUNTRIES).index(country) % 3]
    job = dataclasses.replace(to_found_job(item(title=title), EMPLOYER), country=country)
    ctx, _ = context({"content": "<p>Full fictional requirements.</p>", "first_published": RECENT})
    assert rules(GreenhouseSource().load_details(job, ctx)).kept == [0]


def test_reader_versions_reject_legacy_dates_but_preserve_unchanged_readers():
    job = to_found_job(item(), EMPLOYER)
    legacy = dataclasses.replace(job, posted_at=NOW - timedelta(hours=1), date_precision="exact",
                                 description="Full fictional ad", description_is_complete=True)
    jobstore.remember_ad(legacy)
    # Actual pre-version JSON has no version marker.
    with db.connect() as conn:
        conn.execute("UPDATE ad_texts SET details_json = "
                     "json_remove(details_json, '$._reader_version')")
    assert jobstore.remembered_ad(job) is not None  # unchanged default version
    assert jobstore.remembered_ad(job, reader_version=2) is None
    full = dataclasses.replace(legacy, posted_at=NOW - timedelta(days=20))
    jobstore.remember_ad(full, reader_version=2)
    assert jobstore.remembered_ad(job, reader_version=2).posted_at == full.posted_at
    assert jobstore.remembered_ad(job, reader_version=3) is None


def test_pipeline_refreshes_legacy_cache_once_then_reuses_correct_evidence():
    job = to_found_job(item(), EMPLOYER)
    legacy = dataclasses.replace(job, posted_at=NOW - timedelta(hours=1), date_precision="exact",
                                 description="Full fictional ad", description_is_complete=True)
    jobstore.remember_ad(legacy)
    ctx, requests = context({"content": "<p>Full original fictional nursing requirements.</p>",
                             "first_published": OLD})
    source = GreenhouseSource()
    collected = SimpleNamespace(sources={"greenhouse": source}, reports=[ctx.report])
    run = SimpleNamespace(stop_requested=False, note=lambda _: None, update=lambda *args: None)
    groups = [JobGroup([job])]
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert rules(groups[0].main).left_out == {"too_old": 1}
    assert len(requests) == 1
    groups = [JobGroup([job])]
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].posted_at == NOW - timedelta(days=20) and len(requests) == 1


def test_unsafe_cache_and_unavailable_reader_leave_job_unknown_without_traffic():
    job = to_found_job(item(), EMPLOYER)
    jobstore.remember_ad(dataclasses.replace(
        job, posted_at=NOW, date_precision="exact", description="Old full text",
        description_is_complete=True,
    ))
    ctx, requests = context({})
    ctx.report.status = "unavailable"
    collected = SimpleNamespace(sources={"greenhouse": GreenhouseSource()}, reports=[ctx.report])
    run = SimpleNamespace(stop_requested=False, note=lambda _: None, update=lambda *args: None)
    groups = [JobGroup([job])]
    pipeline.load_full_ads(groups, [0], collected, ctx.http, ctx.keys, run)
    assert groups[0].posted_at is None and groups[0].date_precision == "unknown"
    assert rules(groups[0].main).kept == [0] and requests == []
