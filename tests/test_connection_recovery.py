"""Preserve all work while avoiding concurrent retries over an interrupted AI path."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_ai_parallel import Counting, Echo, client

from jobcu.ai.base import AIConnectionError, AIQuotaExhausted, RawReply, ResearchReply, Usage
from jobcu.ai.client import PARALLEL_REQUESTS, in_parallel
from jobcu.ai.usage import UsageLog


def ask(ai, kind, prompt):
    if kind == "research":
        return ai.research(step="job_places", system="Read fictional evidence", prompt=prompt,
                           max_searches=1).text
    return ai.generate(Echo, step="scoring", system="Keep fictional evidence", prompt=prompt).word


class Recovering(Counting):
    def __init__(self):
        super().__init__()
        self.initial = threading.Barrier(PARALLEL_REQUESTS)
        self.restored = threading.Barrier(PARALLEL_REQUESTS - 1)
        self.probe_started = threading.Event()
        self.allow_success = threading.Event()
        self.premature = threading.Event()
        self.healthy = False
        self.requests = []

    def answer(self, request):
        with self.lock:
            self.calls += 1
            number = self.calls
            self.requests.append(request)
        if number <= PARALLEL_REQUESTS:
            self.initial.wait(timeout=5)
            failure = AIConnectionError("Fictional interrupted connection")
            failure.usage = Usage(10, 5, unreported_requests=1)
            raise failure
        if number == PARALLEL_REQUESTS + 1:
            self.probe_started.set()
            assert self.allow_success.wait(timeout=5)
            self.healthy = True
        elif not self.healthy:
            self.premature.set()
            raise AIConnectionError("Another paid request reached the still broken path")
        else:
            # Healthy work resumes in parallel rather than staying serial for the search.
            self.restored.wait(timeout=5)
        return request["prompt"]

    def complete_json(self, **request):
        value = self.answer(request)
        return RawReply(f'{{"word":"{value}"}}', Usage(20, 8))

    def research(self, **request):
        return ResearchReply(self.answer(request), [], Usage(20, 8, web_searches=1))


@pytest.mark.parametrize("kind", ["research", "structured"])
@pytest.mark.parametrize("profession", ["electronics engineer", "nurse", "teacher"])
def test_one_recovery_request_keeps_every_answer_and_restores_parallel_work(
        tmp_path, kind, profession):
    adapter = Recovering()
    ai = client(adapter)
    ai.usage_log = UsageLog(tmp_path)
    words = [f"{profession} evidence {i}" for i in range(PARALLEL_REQUESTS)]
    with ThreadPoolExecutor(max_workers=1) as driver:
        future = driver.submit(in_parallel, ai, lambda word: ask(ai, kind, word), words)
        try:
            assert adapter.probe_started.wait(timeout=5)
            assert not adapter.premature.wait(timeout=0.1)
        finally:
            adapter.allow_success.set()
        assert future.result(timeout=5) == words
    assert adapter.calls == 2 * PARALLEL_REQUESTS
    # Medium and all original evidence are preserved, including on retries.
    assert all(r["effort"] == "medium" for r in adapter.requests)
    assert {r["prompt"] for r in adapter.requests} == set(words)
    recorded = ai.usage_log.this_month()[0].usage
    assert recorded.input_tokens == PARALLEL_REQUESTS * 30
    assert recorded.output_tokens == PARALLEL_REQUESTS * 13
    assert recorded.unreported_requests == PARALLEL_REQUESTS
    assert ai.parallel_requests == PARALLEL_REQUESTS


class Blocked(Counting):
    def __init__(self, failure=None):
        super().__init__(barrier=threading.Barrier(3))
        self.entered = threading.Event()
        self.extra_research = threading.Event()
        self.research_calls = 0
        self.release = threading.Event()
        self.failure = failure

    def research(self, **request):
        with self.lock:
            self.calls += 1
            self.research_calls += 1
            number = self.research_calls
        if number == 1:
            raise AIConnectionError("Fictional first interruption")
        if number > 2:
            self.extra_research.set()
        self.entered.set()
        assert self.release.wait(timeout=5)
        if self.failure:
            raise self.failure
        return ResearchReply("Complete fictional notes", [], Usage(3, 2, web_searches=1))


def interrupted(adapter, **kwargs):
    ai = client(adapter)
    ai.patient = False
    for key, value in kwargs.items():
        setattr(ai, key, value)
    with pytest.raises(AIConnectionError):
        ask(ai, "research", "first")
    return ai


def test_a_healthy_structured_path_is_independent_of_research_recovery():
    adapter = Blocked()
    ai = interrupted(adapter)
    with ThreadPoolExecutor(max_workers=2) as pool:
        recovery = pool.submit(ask, ai, "research", "recover")
        try:
            assert adapter.entered.wait(timeout=5)
            pending = pool.submit(ask, ai, "research", "queued")
            # The three ordinary slots remain available while one research request recovers.
            assert in_parallel(ai, lambda word: ask(ai, "structured", word), ["a", "b", "c"]) == [
                "a", "b", "c"]
            # Success on another path cannot release the still interrupted research queue.
            assert not adapter.extra_research.wait(timeout=0.1)
        finally:
            adapter.release.set()
        assert recovery.result(timeout=5) == "Complete fictional notes"
        assert pending.result(timeout=5) == "Complete fictional notes"


def test_stop_cancels_recovery_queue_without_another_dispatch(caplog):
    stopped, queued = threading.Event(), threading.Event()

    class Stopped(Exception):
        pass

    def checkpoint():
        if threading.current_thread().name == "waiting":
            queued.set()
        if stopped.is_set():
            raise Stopped()

    adapter = Blocked()
    ai = interrupted(adapter, checkpoint=checkpoint)

    def waiting():
        threading.current_thread().name = "waiting"
        return ask(ai, "research", "queued")

    with ThreadPoolExecutor(max_workers=2) as pool, caplog.at_level("INFO"):
        recovery = pool.submit(ask, ai, "research", "recover")
        assert adapter.entered.wait(timeout=5)
        pending = pool.submit(waiting)
        try:
            assert queued.wait(timeout=5)
            stopped.set()
            with pytest.raises(Stopped):
                pending.result(timeout=2)
        finally:
            adapter.release.set()
        with pytest.raises(Stopped):
            recovery.result(timeout=5)
    assert adapter.calls == 2
    assert "queued" not in caplog.text  # prompt text is never diagnostic output


def test_a_billing_refusal_stops_queued_recovery_without_another_paid_attempt():
    adapter = Blocked(AIQuotaExhausted("Fictional depleted credit"))
    ai = interrupted(adapter)
    with ThreadPoolExecutor(max_workers=2) as pool:
        recovery = pool.submit(ask, ai, "research", "recover")
        assert adapter.entered.wait(timeout=5)
        pending = pool.submit(ask, ai, "research", "queued")
        adapter.release.set()
        for future in (recovery, pending):
            with pytest.raises(AIQuotaExhausted):
                future.result(timeout=5)
    assert adapter.calls == 2
