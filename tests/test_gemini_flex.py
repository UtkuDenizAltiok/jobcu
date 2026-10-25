"""Google Flex: half-price queued processing, retried when busy, never paid for twice."""

import json

import httpx
import pytest
from google import genai
from google.genai import types
from pydantic import BaseModel

from jobcu.ai import client as ai_client
from jobcu.ai import gemini_adapter
from jobcu.ai.base import AIUnavailable, Usage
from jobcu.ai.client import AIClient, check_setup
from jobcu.ai.gemini_adapter import FLEX_ATTEMPTS, FLEX_FAILURES, FLEX_NOTICE, GeminiAdapter
from jobcu.ai.providers import configured_adapter
from jobcu.ai.usage import ModelUsage, UsageLog, estimate_cost, price_for
from jobcu.keystore import KeyStore
from jobcu.settings import AISettings, ModelPrice, Settings


class Answer(BaseModel):
    ok: bool


BUSY = {"error": {"code": 503, "status": "UNAVAILABLE",
                  "message": "The model is currently experiencing high demand."}}


def finished(tier):
    return {"id": "fictional-1", "status": "completed", "service_tier": tier,
            "steps": [{"type": "model_output",
                       "content": [{"type": "text", "text": '{"ok":true}'}]}],
            "usage": {"total_input_tokens": 1000, "total_output_tokens": 300,
                      "total_thought_tokens": 700, "total_cached_tokens": 0}}


@pytest.fixture
def service():
    sdks = []

    def make(answers, *, flex=True, failures=0, patient=True, recover=True):
        """`answers` gives each POST a response: "busy", "accepted" or "failed"."""
        posts, notices, waits = [], [], []
        adapter = GeminiAdapter("fictional-key")
        adapter.flex = flex
        adapter._flex_failures = failures
        outcome = {}

        def handle(request):
            if request.method == "POST":
                body = json.loads(request.content)
                posts.append(body)
                answer = answers[min(len(posts), len(answers)) - 1]
                if answer == "busy":
                    return httpx.Response(503, json=BUSY)
                outcome["status"] = answer
                return httpx.Response(200, json={
                    "id": "fictional-1", "status": "in_progress",
                    "service_tier": body.get("service_tier", "standard")})
            if request.method == "DELETE":
                return httpx.Response(200, json={})
            tier = posts[-1].get("service_tier", "standard")
            if outcome["status"] == "failed":
                return httpx.Response(200, json={"id": "fictional-1", "status": "failed",
                                                 "service_tier": tier})
            return httpx.Response(200, json=finished(tier))

        sdk = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            client_args={"transport": httpx.MockTransport(handle)}))
        adapter._genai_client = sdk
        sdks.append(sdk)
        settings = Settings()
        settings.ai.provider, settings.ai.model = "gemini", "gemini-3.8-flash"
        settings.ai.recover_interrupted_requests = recover
        client = AIClient(settings, adapter=adapter, usage_log=UsageLog(), search_id=1,
                          sleep=waits.append, notify=notices.append, patient=patient)
        return client, posts, notices, waits

    yield make
    for sdk in sdks:
        sdk.close()


def ask(client):
    return client.generate(Answer, step="scoring", system="Use only fictional evidence",
                           prompt="Fictional electronics graduate")


def recorded_models():
    return [usage.model for usage in UsageLog().for_search_by_model(1)]


def test_flex_answer_is_recorded_apart_and_priced_at_half_the_normal_tokens(service):
    client, posts, notices, _ = service(["accepted"])
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts] == ["flex"]
    assert recorded_models() == ["gemini-3.8-flash (flex)"]
    normal = ModelPrice(provider="gemini", model="gemini-3.8-flash", input_per_million=0.75,
                        output_per_million=3.75, web_search_per_thousand=14.0)
    cost, complete = estimate_cost(UsageLog().for_search_by_model(1), [normal])
    assert complete and cost == pytest.approx((1000 * 0.75 + 1000 * 3.75) / 2 / 1e6)
    assert notices == []


