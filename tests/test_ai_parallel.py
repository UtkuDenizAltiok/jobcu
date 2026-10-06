"""Several AI requests at a time for the steps with many (ai/client.py, `in_parallel`)."""

import threading
import time

import pytest
from pydantic import BaseModel

from jobcu.ai.base import (
    AIAuthError,
    AILimitReached,
    AIRateLimited,
    AIWebSearchUnavailable,
    ProviderAdapter,
    RawReply,
    ResearchReply,
    Usage,
)
from jobcu.ai.client import PARALLEL_REQUESTS, AIClient, in_parallel
from jobcu.settings import Settings


class Echo(BaseModel):
    word: str


class Counting(ProviderAdapter):
    """Answers with the prompt, and counts how many requests wait for an answer at once."""

    can_search_the_web = True

    def __init__(self, rate_limit_first=False, barrier=None):
        super().__init__("fake-key")
        self.lock = threading.Lock()
        self.running = self.most_at_once = self.calls = 0
        self.rate_limit_first = rate_limit_first
        self.barrier = barrier

    def _enter(self):
        with self.lock:
            self.calls += 1
            if self.rate_limit_first and self.calls == 1:
                raise AIRateLimited("too many requests", "429", retry_after=0)
            self.running += 1
            self.most_at_once = max(self.most_at_once, self.running)

    def _leave(self):
        with self.lock:
            self.running -= 1

    def complete_json(self, **request):
        self._enter()
        try:
            if self.barrier is not None:
                self.barrier.wait(timeout=5)  # breaks unless enough requests run together
            time.sleep(0.01)
            return RawReply(f'{{"word": "{request["prompt"]}"}}', Usage(1, 1))
        finally:
            self._leave()

    def research(self, **request):
        self._enter()
        try:
            time.sleep(0.01)
            return ResearchReply("notes", [], Usage(1, 1, web_searches=request["max_searches"]))
        finally:
            self._leave()

    def list_models(self):
        return []


def client(adapter, cap=50):
    settings = Settings()
    settings.ai.provider = "gemini"
    settings.ai.model = "m"
    settings.limits.web_search_cap = cap
    return AIClient(settings, adapter=adapter, sleep=lambda seconds: None)


def ask(ai):
    return lambda word: ai.generate(Echo, step="scoring", system="Echo", prompt=word).word


def test_several_requests_wait_together_and_the_results_keep_their_order():
    adapter = Counting(barrier=threading.Barrier(PARALLEL_REQUESTS))
    ai = client(adapter)
    words = [f"w{i}" for i in range(2 * PARALLEL_REQUESTS)]
    finished = []
    results = in_parallel(ai, ask(ai), words, lambda word, result: finished.append(word))
    assert results == words
    assert adapter.most_at_once == PARALLEL_REQUESTS
    assert sorted(finished) == sorted(words)


def test_after_one_rate_limit_the_rest_of_the_search_asks_one_at_a_time():
    adapter = Counting(rate_limit_first=True)
    ai = client(adapter)
    assert ask(ai)("first") == "first"  # waited, then answered
    assert ai.parallel_requests == 1
    assert in_parallel(ai, ask(ai), ["a", "b", "c", "d", "e"]) == ["a", "b", "c", "d", "e"]
    assert adapter.most_at_once == 1


def test_the_first_error_stops_the_items_not_started_yet():
    ai = client(Counting())
    ai.parallel_requests = 2
    started = []

    def work(item):
        started.append(item)
        if item == 0:
            raise AIAuthError("Please check your AI key in Settings.")
        time.sleep(0.05)
        return item

    with pytest.raises(AIAuthError):
        in_parallel(ai, work, list(range(20)))
    assert len(started) < 20


def test_web_look_ups_sent_together_never_go_past_the_cap():
    adapter = Counting()
    ai = client(adapter, cap=10)

    def look_up(item):
        try:
            return ai.research(step="job_places", system="Find", prompt=str(item),
                               max_searches=4).usage.web_searches
        except AILimitReached:
            return 0

    searches = in_parallel(ai, look_up, list(range(6)))
    assert sum(searches) == ai.web_searches_used == 10
    assert ai.web_searches_left() == 0


def test_one_item_or_one_request_at_a_time_runs_in_the_calling_thread():
    ai = client(Counting())
    ai.parallel_requests = 1
    threads = in_parallel(ai, lambda item: threading.current_thread(), [1, 2, 3])
    assert set(threads) == {threading.current_thread()}


def test_web_refusal_stops_queued_requests_and_announces_once():
    class Refused(Counting):
        def research(self, **request):
            with self.lock:
                self.calls += 1
            time.sleep(0.01)
            raise AIWebSearchUnavailable("Web search unavailable")

    adapter = Refused()
    ai = client(adapter)
    notices = []
    ai.notify = notices.append

    def attempt(item):
        try:
            ai.research(step="employers", system="Find", prompt=str(item), max_searches=1)
        except AIWebSearchUnavailable:
            return False
        return True

    assert in_parallel(ai, attempt, list(range(20))) == [False] * 20
    assert 1 <= adapter.calls <= PARALLEL_REQUESTS
    assert notices == ["Web search unavailable"]
    assert ai._web_searches_reserved == 0 and ai.web_searches_used == 0
