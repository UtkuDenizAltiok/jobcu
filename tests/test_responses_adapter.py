"""Responses completion and billed tools through the locked SDK, with no network calls."""

import json

import httpx
import openai
import pytest
from pydantic import BaseModel
from streams import as_stream

from jobcu.ai.base import (
    AIError,
    AIOutputTruncated,
    AIRefused,
    AIUnavailable,
    AIUsageUncertain,
    Usage,
)
from jobcu.ai.client import AIClient
from jobcu.ai.compatible_adapter import CompatibleResponsesAdapter
from jobcu.ai.openai_adapter import OpenAIAdapter
from jobcu.ai.usage import UsageLog
from jobcu.settings import Settings


def response(*, status="completed", usage=True, searches=0, refusal=False):
    value = {
        "id": "resp_fictional", "object": "response", "created_at": 1,
        "model": "fictional-model", "status": status,
        "output": [{"id": "search_fictional_" + str(i), "type": "web_search_call",
                    "status": "completed", "action": {"type": "search", "query": "fictional"}}
                   for i in range(searches)],
    }
    content = ({"type": "refusal", "refusal": "Fictional refusal"} if refusal else {
        "type": "output_text", "text": '{"ok":true}', "annotations": [{
            "type": "url_citation", "url": "https://example.test/city", "title": "City",
            "start_index": 0, "end_index": 11}]})
    value["output"].append({"id": "msg_fictional", "type": "message", "role": "assistant",
                            "status": "completed", "content": [content]})
    if usage:
        value["usage"] = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
                          "input_tokens_details": {"cached_tokens": 2},
                          "output_tokens_details": {"reasoning_tokens": 3}}
    if status == "incomplete":
        value["incomplete_details"] = {"reason": "max_output_tokens"}
    if status == "failed":
        value["error"] = {"code": "server_error", "message": "Fictional service failure"}
    return value


@pytest.fixture
def service():
    clients = []

    def make(value, *, custom=False):
        cls = CompatibleResponsesAdapter if custom else OpenAIAdapter
        adapter = cls("fictional-key", base_url="https://provider.example/v1")
        requests = []

        def handle(request):
            requests.append(json.loads(request.content))
            payload = value[len(requests) - 1] if isinstance(value, list) else value
            return as_stream(request, httpx.Response(200, json=payload))

        sdk = openai.OpenAI(api_key="fictional-key", base_url=adapter.base_url,
                            max_retries=0,
                            http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        clients.append(sdk)
        adapter._sdk_client = sdk
        return adapter, requests

    yield make
    for sdk in clients:
        sdk.close()


def ask(adapter, *, research=False, max_searches=3):
    request = dict(model="fictional-model", system="Use only the stated fictional evidence",
                   prompt="Fictional workplace", effort="medium", max_output_tokens=16000)
    if research:
        return adapter.research(**request, max_searches=max_searches)
    return adapter.complete_json(**request, schema={"type": "object"}, schema_name="Fit")


@pytest.mark.parametrize("limit", [1, 3])
def test_research_sends_the_supported_server_tool_ceiling_and_keeps_evidence(service, limit):
    adapter, requests = service(response(searches=1))
    reply = ask(adapter, research=True, max_searches=limit)
    assert requests[0]["max_tool_calls"] == limit
    assert requests[0]["reasoning"] == {"effort": "medium"}
    assert requests[0]["store"] is False
    assert reply.text == '{"ok":true}'
    assert reply.sources[0].url == "https://example.test/city"
    assert reply.usage == Usage(10, 5, 2, 3, web_searches=1)


@pytest.mark.parametrize("custom,research", [(False, False), (True, False), (False, True)])
@pytest.mark.parametrize("status,refusal,expected", [
    ("incomplete", False, AIOutputTruncated),
    ("failed", False, AIUnavailable),
    ("completed", True, AIRefused),
])
def test_unfinished_or_refused_answers_never_pass_and_retain_the_receipt(
        service, custom, research, status, refusal, expected):
    adapter, requests = service(response(status=status, searches=int(research), refusal=refusal),
                                custom=custom)
    with pytest.raises(expected) as caught:
        ask(adapter, research=research)
    assert caught.value.usage == Usage(10, 5, 2, 3, web_searches=int(research))
    assert len(requests) == 1


@pytest.mark.parametrize("status", ["cancelled", "in_progress", "queued", None])
def test_nonterminal_or_unconfirmed_research_is_not_a_completed_fact(service, status):
    adapter, _ = service(response(status=status, searches=1))
    with pytest.raises(AIError) as caught:
        ask(adapter, research=True)
    assert not caught.value.retryable
    assert caught.value.usage.web_searches == 1


@pytest.mark.parametrize("research", [False, True])
def test_completed_answer_without_usage_retains_the_answer_but_not_a_false_complete_bill(
        service, research):
    adapter, _ = service(response(usage=False, searches=int(research)))
    reply = ask(adapter, research=research)
    assert reply.text == '{"ok":true}'
    assert reply.usage == Usage(web_searches=int(research), unreported_requests=1)


def test_failed_research_without_usage_uses_shared_guard_before_another_dispatch(service):
    adapter, requests = service(response(status="failed", usage=False, searches=2))
    configured = Settings()
    configured.ai.provider, configured.ai.model = "openai", "fictional-model"
    ledger, waits = UsageLog(), []
    client = AIClient(configured, adapter=adapter, usage_log=ledger, sleep=waits.append)
    for prompt in ("Fictional city", "Another fictional city"):
        with pytest.raises(AIUsageUncertain):
            client.research(step="location", system="Sourced evidence", prompt=prompt)
    assert len(requests) == 1 and not waits
    assert ledger.this_month()[0].usage == Usage(web_searches=2, unreported_requests=1)
    assert client._web_searches_reserved == 0


@pytest.mark.parametrize("missing", ["input_tokens", "output_tokens"])
def test_partial_usage_keeps_available_counts_and_marks_missing_categories(service, missing):
    value = response(searches=1)
    del value["usage"][missing]
    adapter, _ = service(value)
    usage = ask(adapter, research=True).usage
    assert usage.input_tokens == (0 if missing == "input_tokens" else 10)
    assert usage.output_tokens == (0 if missing == "output_tokens" else 5)
    assert usage.web_searches == usage.unreported_requests == 1


@pytest.mark.parametrize("custom", [False, True])
def test_structured_truncation_repair_accounts_for_both_bills_once(service, custom):
    class Fit(BaseModel):
        ok: bool

    adapter, requests = service([response(status="incomplete"), response()], custom=custom)
    configured = Settings()
    configured.ai.provider, configured.ai.model = "openai", "fictional-model"
    ledger = UsageLog()
    client = AIClient(configured, adapter=adapter, usage_log=ledger)
    assert client.generate(Fit, step="scoring", system="Use evidence", prompt="Fictional job").ok
    assert len(requests) == 2
    assert requests[0]["max_output_tokens"] == 16000
    assert requests[1]["max_output_tokens"] == 20000
    assert ledger.this_month()[0].usage == Usage(20, 10, 4, 6)


@pytest.mark.parametrize("custom", [False, True])
def test_native_responses_stream_and_other_addresses_stay_plain(service, custom):
    adapter, requests = service(response(), custom=custom)
    reply = ask(adapter)
    assert reply.usage.output_tokens == 5 and not reply.usage.unreported_requests
    assert requests[0].get("stream") is (None if custom else True)
