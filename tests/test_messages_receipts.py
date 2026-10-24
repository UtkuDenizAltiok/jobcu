"""Fictional Messages responses through the installed SDK, without provider traffic."""

import json

import anthropic
import httpx2
import pytest

from jobcu.ai.anthropic_adapter import MAX_CONTINUATIONS, AnthropicAdapter, web_tools
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
    # A paused research turn is continued a bounded number of times, each receipt kept.
    sent = MAX_CONTINUATIONS + 1 if research and stop == "pause_turn" else 1
    assert caught.value.usage == Usage(10 * sent, 5 * sent, 2 * sent,
                                       web_searches=int(research) * sent)
    assert len(requests) == sent


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


def sequence(values):
    """An adapter whose fictional service answers each request with the next value."""
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        value = values[min(len(requests) - 1, len(values) - 1)]
        return value if isinstance(value, httpx2.Response) else httpx2.Response(200, json=value)

    adapter = AnthropicAdapter("fictional-key")
    adapter._sdk_client = anthropic.Anthropic(
        api_key="fictional-key", max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)))
    return adapter, requests


FETCHED = {"type": "web_fetch_tool_result", "tool_use_id": "srvtoolu_fictional",
           "content": {"type": "web_fetch_result", "url": "https://jobs.example.test/ad/7",
                       "retrieved_at": "2026-10-23T10:00:00Z",
                       "content": {"type": "document", "title": "Fictional nurse vacancy",
                                   "source": {"type": "text", "media_type": "text/plain",
                                              "data": "NMBI registration is required."},
                                   "citations": {"enabled": True}}}}
FETCH_CALL = {"type": "server_tool_use", "id": "srvtoolu_fictional", "name": "web_fetch",
              "input": {"url": "https://jobs.example.test/ad/7"}}


def cited(text, **citation):
    return {"type": "text", "text": text, "citations": [{
        "type": "char_location", "document_index": 0, "start_char_index": 0,
        "end_char_index": 30, "cited_text": "NMBI registration is required.", **citation}]}


@pytest.mark.parametrize("model,dynamic", [
    ("claude-haiku-5-5", False), ("claude-sonnet-5-5", True), ("claude-opus-4-6", True),
    ("claude-sonnet-4-5-20250929", False), ("claude-fable-5-1", True), ("fictional", False)])
def test_web_tools_use_each_models_newest_supported_versions_within_the_allowance(
        model, dynamic):
    search, fetch = web_tools(model, 6)
    assert search == {"type": "web_search_20260209" if dynamic else "web_search_20250305",
                      "name": "web_search", "max_uses": 6}
    assert fetch["type"] == ("web_fetch_20260209" if dynamic else "web_fetch_20250910")
    assert fetch["citations"] == {"enabled": True} and fetch["max_content_tokens"] > 0


def test_paused_research_resumes_its_own_turn_and_links_fetched_passages():
    paused = response(stop="pause_turn", searches=1)
    paused["content"] = [FETCH_CALL, FETCHED]
    done = response(searches=1)
    done["content"] = [cited("The fictional ad requires NMBI registration.")]
    adapter, requests = sequence([paused, done])
    reply = ask(adapter, research=True)
    assert len(requests) == 2 and requests[1]["messages"][0] == requests[0]["messages"][0]
    resumed = requests[1]["messages"][1]
    assert resumed["role"] == "assistant" and [b["type"] for b in resumed["content"]] == [
        "server_tool_use", "web_fetch_tool_result"]
    assert reply.usage == Usage(20, 10, 4, web_searches=2)
    assert [s.url for s in reply.sources] == ["https://jobs.example.test/ad/7"]
    assert [(c.text, c.url) for c in reply.citations] == [
        ("The fictional ad requires NMBI registration.", "https://jobs.example.test/ad/7")]


@pytest.mark.parametrize("change", [{"document_index": 3}, {"document_title": "Another ad"}])
def test_a_citation_that_cannot_be_traced_to_a_fetched_page_is_not_linked(change):
    done = response(searches=1)
    done["content"] = [FETCH_CALL, FETCHED, cited("A fictional claim.", **change)]
    adapter, _ = sequence([done])
    reply = ask(adapter, research=True)
    assert reply.citations == [] and [s.url for s in reply.sources] == [
        "https://jobs.example.test/ad/7"]


def test_refused_fetch_tool_falls_back_to_basic_search_before_any_paid_work():
    refused = httpx2.Response(400, json={"type": "error", "error": {
        "type": "invalid_request_error", "message": "web fetch is not enabled"}})
    adapter, requests = sequence([refused, response(searches=1)])
    reply = ask(adapter, research=True)
    assert reply.usage.web_searches == 1 and len(requests) == 2
    assert [t["name"] for t in requests[1]["tools"]] == ["web_search"]
    assert requests[1]["tools"][0]["max_uses"] == 3