def test_busy_flex_is_tried_again_then_sent_at_the_normal_price(service):
    client, posts, notices, waits = service(["busy"] * FLEX_ATTEMPTS + ["accepted"])
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts] == ["flex"] * FLEX_ATTEMPTS + [None]
    # Refusals came before any accepted work: nothing was generated, so nothing is recorded
    # for them, and the answer is recorded at the normal tier.
    assert recorded_models() == ["gemini-3.8-flash"]
    assert sum(waits) >= gemini_adapter.FLEX_RETRY_SECONDS * (2 ** (FLEX_ATTEMPTS - 1) - 1)
    assert notices == []


def test_repeated_flex_failures_move_the_rest_of_the_search_to_normal_processing(service):
    client, posts, notices, _ = service(
        ["busy"] * FLEX_ATTEMPTS + ["accepted"], failures=FLEX_FAILURES - 1)
    assert ask(client).ok
    assert notices.count(FLEX_NOTICE) == 1
    sent = len(posts)
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts[sent:]] == [None]


def test_accepted_flex_work_that_fails_is_not_sent_again_at_the_normal_price(service):
    client, posts, _, _ = service(["failed", "accepted"], patient=False)
    with pytest.raises(AIUnavailable):
        ask(client)
    assert [post.get("service_tier") for post in posts] == ["flex"]


def test_flex_is_off_unless_chosen(service):
    client, posts, _, _ = service(["accepted"], flex=False)
    assert ask(client).ok
    assert [post.get("service_tier") for post in posts] == [None]
    assert recorded_models() == ["gemini-3.8-flash"]


def test_flex_waits_for_recovery_so_a_preempted_request_is_never_an_ambiguous_drop(service):
    # Without recovery the request streams; the fictional service answers it plainly.
    sdk_posts = []
    client, posts, _, _ = service(["accepted"], recover=False)
    adapter = client.adapter()

    def stream(**request):
        sdk_posts.append(request)
        raise gemini_adapter.AIUnavailable("Fictional stop", "")

    adapter._event_resource().create = stream
    with pytest.raises(AIUnavailable):
        client.generate(Answer, step="scoring", system="Use only fictional evidence",
                        prompt="Fictional electronics graduate")
    assert sdk_posts and all("service_tier" not in request for request in sdk_posts)


def test_a_saved_flex_price_is_used_as_saved():
    normal = ModelPrice(provider="gemini", model="gemini-3.8-flash", input_per_million=0.75,
                        output_per_million=3.75, cached_input_per_million=0.075)
    own = ModelPrice(provider="gemini", model="gemini-3.8-flash (flex)", input_per_million=0.1,
                     output_per_million=0.2)
    table = {(p.provider, p.model): p for p in (normal,)}
    half = price_for(table, "gemini", "gemini-3.8-flash (flex)")
    assert (half.input_per_million, half.output_per_million,
            half.cached_input_per_million) == pytest.approx((0.375, 1.875, 0.0375))
    table[("gemini", own.model)] = own
    assert price_for(table, "gemini", own.model) is own
    assert price_for({}, "gemini", own.model) is None
    usage = [ModelUsage("gemini", own.model, Usage(output_tokens=1_000_000))]
    assert estimate_cost(usage, [own]) == (pytest.approx(0.2), True)


def test_the_setting_reaches_google_only(monkeypatch):
    ai = AISettings(flex_processing=True)
    assert configured_adapter("gemini", "fictional-key", ai).flex is True
    assert configured_adapter("anthropic", "fictional-key", ai).flex is False
    assert configured_adapter("gemini", "fictional-key", AISettings()).flex is False


def test_a_connection_test_does_not_wait_in_the_flex_queue(monkeypatch, tmp_path):
    seen = []

    def fake(provider, key, ai, **options):
        seen.append(ai.flex_processing)
        raise ai_client.AIAuthError("fictional stop")

    monkeypatch.setattr(ai_client, "configured_adapter", fake)
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "gemini-3.8-flash"
    settings.ai.flex_processing = True
    keys = KeyStore(tmp_path)
    keys.set("ai_gemini", "fictional-key")
    assert not check_setup(settings, keys).ok
    assert seen == [False] and settings.ai.flex_processing is True
