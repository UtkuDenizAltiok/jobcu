"""Fictional Messages responses through the installed SDK, without provider traffic."""

import json

import anthropic
import httpx2
import pytest

from jobcu.ai.anthropic_adapter import AnthropicAdapter
from jobcu.ai.base import AIInvalidOutput, AIOutputTruncated, AIRefused, Usage
from jobcu.ai.compatible_adapter import CompatibleMessagesAdapter


def response(*, stop="end_turn", searches=0):
    return {"id": "msg_fictional", "type": "message", "role": "assistant",
        "model": "fictional-model", "stop_reason": stop, "stop_sequence": None,
        "content": [{"type": "text", "text": '{"ok":true}'}],
        "usage": {"input_tokens": 7, "output_tokens": 5, "cache_read_input_tokens": 2,
                  "cache_creation_input_tokens": 1,
                  "server_tool_use": {"web_search_requests": searches}}}


@pytest.fixture
def service():
    clients = []

    def make(value, *, custom=False):
        cls = CompatibleMessagesAdapter if custom else AnthropicAdapter
        adapter = cls("fictional-key", base_url="https://provider.example")
        requests = []

        def handle(request):
            requests.append(json.loads(request.content))
            return httpx2.Response(200, json=value)

        sdk = anthropic.Anthropic(api_key="fictional-key", base_url=adapter.base_url,
            max_retries=0, http_client=httpx2.Client(transport=httpx2.MockTransport(handle)))
        adapter._sdk_client = sdk
        clients.append(sdk)
        return adapter, requests

    yield make
    for sdk in clients:
        sdk.close()


def ask(adapter, *, research=False):
    options = dict(model="fictional-model", system="Use only fictional evidence",
                   prompt="Fictional teaching capacity", effort="medium", max_output_tokens=16000)
    if research:
        return adapter.research(**options, max_searches=3)
    return adapter.complete_json(**options, schema={"type": "object"}, schema_name="Fit")


@pytest.mark.parametrize("custom,research", [(False, False), (True, False), (False, True)])
@pytest.mark.parametrize("stop,expected", [
    ("max_tokens", AIOutputTruncated), ("refusal", AIRefused),
    ("pause_turn", AIInvalidOutput), ("tool_use", AIInvalidOutput),
    ("model_context_window_exceeded", AIInvalidOutput), (None, AIInvalidOutput),
])
def test_unfinished_and_refused_messages_do_not_pass_as_facts_or_lose_their_receipt(
        service, custom, research, stop, expected):
    adapter, requests = service(response(stop=stop, searches=int(research)), custom=custom)
    with pytest.raises(expected) as caught:
        ask(adapter, research=research)
    assert caught.value.usage == Usage(10, 5, 2, web_searches=int(research))
    assert len(requests) == 1


@pytest.mark.parametrize("custom,research", [(False, False), (True, False), (False, True)])
@pytest.mark.parametrize("missing", ["usage", "input_tokens", "output_tokens"])
def test_completed_message_with_missing_counts_keeps_the_answer_and_marks_unknown_usage(
        service, custom, research, missing):
    value = response(searches=int(research))
    if missing == "usage":
        del value[missing]
    else:
        del value["usage"][missing]
    adapter, requests = service(value, custom=custom)
    reply = ask(adapter, research=research)
    assert reply.text == '{"ok":true}' and reply.usage.unreported_requests == 1
    assert len(requests) == 1
    if missing != "usage":
        assert reply.usage.input_tokens == (3 if missing == "input_tokens" else 10)
        assert reply.usage.output_tokens == (0 if missing == "output_tokens" else 5)
        assert reply.usage.cached_input_tokens == 2
        assert reply.usage.web_searches == int(research)


@pytest.mark.parametrize("custom", [False, True])
def test_completed_stop_sequences_keep_compatible_structured_answers(service, custom):
    value = response(stop="stop_sequence")
    value["stop_sequence"] = "fictional stop"
    adapter, requests = service(value, custom=custom)
    assert ask(adapter).usage == Usage(10, 5, 2)
    assert requests[0]["output_config"]["effort"] == "medium"


def test_completed_research_retains_sources_medium_and_the_web_use_ceiling(service):
    value = response(searches=1)
    value["content"][0]["citations"] = [{"type": "web_search_result_location",
        "url": "https://city.example.test/capacity", "title": "Fictional capacity",
        "cited_text": "Fictional city data", "encrypted_index": "fictional"}]
    adapter, requests = service(value)
    reply = ask(adapter, research=True)
    assert reply.text == '{"ok":true}' and reply.usage == Usage(10, 5, 2, web_searches=1)
    assert reply.sources[0].url == "https://city.example.test/capacity"
    assert requests[0]["output_config"] == {"effort": "medium"}
    assert requests[0]["tools"][0]["max_uses"] == 3
