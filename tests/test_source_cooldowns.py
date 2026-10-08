"""Source delays and Stop use fictional transports; no vacancy traffic or real waits."""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from email.utils import format_datetime
from types import SimpleNamespace

import httpx
import pytest

from jobcu.sources import http as source_http
from jobcu.sources.base import FoundJob, JobQuery, JobSource

HOST = "jobs.example.test"
URL = f"https://{HOST}/hardware-engineer"
NOW = datetime(2026, 10, 8, 12, tzinfo=UTC).timestamp()


class Clock:
    def __init__(self):
        self.seconds = 100.0
        self.sleeps = []

    def read(self):
        return self.seconds

    def sleep(self, seconds):
        assert seconds >= 0
        self.sleeps.append(seconds)
        self.seconds += seconds


def client(handler, clock, **kwargs):
    return source_http.PoliteClient(
        min_intervals={HOST: 0, "other.example.test": 0},
        sleep=clock.sleep, clock=clock.read, wall_clock=lambda: NOW,
        transport=httpx.MockTransport(handler), **kwargs,
    )


@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.parametrize("header", ["600", format_datetime(
    datetime.fromtimestamp(NOW + 600, UTC), usegmt=True,
)])
def test_numeric_and_http_date_delays_are_not_shortened(status, header):
    clock, times, notes = Clock(), [], []

    def handler(request):
        times.append(clock.read())
        if len(times) == 1:
            return httpx.Response(status, headers={"Retry-After": header})
        return httpx.Response(200, text="Full fictional nursing ad")

    http = client(handler, clock, on_wait=lambda host, seconds: notes.append((host, seconds)))
    try:
        response = http.get(URL)
        assert response.text == "Full fictional nursing ad"
        assert times == [100, 700]
        assert http.request_count == {HOST: 2}
        assert notes == [(HOST, 600)]
        assert http.get(URL) is response
        assert len(times) == 2
    finally:
        http.close()


@pytest.mark.parametrize(("header", "expected"), [
    ("0", 0), (" 7 ", 7), ("-2", None), ("nan", None), ("inf", None),
    ("tomorrow", None), ("7.5", None),
    ("Thu, 08 Oct 2026 12:00:09 GMT", 9),
    ("Thu, 08 Oct 2026 11:59:59 GMT", 0),
    ("Thursday, 08-Oct-26 12:00:09 GMT", 9),
    ("Thu Oct  8 12:00:09 2026", 9),
])
def test_retry_after_forms_and_invalid_values(header, expected):
    response = httpx.Response(429, headers={"Retry-After": header})
    assert source_http._retry_after(response, now=NOW) == expected


def test_final_failed_attempt_also_delays_the_next_reader():
    clock, times = Clock(), []

    def handler(request):
        times.append(clock.read())
        if request.url.path == "/hardware-engineer":
            return httpx.Response(429, headers={"Retry-After": "600"})
        return httpx.Response(200, text="Full fictional hospitality ad")

    http = client(handler, clock)
    try:
        assert http.get(URL).status_code == 429
        assert times == [100, 700, 1300, 1900]
        assert http.get(f"https://{HOST}/hospitality").status_code == 200
        assert times[-1] == 2500
        assert http.request_count[HOST] == 5
    finally:
        http.close()


def test_parallel_readers_share_cooldown_without_delaying_another_host():
    clock, times = Clock(), []
    waiting, release = threading.Event(), threading.Event()
    http = None

    def sleep(seconds):
        waiting.set()
        assert release.wait(5)
        clock.sleep(seconds)

    def handler(request):
        times.append((request.url.host, request.url.path, clock.read()))
        if request.url.path == "/hardware-engineer" and len(times) == 1:
            return httpx.Response(429, headers={"Retry-After": "600"})
        return httpx.Response(200, text="Full fictional ad")

    http = client(handler, clock)
    http._sleep = sleep
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(http.get, URL)
            try:
                assert waiting.wait(5)
                assert http._host_locks[HOST].locked()
                second = pool.submit(http.get, f"https://{HOST}/nurse")
                other = pool.submit(http.get, "https://other.example.test/chef")
                assert other.result(timeout=5).status_code == 200
                assert not second.done()
            finally:
                release.set()
            assert first.result(timeout=5).status_code == 200
            assert second.result(timeout=5).status_code == 200
        assert next(t for h, p, t in times if p == "/chef") == 100
        assert all(t >= 700 for h, p, t in times[1:] if h == HOST)
    finally:
        release.set()
        http.close()


def test_stop_interrupts_long_delay_without_sending_a_retry():
    clock, calls, stopped = Clock(), [], threading.Event()

    def handler(request):
        calls.append(1)
        return httpx.Response(429, headers={"Retry-After": "600"})

    http = client(handler, clock, should_stop=stopped.is_set)
    def sleep(seconds):
        clock.sleep(seconds)
        stopped.set()
    http._sleep = sleep
    try:
        with pytest.raises(source_http.RequestStopped):
            http.get(URL)
        assert len(calls) == 1
        assert sum(clock.sleeps) <= 0.2
        assert http.request_count[HOST] == 1
    finally:
        http.close()


