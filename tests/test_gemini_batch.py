"""Google's Batch API takes the work that can wait when Flex is refused: the same half price."""

import json
import threading
import time

import httpx
import pytest
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from jobcu.ai import gemini_batch, request_recovery
from jobcu.ai.base import AIOutputTruncated, Usage
from jobcu.ai.client import AIClient, in_parallel
from jobcu.ai.gemini_adapter import FLEX_FAILURES, FLEX_NOTICE, GeminiAdapter
from jobcu.ai.gemini_batch import Answer, BatchQueue, JobView
from jobcu.ai.providers import configured_adapter
from jobcu.ai.usage import ModelUsage, UsageLog, estimate_cost, price_for
from jobcu.settings import AISettings, ModelPrice, Settings

MODEL = "gemini-4-hydrogen"
BUSY = {"error": {"code": 503, "status": "UNAVAILABLE",
                  "message": "gemini-4-hydrogen is currently experiencing high demand."}}


class Answered(BaseModel):
    ok: bool


def response(text='{"ok":true}', finish=types.FinishReason.STOP):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(parts=[types.Part(text=text)]),
                                    finish_reason=finish)],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=1000, candidates_token_count=300, thoughts_token_count=700))


class FakeBatches:
    """Google's Batch API as Jobcu sees it: jobs answered after `polls` readings."""

    def __init__(self, *, polls=1, answer=None, create_error=None, found=None):
        self.created, self.cancelled, self.deleted, self.read = [], [], [], []
        self.polls = polls
        self.answer = answer or (lambda key, request: Answer(response()))
        self.create_error = create_error
        self.found = found
        self.jobs = {}

    def create(self, model, display_name, requests):
        self.created.append((model, display_name, [key for key, _ in requests]))
        if self.create_error is not None:
            raise self.create_error
        name = f"batches/fictional-{len(self.created)}"
        self.jobs[name] = dict(requests)
        return name

    def find(self, display_name):
        return self.found

    def get(self, name, keys):
        self.read.append(name)
        requests = self.jobs.get(name, {})
        if name in self.cancelled:
            return JobView("JOB_STATE_CANCELLED")
        if self.read.count(name) < self.polls:
            return JobView("JOB_STATE_RUNNING")
        answers = {}
        for key in keys or list(requests):
            answer = self.answer(key, requests.get(key))
            if answer is not None:
                answers[key] = answer
        return JobView("JOB_STATE_SUCCEEDED", answers)

    def cancel(self, name):
        self.cancelled.append(name)

    def delete(self, name):
        self.deleted.append(name)


@pytest.fixture
def service():
    sdks = []

    def make(fake=None, *, flex_answers=("busy",), batching=False, recover=True, batch=True):
        """`flex_answers` gives each interaction POST "busy" (Flex refused) or "accepted"."""
        posts, notices, waits = [], [], []
        adapter = GeminiAdapter("fictional-key")
        adapter.flex, adapter.batch = True, batch
        fake = fake or FakeBatches()
        adapter._batches = BatchQueue(fake, pause=lambda seconds: None)
        adapter._batches.quiet = 0.0
        if batching:
            adapter._flex_failures = FLEX_FAILURES
            adapter._flex_paused_at = adapter._clock()

        def handle(request):
            if request.method == "POST":
                body = json.loads(request.content)
                posts.append(body)
                answer = flex_answers[min(len(posts), len(flex_answers)) - 1]
                if answer == "busy" and body.get("service_tier") == "flex":
                    return httpx.Response(503, json=BUSY)
                return httpx.Response(200, json={
                    "id": f"fictional-{len(posts)}", "status": "in_progress",
                    "service_tier": body.get("service_tier", "standard")})
            if request.method == "DELETE":
                return httpx.Response(200, json={})
            tier = posts[-1].get("service_tier", "standard")
            return httpx.Response(200, json={
                "id": request.url.path.rsplit("/", 1)[-1], "status": "completed",
                "service_tier": tier,
                "steps": [{"type": "model_output",
                           "content": [{"type": "text", "text": '{"ok":true}'}]}],
                "usage": {"total_input_tokens": 1000, "total_output_tokens": 300,
                          "total_thought_tokens": 700}})

        sdk = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            client_args={"transport": httpx.MockTransport(handle)}))
        adapter._genai_client = sdk
        sdks.append(sdk)
        settings = Settings()
        settings.ai.provider, settings.ai.model = "gemini", MODEL
        settings.ai.recover_interrupted_requests = recover
        client = AIClient(settings, adapter=adapter, usage_log=UsageLog(), search_id=1,
                          sleep=waits.append, notify=notices.append)
        return client, fake, posts, notices

    yield make
    for sdk in sdks:
        sdk.close()


