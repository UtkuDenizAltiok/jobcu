"""Native contract and cost failure paths through the real SDK, entirely offline."""

import copy
import json

import httpx
import openai
import pytest
from pydantic import BaseModel

from jobcu.ai import mimo_adapter
from jobcu.ai.base import (
    AIInvalidOutput,
    AILimitReached,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRefused,
    AIUsageUncertain,
    AIWebSearchUnavailable,
    Usage,
)
from jobcu.ai.client import AIClient
from jobcu.ai.mimo_adapter import MiMoAdapter
from jobcu.ai.providers import configured_adapter
from jobcu.ai.usage import UsageLog
from jobcu.settings import AISettings, Settings


def payload(*, research=False, tools=1, pages=2):
    message = {"role": "assistant", "content": '{"ok":true}'}
    usage = {"prompt_tokens": 100, "completion_tokens": 20,
             "prompt_tokens_details": {"cached_tokens": 30},
             "completion_tokens_details": {"reasoning_tokens": 5}}
    if research:
        message["content"] = "The fictional city figures need a comparable geographic unit."
        message["annotations"] = [
            {"type": "url_citation", "url": "https://official.example/table", "title": "Table"},
            {"type": "url_citation", "url": "https://official.example/table", "title": "Copy"},
        ]
        usage["web_search_usage"] = {"tool_usage": tools, "page_usage": pages}
    return {"id": "chat_fictional", "object": "chat.completion", "created": 1,
            "model": "fictional-model", "choices": [{"index": 0, "finish_reason": "stop",
                                                        "message": message}], "usage": usage}


def streamed(value):
    """The answer as the service streams it (seen 2026-10-31): usage in the last chunk."""
    head = {"id": "chat_fictional", "object": "chat.completion.chunk", "created": 1,
            "model": "fictional-model"}
    choice = value["choices"][0]
    chunks = [{**head, "choices": [{"index": 0, "finish_reason": choice["finish_reason"],
                                    "delta": {"role": "assistant",
                                              "content": choice["message"]["content"]}}]}]
    if "usage" in value:
        chunks.append({**head, "choices": [], "usage": value["usage"]})
    text = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=text)


