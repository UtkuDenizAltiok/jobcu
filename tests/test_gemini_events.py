"""Exercise the locked native SDK over offline HTTP/SSE, including billing and failures."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from google import genai
from google.genai import types

from jobcu.ai.base import (
    AIAuthError,
    AIBadRequest,
    AIConnectionError,
    AIModelNotFound,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIReasoningUnsupported,
    AIRefused,
    AIUnavailable,
    AIUsageUncertain,
    AIWebSearchUnavailable,
    Usage,
)
from jobcu.ai.gemini_adapter import GeminiAdapter


class Events(httpx.SyncByteStream):
    def __init__(self, events):
        self.events, self.closed = events, False

    def __iter__(self):
        for event in self.events:
            if isinstance(event, Exception):
                raise event
            frame = ("data: " + json.dumps(event, ensure_ascii=False) + "\n\n").encode()
            # Actual byte fragmentation exercises the SDK's UTF-8/SSE decoder.
            for start in range(0, len(frame), 13):
                yield frame[start:start + 13]

    def close(self):
        self.closed = True


@pytest.fixture
def service():
    clients = []

    def make(*attempts):
        requests, streams = [], []
        adapter = GeminiAdapter("fictional-key")

        def handle(request):
            requests.append({"path": request.url.path, "body": json.loads(request.content)})
            assert request.url.path == "/v1beta/interactions"
            result = attempts[len(requests) - 1]
            if isinstance(result, Exception):
                raise result
            if isinstance(result, httpx.Response):
                return result
            stream = Events(result)
            streams.append(stream)
            return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
                                  stream=stream)

        client = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
            timeout=180000, retry_options=types.HttpRetryOptions(attempts=1),
            client_args={"transport": httpx.MockTransport(handle),
                         "event_hooks": {"response": [adapter._capture_response]}}))
        clients.append(client)
        adapter._genai_client = client
        return adapter, requests, streams

    yield make
    for client in clients:
        client.close()


def event(kind, **fields):
    return {"event_type": kind, **fields}


def start(index=0, kind="model_output", **fields):
    return event("step.start", index=index, step={"type": kind, **fields})


def text(words, index=0):
    return event("step.delta", index=index, delta={"type": "text", "text": words})


def done(*, status="completed", usage=True, steps=None):
    interaction = {"id": "fictional", "status": status}
    if usage:
        interaction["usage"] = {"total_input_tokens": 100, "total_output_tokens": 30,
                                "total_thought_tokens": 50, "total_cached_tokens": 10}
    if steps is not None:
        interaction["steps"] = steps
    return event("interaction.completed", interaction=interaction)


def generate(adapter):
    return adapter.complete_json(
        model="models/gemini-3.8-flash", system="Compare only the fictional evidence",
        prompt="Fictional vacancy", schema={"type": "object"}, schema_name="Fit",
        effort="medium", max_output_tokens=16000)


def research(adapter, model="gemini-3.8-flash"):
    return adapter.research(model=model, system="Find original fictional evidence",
                            prompt="Fictional town library", effort="medium",
                            max_output_tokens=6000, max_searches=4)


@pytest.mark.parametrize("ending", [
    event("interaction.status_update", status="failed"),
    event("error", error={"code": "service_unavailable", "message": "Fictional outage"}),
])
def test_failed_research_after_native_search_activity_does_not_repeat_without_a_bill(
        service, ending):
    from jobcu.ai.client import AIClient
    from jobcu.ai.usage import UsageLog
    from jobcu.settings import Settings

    adapter, requests, streams = service([
        start(0, "google_search_call", arguments={"queries": ["fictional city", "library"]}),
        event("step.stop", index=0, usage={"total_input_tokens": 12}), ending,
    ], [start(), text("An automatically repeated answer"), done()])
    configured = Settings()
    configured.ai.provider, configured.ai.model = "gemini", "gemini-3.8-flash"
    ledger, waits = UsageLog(), []
    client = AIClient(configured, adapter=adapter, usage_log=ledger, sleep=waits.append)
    for prompt in ("Fictional city library", "Another fictional city"):
        with pytest.raises(AIUsageUncertain):
            client.research(step="location", system="Use sourced evidence", prompt=prompt)
    assert len(requests) == 1 and streams[0].closed and not waits
    assert ledger.this_month()[0].usage == Usage(
        input_tokens=12, web_searches=2, unreported_requests=1)
    assert client._web_searches_reserved == 0


@pytest.mark.parametrize("profession", ["electronics engineer", "nurse", "teacher"])
def test_stateless_stream_preserves_evidence_effort_and_one_complete_receipt(service, profession):
    answer = json.dumps({"profession": profession, "town": "Münchendorf"}, ensure_ascii=False)
    adapter, requests, streams = service([
        event("interaction.created", interaction={"id": "fictional", "status": "in_progress"}),
        start(0, "thought"), event("step.delta", index=0, delta={"type": "thought_summary",
            "content": {"type": "text", "text": "PRIVATE_THOUGHT"}}),
        start(1), text(answer[:9], 1), text(answer[9:], 1), done(),
        httpx.RemoteProtocolError("A late body close cannot undo completed generation"),
    ])
    reply = generate(adapter)
    assert reply.text == answer
    assert reply.usage == Usage(100, 80, 10, 50)
    assert len(requests) == 1 and streams[0].closed
    body = requests[0]["body"]
    assert body["model"] == "gemini-3.8-flash"
    assert body["store"] is body["background"] is False and body["stream"] is True
    assert "previous_interaction_id" not in body and "tools" not in body
    assert body["generation_config"] == {
        "max_output_tokens": 16000, "thinking_level": "medium", "thinking_summaries": "auto"}
    assert body["response_format"] == {
        "type": "text", "mime_type": "application/json", "schema": {"type": "object"}}


def test_byte_citations_queries_and_late_metadata_are_preserved_without_guessing(service):
    prefix, words = "CITY C0 — Münchendorf\n", "Its fictional library opens on Sundays."
    notes = prefix + words
    valid = {"type": "url_citation", "url": "https://example.test/library", "title": "Library",
             "start_index": len(prefix.encode()), "end_index": len(notes.encode())}
    adapter, requests, streams = service([
        start(0, "google_search_call", id="search0", arguments={"queries": ["fictional library"]}),
        event("step.delta", index=0, delta={"type": "google_search_call",
              "arguments": {"queries": ["fictional library", "fictional opening"]}}),
        start(1), text(notes[:14], 1), text(notes[14:], 1),
        event("step.delta", index=1, delta={"type": "text_annotation_delta", "annotations": [
            valid, {**valid, "start_index": -1}, {**valid, "end_index": 99999},
            {**valid, "start_index": notes.encode().index("ü".encode()) + 1},
        ]}), done(),
    ])
    reply = research(adapter)
    assert reply.text == notes
    assert [(c.text, c.url) for c in reply.citations] == [(words, valid["url"])]
    assert [s.url for s in reply.sources] == [valid["url"]]
    assert reply.usage == Usage(100, 80, 10, 50, web_searches=2)
    assert requests[0]["body"]["tools"] == [{"type": "google_search"}]
    assert "response_format" not in requests[0]["body"]
    assert len(requests) == 1 and streams[0].closed


@pytest.mark.parametrize("model,searches", [("gemini-2.5-flash", 1), ("gemini-3.8-flash", 2)])
def test_canonical_completion_does_not_double_text_or_native_query_usage(service, model, searches):
    step = {"type": "google_search_call", "id": "q", "arguments": {
        "queries": ["", "fictional library", "fictional library", "fictional opening"]}}
    adapter, _, _ = service([
        start(0), text("Fictional result"), done(steps=[step, {
            "type": "model_output", "content": [{"type": "text", "text": "Fictional result"}]}]),
    ])
    reply = research(adapter, model)
    assert reply.text == "Fictional result" and reply.usage.web_searches == searches


@pytest.mark.parametrize("events", [[], [start(), text('{"ok":true}')]])
def test_eof_or_missing_terminal_never_returns_a_valid_partial_answer(service, events):
    adapter, requests, streams = service(events)
    with pytest.raises(AIUnavailable) as caught:
        generate(adapter)
    assert caught.value.usage.unreported_requests == 1
    assert len(requests) == 1 and streams[0].closed


@pytest.mark.parametrize("research_path", [False, True])
@pytest.mark.parametrize("partial", [False, True])
def test_silent_eof_stops_client_repetition_of_possibly_billed_work(
    service, research_path, partial
):
    from pydantic import BaseModel

    from jobcu.ai.client import AIClient
    from jobcu.ai.usage import UsageLog
    from jobcu.settings import Settings

    class Answer(BaseModel):
        ok: bool

    first = [start(), text('{"ok":true}')] if partial else []
    adapter, requests, streams = service(first, [start(), text('{"ok":true}'), done()])
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "gemini-3.8-flash"
    ledger, waits = UsageLog(), []
    client = AIClient(settings, adapter=adapter, usage_log=ledger, sleep=waits.append)

    def ask():
        if research_path:
            return client.research(step="location_research", system="Use original evidence",
                                   prompt="Fictional library service")
        return client.generate(Answer, step="scoring", system="Use stated evidence",
                               prompt="Fictional applicant and vacancy")

    for _ in range(2):
        with pytest.raises(AIConnectionError) as caught:
            ask()
        assert caught.value.request_sent is True
    assert len(requests) == len(streams) == 1 and streams[0].closed
    assert not waits and ledger.this_month()[0].usage.unreported_requests == 1
    assert requests[0]["body"]["generation_config"]["thinking_level"] == "medium"


def test_missing_final_receipt_is_explicit_without_repeating_completed_work(service):
    adapter, requests, _ = service([start(), text('{"ok":true}'), done(usage=False)])
    reply = generate(adapter)
    assert json.loads(reply.text) == {"ok": True} and reply.usage.unreported_requests == 1
    assert len(requests) == 1


def test_unreported_query_count_is_not_a_complete_bill(service):
    adapter, requests, _ = service([
        start(0, "google_search_call", id="q", arguments={"queries": []}),
        start(1), text("Fictional answer", 1), done(),
    ])
    reply = research(adapter)
    assert reply.usage.web_searches == 1 and reply.usage.unreported_requests == 1
    assert len(requests) == 1


def test_native_search_count_and_partial_token_receipts_survive_failure(service):
    adapter, requests, _ = service([
        start(0, "google_search_call", id="q", arguments={"queries": ["fictional"]}),
        event("step.delta", index=0, delta={"type": "google_search_call", "arguments": {}},
              metadata={"total_usage": {"total_input_tokens": 20, "total_output_tokens": 10,
                        "total_thought_tokens": 5,
                        "grounding_tool_count": [{"type": "google_search", "count": 3}]}}),
        httpx.RemoteProtocolError("Fictional body interruption"),
    ])
    with pytest.raises(AIConnectionError) as caught:
        research(adapter)
    assert caught.value.usage == Usage(20, 15, reasoning_tokens=5, web_searches=3,
                                      unreported_requests=1)
    assert len(requests) == 1


@pytest.mark.parametrize("headers", [False, True])
def test_wrapped_disconnect_is_recognised_and_does_not_reveal_payloads(service, headers, caplog):
    failure = httpx.RemoteProtocolError("PRIVATE_TRANSPORT_DETAIL")
    attempt = [start(), text("PRIVATE_PARTIAL_TEXT"), failure] if headers else failure
    adapter, requests, streams = service(attempt)
    with caplog.at_level("INFO", logger="jobcu.ai.gemini_adapter"):
        with pytest.raises(AIConnectionError) as caught:
            generate(adapter)
    assert caught.value.usage.unreported_requests == 1 and len(requests) == 1
    assert f"headers_received={headers}" in caplog.text and "PRIVATE_" not in caplog.text
    assert not streams or streams[0].closed


@pytest.mark.parametrize("status,message,error", [
    (401, "Invalid API key", AIAuthError), (403, "Access denied", AIAuthError),
    (402, "Payment required", AIQuotaExhausted), (404, "Model not found", AIModelNotFound),
    (429, "Too many requests", AIRateLimited), (503, "Temporary outage", AIUnavailable),
    (400, "thinking_level is not supported for this model", AIReasoningUnsupported),
    (400, "thinking_level medium is unsupported", AIBadRequest),
])
def test_http_classification_and_exactly_one_sdk_dispatch(service, status, message, error):
    response = httpx.Response(status, json={"error": {"code": status, "message": message}})
    adapter, requests, _ = service(response)
    with pytest.raises(error):
        generate(adapter)
    assert len(requests) == 1  # the SDK's hidden retry would exhaust the mock responses


def test_search_capability_refusal_remains_distinct_from_a_connection_failure(service):
    response = httpx.Response(400, json={"error": {
        "code": 400, "message": "Google Search grounding is not available for this project"}})
    adapter, requests, _ = service(response)
    with pytest.raises(AIWebSearchUnavailable):
        research(adapter)
    assert len(requests) == 1


def test_plain_gateway_failure_does_not_become_an_invalid_request(service):
    adapter, requests, _ = service(httpx.Response(503, text="Fictional gateway unavailable"))
    with pytest.raises(AIUnavailable):
        generate(adapter)
    assert len(requests) == 1


def test_repeated_text_cannot_attach_one_annotation_to_different_claims(service):
    words = "Fictional library is open."
    content = {"type": "text", "text": words, "annotations": [{
        "type": "url_citation", "url": "https://example.test/library",
        "start_index": 0, "end_index": len(words.encode())}]}
    adapter, _, _ = service([done(steps=[
        {"type": "model_output", "content": [content, content]}])])
    reply = research(adapter)
    assert reply.text == words * 2 and reply.citations == []


def test_parallel_failure_closes_only_its_own_stream():
    barrier = threading.Barrier(2)
    streams, requests = [], []
    adapter = GeminiAdapter("fictional-key")

    class Together(Events):
        def __iter__(self):
            barrier.wait(timeout=5)
            yield from super().__iter__()

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        failure = body["input"] == "broken"
        ending = httpx.RemoteProtocolError("Fictional interruption") if failure else done()
        stream = Together([start(), text('{"ok":true}'), ending])
        streams.append(stream)
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"}, stream=stream)

    client = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1), client_args={
            "transport": httpx.MockTransport(handle),
            "event_hooks": {"response": [adapter._capture_response]}}))
    adapter._genai_client = client

    def run(prompt):
        try:
            return adapter.complete_json(
                model="gemini-3.8-flash", system="Fictional comparison", prompt=prompt,
                schema={"type": "object"}, schema_name="Fit", effort="medium",
                max_output_tokens=16000).text
        except AIConnectionError:
            return "interrupted"

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert list(executor.map(run, ["broken", "healthy"])) == [
                "interrupted", '{"ok":true}']
        assert len(requests) == 2 and all(stream.closed for stream in streams)
    finally:
        client.close()


@pytest.mark.parametrize("status,error", [
    ("incomplete", AIOutputTruncated), ("failed", AIUnavailable),
    ("cancelled", AIBadRequest), ("requires_action", AIBadRequest),
    ("budget_exceeded", AIQuotaExhausted),
])
def test_terminal_failure_never_accepts_schema_valid_partial_text(service, status, error):
    adapter, requests, streams = service([start(), text('{"ok":true}'), done(status=status)])
    with pytest.raises(error):
        generate(adapter)
    assert len(requests) == 1 and streams[0].closed


@pytest.mark.parametrize("status,error", [("incomplete", AIOutputTruncated),
                                         ("cancelled", AIBadRequest),
                                         ("budget_exceeded", AIQuotaExhausted)])
def test_failed_terminal_outcome_can_still_supply_a_complete_usage_receipt(service, status, error):
    adapter, requests, _ = service([start(), text('Partial fictional answer'), done(status=status)])
    with pytest.raises(error) as caught:
        generate(adapter)
    assert caught.value.usage == Usage(100, 80, 10, 50)
    assert len(requests) == 1


@pytest.mark.parametrize("code,error", [
    ("quota_exceeded", AIQuotaExhausted), ("rate_limit_exceeded", AIRateLimited),
    ("invalid_argument", AIBadRequest), ("content_filter", AIRefused),
])
def test_event_errors_keep_their_service_meaning(service, code, error):
    adapter, requests, _ = service([event("error", error={"code": code, "message": "Fictional"})])
    with pytest.raises(error):
        generate(adapter)
    assert len(requests) == 1


@pytest.mark.parametrize("code,error", [
    ("authentication", AIAuthError),
    ("parameter_unknown", AIBadRequest),
    ("failed_precondition", AIBadRequest),
    ("out_of_range", AIBadRequest),
    ("unimplemented", AIBadRequest),
    ("malformed_function_call", AIBadRequest),
    ("malformed_tool_call", AIBadRequest),
    ("unexpected_tool_call", AIBadRequest),
    ("too_many_tool_calls", AIBadRequest),
    ("missing_thought_signature", AIBadRequest),
    ("prohibited_content", AIRefused),
    ("spii", AIRefused),
    ("blocklist", AIRefused),
    ("content_blocked", AIRefused),
    ("language", AIRefused),
    ("future_unknown_parameter_failure", AIBadRequest),
])
def test_documented_terminal_event_errors_cannot_be_retried_as_outages(service, code, error):
    adapter, requests, _ = service([event("error", error={"code": code, "message": "Fictional"})])
    with pytest.raises(error) as caught:
        generate(adapter)
    assert not caught.value.retryable and len(requests) == 1


@pytest.mark.parametrize("missing", ["total_input_tokens", "total_output_tokens",
                                     "total_thought_tokens", "total_cached_tokens"])
def test_partial_final_usage_does_not_claim_a_complete_bill(service, missing):
    terminal = done()
    terminal["interaction"]["usage"].pop(missing)
    adapter, requests, _ = service([start(), text('{"ok":true}'), terminal])
    reply = generate(adapter)
    assert reply.text == '{"ok":true}' and reply.usage.unreported_requests == 1
    assert len(requests) == 1


def test_refusal_after_started_generation_preserves_missing_usage(service):
    adapter, requests, _ = service([start(), text('Partial fictional answer'),
        event("error", error={"code": "safety", "message": "Fictional refusal"})])
    with pytest.raises(AIRefused) as caught:
        generate(adapter)
    assert caught.value.usage and caught.value.usage.unreported_requests == 1
    assert len(requests) == 1