def test_stop_while_queued_for_a_host_does_not_wait_for_its_reader():
    clock, stopped, queued = Clock(), threading.Event(), threading.Event()
    lock = threading.Lock()
    lock.acquire()

    class QueuedLock:
        def acquire(self, **kwargs):
            queued.set()
            return lock.acquire(**kwargs)

        def release(self):
            lock.release()

    def handler(request):
        pytest.fail("A stopped queued request must not reach the transport")

    http = client(handler, clock, should_stop=stopped.is_set)
    http._host_locks[HOST] = QueuedLock()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(http.get, URL)
            try:
                assert queued.wait(5)
                stopped.set()
                with pytest.raises(source_http.RequestStopped):
                    future.result(timeout=5)
            finally:
                lock.release()
        assert http.request_count == {}
    finally:
        http.close()


def test_bot_protection_is_not_retried_or_contacted_by_later_readers():
    clock, calls = Clock(), []
    def handler(request):
        calls.append(1)
        return httpx.Response(429, text="Please complete the CAPTCHA",
                              headers={"Retry-After": "600"})

    http = client(handler, clock)
    try:
        for address in (URL, f"https://{HOST}/nursing"):
            with pytest.raises(source_http.Blocked):
                http.get(address)
        assert len(calls) == 1
        assert clock.sleeps == []
    finally:
        http.close()


@pytest.mark.parametrize(("header", "delay"), [("0", 0), ("nan", 5), ("-7", 5)])
def test_zero_is_honored_and_invalid_delays_use_normal_backoff(header, delay):
    clock, times = Clock(), []
    def handler(request):
        times.append(clock.read())
        return (httpx.Response(429, headers={"Retry-After": header}) if len(times) == 1
                else httpx.Response(200))
    http = client(handler, clock)
    try:
        assert http.get(URL).status_code == 200
        assert times == [100, 100 + delay]
    finally:
        http.close()


@pytest.mark.parametrize("title", ["Power Electronics Engineer", "Registered Nurse", "Chef"])
def test_cancelled_collection_keeps_already_found_ads(title, monkeypatch):
    from jobcu import pipeline, search

    clock, notes = Clock(), []
    run = SimpleNamespace(stop_requested=False, update=lambda *a: None, note=notes.append)

    class FictionalSource(JobSource):
        id, name, kind = "fictional", "Fictional employer", "employer"

        def search(self, query, ctx):
            yield FoundJob(source=self.id, source_job_id="1", url=URL, title=title)
            ctx.http.get(URL)
            pytest.fail("Collection must stop before reading another page")

    calls = []
    def handler(request):
        calls.append(1)
        return httpx.Response(429, headers={"Retry-After": "600"})

    http = client(handler, clock, should_stop=lambda: run.stop_requested,
                  on_wait=lambda host, seconds: search._source_wait_note(run, host, seconds))
    def sleep(seconds):
        clock.sleep(seconds)
        run.stop_requested = True
    http._sleep = sleep
    monkeypatch.setattr(pipeline, "all_sources", lambda: [FictionalSource()])
    query = JobQuery(["DE", "IE"], [], [], 24, datetime.fromtimestamp(NOW, UTC))
    try:
        collected = pipeline.collect(query, http, None, [], run)
        assert [job.title for job in collected.jobs] == [title]
        assert collected.reports[0].status == "partial"
        assert collected.reports[0].jobs_found == 1
        assert calls == [1]
        assert len(notes) == 1 and HOST in notes[0] and "600 seconds" in notes[0]
        assert "Stop" in notes[0] and "https://" not in notes[0]
    finally:
        http.close()


def test_an_inflight_response_can_extend_an_existing_wait():
    clock, times, counts = Clock(), [], {}
    entered, release, retry_queued = threading.Event(), threading.Event(), threading.Event()
    reader = [None]

    def handler(request):
        path = request.url.path
        counts[path] = counts.get(path, 0) + 1
        times.append((path, clock.read()))
        if path == "/nurse" and counts[path] == 1:
            reader[0] = threading.get_ident()
            entered.set()
            assert release.wait(5)
            return httpx.Response(503, headers={"Retry-After": "600"})
        if path == "/hardware-engineer" and counts[path] == 1:
            return httpx.Response(429, headers={"Retry-After": "600"})
        return httpx.Response(200)

    http = client(handler, clock)
    original = http._wait_turn
    def wait_turn(host):
        if threading.get_ident() == reader[0]:
            retry_queued.set()  # the second response has registered its later deadline
        original(host)
    http._wait_turn = wait_turn

    def sleep(seconds):
        clock.sleep(seconds)
        release.set()
        assert retry_queued.wait(5)
    http._sleep = sleep
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            nurse = pool.submit(http.get, f"https://{HOST}/nurse")
            try:
                assert entered.wait(5)
                engineer = pool.submit(http.get, URL)
                assert engineer.result(timeout=5).status_code == 200
                assert nurse.result(timeout=5).status_code == 200
            finally:
                release.set()
        assert times[:2] == [("/nurse", 100), ("/hardware-engineer", 100)]
        assert all(when == 1300 for path, when in times[2:])
    finally:
        release.set()
        http.close()