@pytest.fixture
def service():
    clients = []

    def make(values):
        adapter = MiMoAdapter("fictional-key")
        requests = []
        values = values if isinstance(values, list) else [values]

        def handle(request):
            requests.append(request)
            value = values[min(len(requests) - 1, len(values) - 1)]
            if isinstance(value, httpx.Response):
                return value
            if json.loads(request.content).get("stream"):
                return streamed(value)
            return httpx.Response(200, json=value)

        sdk = openai.OpenAI(api_key=adapter.api_key, base_url=adapter.base_url, max_retries=0,
                            http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        adapter._sdk_client = sdk
        clients.append(sdk)
        return adapter, requests

    yield make
    for sdk in clients:
        sdk.close()


class Answer(BaseModel):
    ok: bool


def client(adapter, **kwargs):
    settings = Settings(ai=AISettings(provider="mimo", model="fictional-model"))
    return AIClient(settings, adapter=adapter, patient=False, **kwargs)


def research(adapter, maximum=4):
    return adapter.research(model="fictional-model", system="Verify fictional public evidence.",
        prompt="Compare a fictional city's population and election units without inventing facts.",
        max_searches=maximum, max_output_tokens=16000, effort="medium")


@pytest.mark.parametrize("profession", ["power electronics", "nursing", "primary teaching"])
def test_native_generation_uses_documented_controls(service, profession):
    adapter, calls = service(payload())
    notes = []
    ai = client(adapter, notify=notes.append)
    for _ in range(2):
        assert ai.generate(Answer, step="scoring", system="Use only the fictional evidence.",
                           prompt=f"Fictional {profession} profile and full advertisement.").ok
    body = json.loads(calls[0].content)
    assert str(calls[0].url) == "https://api.xiaomimimo.com/v1/chat/completions"
    assert calls[0].headers["authorization"] == "Bearer fictional-key"
    assert body["thinking"] == {"type": "enabled"}
    assert body["response_format"] == {"type": "json_object"}
    # Its thinking can outlast a silent request's timeout; a stream stays busy.
    assert body["stream"] is True and body["stream_options"] == {"include_usage": True}
    assert '"required"' in body["messages"][1]["content"]
    assert body["max_completion_tokens"] == 16000
    assert "max_tokens" not in body and "reasoning_effort" not in body
    assert len(calls) == 2  # no unsupported schema probe before the real request
    assert sum("literal medium" in note for note in notes) == 1


def test_native_host_is_fixed_and_other_api_stays_independent():
    settings = AISettings(provider="mimo", model="fictional-model",
                          base_url="https://unrelated.example/v1")
    adapter = configured_adapter("mimo", "fictional-key", settings)
    assert isinstance(adapter, MiMoAdapter)
    assert adapter.base_url == "https://api.xiaomimimo.com/v1"


@pytest.mark.parametrize("maximum,keywords", [(1, 1), (4, 4), (10, 10), (25, 10)])
def test_research_gets_the_shared_query_allowance_and_records_billed_pages(
        service, maximum, keywords):
    results = mimo_adapter.RESULTS_PER_KEYWORD
    adapter, calls = service(payload(research=True, tools=keywords, pages=keywords * results))
    answer = research(adapter, maximum)
    body = json.loads(calls[0].content)
    assert body["tools"] == [{"type": "web_search", "force_search": True,
                              "max_keyword": keywords, "limit": results}]
    assert body["thinking"] == {"type": "enabled"}
    assert body["max_completion_tokens"] == 16000
    assert answer.usage == Usage(100, 20, 30, 5, keywords, web_results=keywords * results)
    assert answer.usage.web_searches <= maximum
    assert [(s.url, s.title) for s in answer.sources] == [
        ("https://official.example/table", "Table")]
    assert answer.citations is None  # URL annotations are not a generated-passage mapping


@pytest.mark.parametrize("maximum", [0, -1])
def test_insufficient_shared_allowance_never_dispatches(service, maximum):
    adapter, calls = service(payload(research=True))
    with pytest.raises(AILimitReached):
        research(adapter, maximum)
    assert not calls


@pytest.mark.parametrize("field,value", [("tool_usage", None), ("page_usage", None),
    ("tool_usage", -1), ("page_usage", True), ("tool_usage", "1"), ("page_usage", 2.5)])
def test_incomplete_research_counts_stop_before_any_repetition(service, field, value):
    body = payload(research=True)
    if value is None:
        body["usage"]["web_search_usage"].pop(field)
    else:
        body["usage"]["web_search_usage"][field] = value
    adapter, calls = service(body)
    ai, usage = client(adapter, usage_log=UsageLog()), UsageLog()
    for _ in range(2):
        with pytest.raises(AIUsageUncertain):
            ai.research(step="location", system="Fictional rules", prompt="Fictional city")
    assert len(calls) == 1
    receipt = usage.this_month()[0].usage
    assert receipt.input_tokens == 100 and receipt.output_tokens == 20
    assert receipt.unreported_requests == 1


@pytest.mark.parametrize("field", ["usage", "prompt_tokens", "completion_tokens"])
@pytest.mark.parametrize("operation", ["structured", "research"])
def test_missing_tokens_stop_paid_paths_and_preserve_available_receipt(service, field, operation):
    body = payload(research=operation == "research")
    if field == "usage":
        body.pop(field)
    else:
        body["usage"].pop(field)
    adapter, calls = service(body)
    ai = client(adapter, usage_log=UsageLog())
    for _ in range(2):
        with pytest.raises(AIUsageUncertain):
            if operation == "research":
                ai.research(step="location", system="Rules", prompt="Fictional city")
            else:
                ai.generate(Answer, step="scoring", system="Rules", prompt="Fictional nurse")
    assert len(calls) == 1
    assert UsageLog().this_month()[0].usage.unreported_requests == 1


@pytest.mark.parametrize("tools,pages", [(5, 5), (1, 21)])
def test_provider_exceeding_requested_bounds_preserves_bill_and_stops(service, tools, pages):
    adapter, calls = service(payload(research=True, tools=tools, pages=pages))
    ai = client(adapter, usage_log=UsageLog())
    for _ in range(2):
        with pytest.raises(AIUsageUncertain, match="exceeded"):
            ai.research(step="location", system="Rules", prompt="Fictional city", max_searches=4)
    assert len(calls) == 1
    receipt = UsageLog().this_month()[0].usage
    assert (receipt.web_searches, receipt.web_results) == (tools, pages)


@pytest.mark.parametrize("finish,expected", [("length", AIOutputTruncated),
    ("content_filter", AIRefused), ("tool_calls", AIInvalidOutput),
    ("repetition_truncation", AIInvalidOutput), (None, AIInvalidOutput)])
def test_partial_research_is_never_published_as_verified_evidence(service, finish, expected):
    body = payload(research=True)
    body["choices"][0]["finish_reason"] = finish
    adapter, calls = service(body)
    with pytest.raises(expected) as found:
        research(adapter)
    assert found.value.usage == Usage(100, 20, 30, 5, 1, web_results=2)
    assert len(calls) == 1


@pytest.mark.parametrize("annotations", [[], [{"type": "url_citation", "url": "file:///x"}],
    [{"type": "url_citation", "url": "https://user:secret@official.example/table"}]])
def test_unsourced_memory_or_unsafe_links_cannot_verify_current_facts(service, annotations):
    body = payload(research=True)
    body["choices"][0]["message"]["annotations"] = annotations
    body["choices"][0]["message"]["content"] += " https://invented.example/table"
    adapter, _ = service(body)
    with pytest.raises(AIInvalidOutput) as found:
        research(adapter)
    assert (found.value.usage.web_searches, found.value.usage.web_results) == (1, 2)


def test_one_unsourced_answer_leaves_later_online_checks_available(service):
    unsourced = payload(research=True)
    unsourced["choices"][0]["message"]["annotations"] = []
    adapter, calls = service([unsourced, payload(research=True)])
    ai = client(adapter, usage_log=UsageLog())
    with pytest.raises(AIInvalidOutput):
        ai.research(step="job_places", system="Rules", prompt="Fictional vacancy")
    assert ai.web_research_unavailable_reason() is None
    answer = ai.research(step="job_places", system="Rules", prompt="Another fictional vacancy")
    assert answer.sources and len(calls) == 2


def test_no_search_and_provider_plugin_failure_stay_specific(service):
    body = payload(research=True, tools=0, pages=0)
    body["choices"][0]["message"]["error_message"] = "Fictional plugin failure"
    adapter, _ = service(body)
    with pytest.raises(AIWebSearchUnavailable, match="plugin") as found:
        research(adapter)
    assert found.value.usage == Usage(100, 20, 30, 5)


def test_plugin_activation_refusal_is_not_retried_as_a_connection_problem(service):
    adapter, calls = service(httpx.Response(400, json={"error": {
        "message": "web_search plugin is not activated", "type": "invalid_request_error"}}))
    with pytest.raises(AIWebSearchUnavailable, match="Enable the Web Search plugin"):
        research(adapter)
    assert len(calls) == 1


def test_billing_refusal_stops_subsequent_requests_without_polling(service):
    adapter, calls = service(httpx.Response(402, json={"error": {
        "message": "Insufficient credit balance", "type": "billing_error"}}))
    ai = client(adapter)
    for _ in range(2):
        with pytest.raises(AIQuotaExhausted):
            ai.research(step="location", system="Rules", prompt="Fictional city")
    assert len(calls) == 1


def test_research_usage_reaches_shared_allowance_and_generation_stays_independent(service):
    adapter, calls = service([payload(research=True, tools=1, pages=3), payload()])
    ai = client(adapter, usage_log=UsageLog())
    ai.settings.limits.web_search_cap = 1
    answer = ai.research(step="location", system="Rules", prompt="Fictional city")
    # Queries use the shared allowance like any provider's; result pages are billed apart.
    assert answer.usage.web_searches == 1 and answer.usage.web_results == 3
    assert ai.web_searches_left() == 0
    with pytest.raises(AILimitReached):
        ai.research(step="location", system="Rules", prompt="Another fictional city")
    assert ai.generate(Answer, step="scoring", system="Rules", prompt="Fictional teacher").ok
    assert len(calls) == 2
    assert UsageLog().this_month()[0].usage == Usage(200, 40, 60, 10, 1, web_results=3)


def test_unknown_bill_does_not_become_known_zero_after_truncation(service):
    body = copy.deepcopy(payload())
    body.pop("usage")
    body["choices"][0]["finish_reason"] = "length"
    adapter, calls = service(body)
    ai = client(adapter, usage_log=UsageLog())
    with pytest.raises(AIUsageUncertain):
        ai.generate(Answer, step="scoring", system="Rules", prompt="Fictional engineer")
    assert len(calls) == 1