def ask(client, prompt="Fictional electronics graduate"):
    return client.generate(Answered, step="scoring", system="Use only fictional evidence",
                           prompt=prompt)


def recorded():
    return {usage.model: usage.usage for usage in UsageLog().for_search_by_model(1)}


def test_a_request_flex_refuses_goes_into_a_batch_job_at_the_same_half_price(service):
    client, fake, posts, notices = service()
    assert ask(client).ok
    # One refused Flex attempt, no waiting for Flex to have room: the request went to Batch.
    assert [post.get("service_tier") for post in posts] == ["flex"]
    assert len(fake.created) == 1 and len(fake.created[0][2]) == 1
    assert list(recorded()) == [f"{MODEL} (batch)"]
    assert recorded()[f"{MODEL} (batch)"].output_tokens == 1000
    normal = ModelPrice(provider="gemini", model=MODEL, input_per_million=1.5,
                        output_per_million=7.5)
    cost, complete = estimate_cost(UsageLog().for_search_by_model(1), [normal])
    assert complete and cost == pytest.approx((1000 * 1.5 + 1000 * 7.5) / 2 / 1e6)
    assert notices == [gemini_batch.NOTICE]
    # The job's stay at Google ends with the answer, and nothing is left to clean up.
    assert fake.deleted == ["batches/fictional-1"]
    assert request_recovery.pending("gemini", force=True) == []


def test_the_rest_of_the_search_goes_to_batch_without_trying_flex_each_time(service):
    client, fake, posts, notices = service()
    assert ask(client).ok and ask(client).ok
    assert [post.get("service_tier") for post in posts] == ["flex"]
    assert len(fake.created) == 2
    assert notices.count(gemini_batch.NOTICE) == 1 and FLEX_NOTICE not in notices


def test_requests_that_can_wait_share_one_batch_job(service):
    client, fake, posts, _ = service(batching=True)
    queue = client.adapter()._batches
    queue.quiet, queue.pause = 0.5, time.sleep  # real seconds: every request joins first
    seen = []

    def work(number):
        seen.append(threading.current_thread().name)
        return ask(client, f"Fictional ad {number}").ok

    assert in_parallel(client, work, list(range(12)), can_wait=True) == [True] * 12
    assert len(fake.created) == 1 and len(fake.created[0][2]) == 12
    assert posts == []  # no Flex or normal request while Batch answers
    assert len(set(seen)) == 12  # all waited together, not four at a time


def test_a_request_the_batch_left_unanswered_is_sent_at_the_normal_price(service):
    unanswered = []

    def answer(key, request):
        if "second" in request.contents:
            unanswered.append(key)
            return Answer(None, "Fictional internal error")
        return Answer(response())

    client, fake, posts, _ = service(FakeBatches(answer=answer), batching=True)
    assert ask(client, "first ad").ok and ask(client, "second ad").ok
    assert unanswered and [post.get("service_tier") for post in posts] == [None]
    assert set(recorded()) == {MODEL, f"{MODEL} (batch)"}


def test_a_refused_batch_job_sends_its_requests_the_normal_way_for_the_rest_of_the_search(
        service):
    refused = errors.ClientError(400, {"error": {"code": 400, "message": "Fictional refusal"}})
    client, fake, posts, notices = service(FakeBatches(create_error=refused))
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts] == ["flex", None]
    assert gemini_batch.UNAVAILABLE_NOTICE in notices
    assert not client.batching()
    assert ask(client).ok
    assert len(fake.created) == 1  # not asked again in this search


def test_a_busy_batch_service_is_asked_again_with_the_next_requests(service):
    busy = errors.ServerError(503, {"error": {"code": 503, "message": "Fictional busy"}})
    fake = FakeBatches(create_error=busy)
    client, fake, posts, notices = service(fake)
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts] == ["flex", None]
    fake.create_error = None
    assert ask(client).ok
    assert len(fake.created) == 2 and gemini_batch.UNAVAILABLE_NOTICE not in notices


def test_a_job_whose_creation_went_unanswered_is_found_by_its_name(service):
    # The answer to "create" was lost: the job may exist at Google, running and billing.
    fake = FakeBatches(create_error=httpx.ConnectError("Fictional lost answer"),
                       found="batches/fictional-found")
    client, fake, posts, _ = service(fake)
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts] == ["flex"]
    assert fake.read and set(fake.read) == {"batches/fictional-found"}
    assert fake.deleted == ["batches/fictional-found"]


