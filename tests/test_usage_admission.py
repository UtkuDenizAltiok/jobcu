"""Queued paid work must see the preceding successful receipt before dispatch."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from test_ai_cost_recovery import GOOD, ask, settings

from jobcu.ai.base import AILimitReached, ProviderAdapter, RawReply, ResearchReply, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.usage import UsageLog
from jobcu.settings import ModelPrice


@pytest.mark.parametrize("kind", ["research", "structured"])
@pytest.mark.parametrize("limit", ["tokens", "cost"])
def test_successful_receipt_is_recorded_before_queued_request_checks_its_limit(
        tmp_path, kind, limit):
    recording, allow_receipt, premature = (threading.Event() for _ in range(3))

    class Ledger(UsageLog):
        def record(self, **kwargs):
            recording.set()
            assert allow_receipt.wait(timeout=5)
            super().record(**kwargs)

    class Adapter(ProviderAdapter):
        can_search_the_web = True

        def __init__(self):
            super().__init__("fictional-key")
            self.calls = 0

        def answer(self):
            self.calls += 1
            if self.calls > 1:
                premature.set()

        def complete_json(self, **request):
            self.answer()
            return RawReply(GOOD, Usage(10, 5))

        def research(self, **request):
            self.answer()
            return ResearchReply("Complete fictional evidence", [], Usage(10, 5, web_searches=1))

        def list_models(self):
            return []

    configured = settings()
    if limit == "tokens":
        configured.limits.monthly_token_limit = 15
    else:
        configured.limits.monthly_cost_limit = 0.000014
        configured.prices = [ModelPrice(
            provider="gemini", model="fictional-model", input_per_million=1,
            output_per_million=1, web_search_per_thousand=1)]
    adapter, ledger = Adapter(), Ledger(tmp_path)
    ai = AIClient(configured, adapter=adapter, usage_log=ledger)
    ai.parallel_requests = 1

    def work():
        if kind == "structured":
            return ask(ai)
        return ai.research(step="job_places", system="Find fictional evidence",
                           prompt="Fictional vacancy", max_searches=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(work)
        assert recording.wait(timeout=5)
        pending = pool.submit(work)
        try:
            assert not premature.wait(timeout=0.1)
        finally:
            allow_receipt.set()
        assert first.result(timeout=5)
        with pytest.raises(AILimitReached):
            pending.result(timeout=5)
    assert adapter.calls == 1
    assert ledger.this_month()[0].usage == Usage(10, 5, web_searches=int(kind == "research"))


def test_completed_web_use_releases_its_reservation_before_accepting_more_work(tmp_path):
    from test_ai_parallel import Counting, client

    recording, allow_receipt, second_finished = (threading.Event() for _ in range(3))

    class Ledger(UsageLog):
        first = True

        def record(self, **kwargs):
            if self.first:
                self.first = False
                recording.set()
                assert allow_receipt.wait(timeout=5)
            super().record(**kwargs)

    adapter, ledger = Counting(), Ledger(tmp_path)
    ai = client(adapter, cap=2)
    ai.parallel_requests, ai.usage_log = 1, ledger

    def work(second=False):
        try:
            return ai.research(step="job_places", system="Read fictional evidence",
                               prompt="Fictional vacancy", max_searches=1)
        finally:
            if second:
                second_finished.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(work)
        assert recording.wait(timeout=5)
        second = pool.submit(work, True)
        try:
            assert not second_finished.wait(timeout=0.1)
        finally:
            allow_receipt.set()
        assert first.result(timeout=5).text == second.result(timeout=5).text == "notes"
    assert adapter.calls == 2 and ai.web_searches_left() == 0
    assert ledger.this_month()[0].usage == Usage(2, 2, web_searches=2)
