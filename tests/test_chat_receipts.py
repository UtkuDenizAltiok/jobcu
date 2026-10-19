"""Real SDK parsing with fictional response states; no provider or owner-data traffic."""

import copy
import json

import httpx
import openai
import pytest
from pydantic import BaseModel

from jobcu.ai.base import AIInvalidOutput, AIOutputTruncated, AIRefused, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.compatible_adapter import CompatibleAdapter
from jobcu.ai.usage import UsageLog
from jobcu.settings import AISettings, Settings


def response():
    return {"id": "chat_fictional", "object": "chat.completion", "created": 1,
        "model": "fictional-model", "choices": [{"index": 0, "finish_reason": "stop",
        "message": {"role": "assistant", "content": '{"ok":true}'}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                  "prompt_tokens_details": {"cached_tokens": 2},
                  "completion_tokens_details": {"reasoning_tokens": 3}}}


@pytest.fixture
def service():
    clients = []
    CompatibleAdapter._mode_cache.clear()

    def make(payload):
        requests = []
        adapter = CompatibleAdapter("fictional-key", base_url="https://provider.example/v1")

        def handle(request):
            requests.append(json.loads(request.content))
            value = payload[len(requests) - 1] if isinstance(payload, list) else payload
            return httpx.Response(200, json=value)

        sdk = openai.OpenAI(api_key="fictional-key", base_url=adapter.base_url, max_retries=0,
                            http_client=httpx.Client(transport=httpx.MockTransport(handle)))
        adapter._sdk_client = sdk
        clients.append(sdk)
        return adapter, requests

    yield make
    for sdk in clients:
        sdk.close()
    CompatibleAdapter._mode_cache.clear()


def ask(adapter):
    return adapter.complete_json(model="fictional-model", system="Fictional rules",
        prompt="Fictional nursing capacity", schema={"type": "object"}, schema_name="Fit",
        effort="medium", max_output_tokens=16000)


@pytest.mark.parametrize("missing", ["usage", "prompt_tokens", "completion_tokens"])
def test_missing_usage_is_unknown_while_available_counts_and_answer_survive(service, missing):
    value = response()
    if missing == "usage":
        del value[missing]
    else:
        del value["usage"][missing]
    adapter, requests = service(value)
    reply = ask(adapter)
    assert reply.text == '{"ok":true}' and len(requests) == 1
    assert reply.usage.unreported_requests == 1
    if missing != "usage":
        assert reply.usage.cached_input_tokens == 2 and reply.usage.reasoning_tokens == 3
        assert reply.usage.input_tokens == (0 if missing == "prompt_tokens" else 10)
        assert reply.usage.output_tokens == (0 if missing == "completion_tokens" else 5)


@pytest.mark.parametrize("finish,refusal,empty,expected", [
    ("length", False, False, AIOutputTruncated),
    ("content_filter", False, False, AIRefused),
    ("stop", True, False, AIRefused),
    ("tool_calls", False, False, AIInvalidOutput),
    ("function_call", False, False, AIInvalidOutput),
    (None, False, False, AIInvalidOutput),
    ("stop", False, True, AIInvalidOutput),
])
def test_nonanswers_never_pass_as_completed_facts_and_keep_receipts(
        service, finish, refusal, empty, expected):
    value = response()
    value["choices"][0]["finish_reason"] = finish
    if refusal:
        value["choices"][0]["message"]["refusal"] = "Fictional refusal"
    if empty:
        value["choices"] = []
    adapter, requests = service(value)
    with pytest.raises(expected) as caught:
        ask(adapter)
    assert caught.value.usage == Usage(10, 5, 2, 3)
    assert len(requests) == 1


class Fit(BaseModel):
    ok: bool


def configured_settings():
    return Settings(ai=AISettings(provider="openai_compatible", model="fictional-model",
        base_url="https://provider.example/v1", compatible_protocol="chat_completions"))


def test_bounded_truncation_repair_records_both_receipts_once_without_dropping_medium(service):
    first = response()
    first["choices"][0]["finish_reason"] = "length"
    second = copy.deepcopy(first)
    second["choices"][0]["finish_reason"] = "stop"
    adapter, requests = service([first, second])
    log = UsageLog()
    client = AIClient(configured_settings(), adapter=adapter, usage_log=log)
    assert client.generate(Fit, step="scoring", system="Fictional rules",
                           prompt="Fictional electronics role").ok
    assert log.this_month()[0].usage == Usage(20, 10, 4, 6)
    assert [r["max_tokens"] for r in requests] == [16000, 20000]
    assert all(r["reasoning_effort"] == "medium" for r in requests)
    assert all(r["response_format"]["type"] == "json_schema" for r in requests)


def test_completed_answer_without_usage_stays_usable_and_the_missing_bill_stays_visible(service):
    value = response()
    value.pop("usage")
    adapter, requests = service(value)
    log, notes = UsageLog(), []
    client = AIClient(configured_settings(), adapter=adapter, usage_log=log, notify=notes.append)
    assert client.generate(Fit, step="scoring", system="Fictional rules",
                           prompt="Fictional teacher role").ok
    assert log.this_month()[0].usage == Usage(unreported_requests=1)
    assert any("did not report complete usage" in note for note in notes)
    assert len(requests) == 1


def test_an_explicit_complete_zero_receipt_is_not_mistaken_for_a_missing_bill(service):
    value = response()
    value["usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    adapter, _ = service(value)
    assert ask(adapter).usage == Usage()


@pytest.mark.parametrize("message", [None, {"role": "assistant", "content": [{"text": "x"}]},
    {"role": "assistant", "content": '{"ok":true}',
     "tool_calls": [{"id": "tool_fictional", "type": "function",
                     "function": {"name": "fictional", "arguments": "{}"}}]}])
def test_an_invalid_message_or_unrequested_tool_call_is_terminal_with_its_bill(service, message):
    value = response()
    value["choices"][0]["message"] = message
    adapter, requests = service(value)
    with pytest.raises(AIInvalidOutput) as caught:
        ask(adapter)
    assert caught.value.usage == Usage(10, 5, 2, 3)
    assert len(requests) == 1