def test_a_job_unanswered_after_an_hour_is_cancelled_and_its_requests_sent_normally(service):
    client, fake, posts, notices = service(FakeBatches(polls=10**6), batching=True)
    queue = client.adapter()._batches
    now = [0.0]
    queue.clock = lambda: now[0]

    def wait_a_while(seconds):
        now[0] += 600

    client.sleep = wait_a_while
    assert ask(client).ok
    assert fake.cancelled == ["batches/fictional-1"]
    assert [post.get("service_tier") for post in posts] == [None]
    assert queue.unavailable and gemini_batch.UNAVAILABLE_NOTICE in notices


def test_stop_cancels_the_job_and_a_later_start_records_its_bill_and_deletes_it(
        service, monkeypatch):
    class Stopped(Exception):
        pass

    client, fake, posts, _ = service(FakeBatches(polls=3), batching=True)
    readings = []

    def checkpoint():
        if len(fake.read) >= 1:
            readings.append(len(fake.read))
            raise Stopped

    client.checkpoint = checkpoint
    with pytest.raises(Stopped):
        ask(client)
    assert fake.cancelled == ["batches/fictional-1"] and fake.deleted == []
    assert posts == []  # nothing sent the normal way after Stop

    # The next Jobcu start (no process has polled the job for ten minutes): the job has
    # ended; what it answered is billed and recorded.
    monkeypatch.setattr(request_recovery, "STALE_SECONDS", -1)
    fake.cancelled.clear()
    fake.read.extend(["batches/fictional-1"] * 5)
    rows = request_recovery.pending("gemini", force=True)
    assert [row["interaction_id"] for row in rows] == ["batches/fictional-1"]
    adapter = GeminiAdapter("fictional-key")
    adapter._batches = BatchQueue(fake)
    adapter.cleanup_pending(request_recovery.RecoveryContext(False, "gemini", "cleanup"),
                            force=True)
    assert fake.deleted == ["batches/fictional-1"]
    assert request_recovery.pending("gemini", force=True) == []
    assert recorded()[f"{MODEL} (batch)"].output_tokens == 1000


def test_a_truncated_batch_answer_is_asked_again_with_more_room(service):
    answers = iter([Answer(response(finish=types.FinishReason.MAX_TOKENS)), Answer(response())])
    client, fake, posts, _ = service(FakeBatches(answer=lambda key, request: next(answers)),
                                     batching=True)
    assert ask(client).ok
    limits = [fake.jobs[f"batches/fictional-{n}"] for n in (1, 2)]
    first, second = (next(iter(job.values())).config.max_output_tokens for job in limits)
    assert second > first
    assert posts == []


def test_a_refusal_or_truncation_carries_its_bill():
    with pytest.raises(AIOutputTruncated) as cut:
        gemini_batch.reply_from(response(finish=types.FinishReason.MAX_TOKENS))
    assert cut.value.usage.output_tokens == 1000 and cut.value.usage.service_tier == "batch"


def test_flex_is_tried_again_after_ten_minutes_and_taken_ends_the_batching(service):
    client, fake, posts, _ = service(flex_answers=("accepted",), batching=True)
    adapter = client.adapter()
    now = [5000.0]
    adapter._clock = lambda: now[0]
    adapter._flex_paused_at = now[0]
    assert ask(client).ok
    assert len(fake.created) == 1 and posts == []
    now[0] += 600
    assert ask(client).ok  # this one tries Flex, and Google takes it
    assert [post.get("service_tier") for post in posts] == ["flex"]
    assert not client.batching()


def test_a_request_sent_to_wait_in_a_batch_stays_there_after_flex_is_served_again(service):
    # The client sent it to wait with many others; Flex being taken again meanwhile must not
    # turn the waiting requests into a burst of Flex requests.
    client, fake, posts, _ = service(flex_answers=("accepted",))
    adapter = client.adapter()  # Flex served: nothing paused
    adapter.configure_request_recovery(
        request_recovery.RecoveryContext(True, "gemini", "scoring", search_id=1))
    reply = adapter.complete_json(
        model=MODEL, system="Use only fictional evidence", prompt="Fictional ad",
        schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
        schema_name="Answered", effort="low", max_output_tokens=500, batch=True)
    assert json.loads(reply.text) == {"ok": True}
    assert posts == [] and len(fake.created) == 1


def test_batch_needs_flex_and_request_recovery_and_reaches_google_only():
    both = AISettings(flex_processing=True, recover_interrupted_requests=True)
    assert configured_adapter("gemini", "fictional-key", both).batch is True
    assert configured_adapter("gemini", "fictional-key", AISettings(
        flex_processing=True)).batch is False
    assert configured_adapter("gemini", "fictional-key", AISettings(
        recover_interrupted_requests=True)).batch is False
    assert configured_adapter("anthropic", "fictional-key", both).batch is False


def test_batch_usage_without_its_own_price_row_costs_half_the_normal_tokens():
    normal = ModelPrice(provider="gemini", model=MODEL, input_per_million=1.5,
                        output_per_million=7.5, cached_input_per_million=0.15)
    half = price_for({("gemini", MODEL): normal}, "gemini", f"{MODEL} (batch)")
    assert (half.input_per_million, half.output_per_million,
            half.cached_input_per_million) == pytest.approx((0.75, 3.75, 0.075))
    usage = [ModelUsage("gemini", f"{MODEL} (batch)", Usage(output_tokens=1_000_000))]
    assert estimate_cost(usage, [normal]) == (pytest.approx(3.75), True)


def test_items_that_can_wait_run_many_at_a_time_only_while_the_provider_batches():
    class Client:
        parallel_requests = 4

        def __init__(self):
            self.batch = False

        def at_once(self, *, can_wait=False):
            return 100 if can_wait and self.batch else self.parallel_requests

    running, most = [0], [0]
    lock = threading.Lock()
    gate = threading.Event()

    def work(item):
        with lock:
            running[0] += 1
            most[0] = max(most[0], running[0])
        gate.wait(0.3)
        with lock:
            running[0] -= 1
        return item

    client = Client()
    assert in_parallel(client, work, list(range(20)), can_wait=True) == list(range(20))
    assert most[0] == 4
    client.batch, most[0] = True, 0
    assert in_parallel(client, work, list(range(20)), can_wait=True) == list(range(20))
    assert most[0] == 20
    most[0] = 0
    assert in_parallel(client, work, list(range(20))) == list(range(20))  # look-ups: 4
    assert most[0] == 4


def test_a_batch_request_carries_its_format_as_gemini_s_own_schema_in_order():
    # A batch request ignored a JSON Schema and followed the same schema in Gemini's own form
    # (2026-11-28); the order of the properties keeps the evidence before the scores.
    from jobcu.ai.schema import strict_json_schema
    from jobcu.scoring import ScoringAnswer

    sent = []

    def handle(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"name": "batches/fictional", "metadata": {
            "name": "batches/fictional", "state": "BATCH_STATE_PENDING"}})

    sdk = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
        client_args={"transport": httpx.MockTransport(handle)}))
    request = gemini_batch.request_for(
        "k", system="Use only fictional evidence", prompt="Fictional ad",
        schema=strict_json_schema(ScoringAnswer), effort="low", max_output_tokens=500)
    assert gemini_batch.BatchService(lambda: sdk).create(
        MODEL, "jobcu fictional", [("k", request)]) == "batches/fictional"
    sdk.close()
    body = sent[0]["batch"]["inputConfig"]["requests"]["requests"][0]
    generation = body["request"]["generationConfig"]
    assert "responseJsonSchema" not in generation and body["metadata"] == {"key": "k"}
    item = generation["responseSchema"]["properties"]["scores"]["items"]
    assert item["property_ordering"][:2] == ["job_id", "ad_language"]
    assert "additional" not in json.dumps(generation)
    assert item["properties"]["years_required"]["nullable"] is True


def test_a_job_google_refused_entirely_is_sent_again_once_then_batch_rests(service):
    # 2026-11-28: for a quarter of an hour Google answered "invalid argument" for every request
    # of every job, plain ones included; the same requests were answered before and after.
    refusals = {"left": 1}

    def answer(key, request):
        if refusals["left"]:
            return Answer(None, "Request contains an invalid argument.")
        return Answer(response())

    fake = FakeBatches(answer=answer)
    original_get = fake.get

    def get(name, keys):
        view = original_get(name, keys)
        if view.state == "JOB_STATE_SUCCEEDED" and name == "batches/fictional-1":
            refusals["left"] = 0  # the next job is answered
        return view

    fake.get = get
    client, fake, posts, notices = service(fake, batching=True)
    assert ask(client).ok
    assert len(fake.created) == 2 and posts == []  # sent again, answered at half price
    assert gemini_batch.UNAVAILABLE_NOTICE not in notices

    # Refused twice in a row: the request goes the normal way and Batch rests for the search.
    refusals["left"] = 10**6
    fake.get = lambda name, keys: JobView("JOB_STATE_SUCCEEDED", {
        key: Answer(None, "Request contains an invalid argument.") for key in keys})
    assert ask(client).ok
    assert len(fake.created) == 4 and [post.get("service_tier") for post in posts] == [None]
    assert gemini_batch.UNAVAILABLE_NOTICE in notices and not client.batching()
