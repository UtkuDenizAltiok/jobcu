"""Real SDK/SSE serialization with fictional data and no network or provider calls."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from google import genai
from google.genai import types
from pydantic import BaseModel

from jobcu.ai.base import AIOutputTruncated, AIRefused, AIUnavailable, Usage
from jobcu.ai.client import AIClient
from jobcu.ai.gemini_adapter import GeminiAdapter
from jobcu.settings import Settings


class Events(httpx.SyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.closed = False

    def __iter__(self):
        for chunk in self.chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield ("data: " + json.dumps(chunk) + "\n\n").encode("utf-8")

    def close(self):
        self.closed = True


@pytest.fixture
def service():
    clients = []

    def make(*attempts):
        streams = [Events(chunks) for chunks in attempts]
        requests = []

        def handle(request):
            requests.append({"path": request.url.path, "body": json.loads(request.content)})
            assert request.url.path.endswith(":streamGenerateContent")
            return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
                                  stream=streams[len(requests) - 1])

        adapter = GeminiAdapter("fictional-key")
        client = genai.Client(api_key="fictional-key", http_options=types.HttpOptions(
            client_args={"transport": httpx.MockTransport(handle),
                         "event_hooks": {"response": [adapter._capture_response]}},
            retry_options=types.HttpRetryOptions(attempts=1)))
        clients.append(client)
        adapter._genai_client = client
        return adapter, requests, streams

    yield make
    for client in clients:
        client.close()


def chunk(text=None, *, finish=None, grounding=None, thought=False, usage=None):
    candidate = {}
    if text is not None:
        candidate["content"] = {"parts": [{"text": text, "thought": thought}], "role": "model"}
    if finish:
        candidate["finishReason"] = finish
    if grounding:
        candidate["groundingMetadata"] = grounding
    response = {"candidates": [candidate]} if candidate else {}
    if usage:
        response["usageMetadata"] = usage
    return response


def generate(adapter):
    return adapter.complete_json(model="fictional-model", system="Compare the stated evidence",
                                 prompt="Fictional documents and ad", schema={"type": "object"},
                                 schema_name="Fit", effort="medium", max_output_tokens=16000)


def research(adapter):
    return adapter.research(model="fictional-model", system="Find original evidence",
                            prompt="Fictional ad", max_searches=4, max_output_tokens=6000,
                            effort="medium")


@pytest.mark.parametrize("profession", ["nurse", "teacher", "electronics engineer"])
def test_fragmented_json_keeps_full_evidence_medium_and_final_usage(service, profession):
    text = json.dumps({"profession": profession, "requirement": "registration unknown",
                       "town": "München"}, ensure_ascii=False)
    adapter, requests, streams = service([
        chunk("internal reasoning", thought=True),
        chunk(text[:15], usage={"promptTokenCount": 100, "candidatesTokenCount": 2}),
        chunk(text[15:]), chunk(finish="STOP"),
        chunk(usage={"promptTokenCount": 100, "candidatesTokenCount": 30,
                     "thoughtsTokenCount": 50, "cachedContentTokenCount": 10}),
    ])
    reply = generate(adapter)
    assert reply.text == text
    assert reply.usage == Usage(100, 80, 10, 50)
    assert len(requests) == 1 and streams[0].closed
    config = requests[0]["body"]["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == {"type": "object"}
    thinking = config["thinkingConfig"]
    assert thinking.get("thinkingLevel", thinking.get("thinking_level")) == "MEDIUM"
    assert config["maxOutputTokens"] == 16000
    assert "tools" not in requests[0]["body"]


def test_research_retains_late_sources_query_multiplicity_and_cumulative_usage(service):
    first = {"webSearchQueries": ["fictional qualification"], "groundingChunks": [
        {"web": {"uri": "https://example.org/ad", "title": "Original ad"}}]}
    final = {"webSearchQueries": ["fictional qualification", "fictional qualification",
                                  "fictional town"], "groundingChunks": [
        {"web": {"uri": "https://example.org/ad", "title": "Original ad"}},
        {"web": {"uri": "https://example.org/town", "title": "Town"}}]}
    adapter, requests, streams = service([
        chunk("JOB J0\n", grounding=first, usage={"promptTokenCount": 100}),
        chunk("Registration required; town unknown.", grounding=final, finish="STOP",
              usage={"promptTokenCount": 100, "candidatesTokenCount": 20,
                     "thoughtsTokenCount": 40}),
        chunk(usage={"promptTokenCount": 100, "candidatesTokenCount": 20,
                     "thoughtsTokenCount": 40}),
    ])
    reply = research(adapter)
    assert reply.text == "JOB J0\nRegistration required; town unknown."
    assert [source.url for source in reply.sources] == [
        "https://example.org/ad", "https://example.org/town"]
    assert reply.usage == Usage(100, 60, reasoning_tokens=40, web_searches=3)
    body = requests[0]["body"]
    assert body["tools"] == [{"googleSearch": {}}]
    thinking = body["generationConfig"]["thinkingConfig"]
    assert thinking.get("thinkingLevel", thinking.get("thinking_level")) == "MEDIUM"
    assert streams[0].closed


@pytest.mark.parametrize("call", [generate, research])
@pytest.mark.parametrize("finish,error", [
    ("MAX_TOKENS", AIOutputTruncated), ("SAFETY", AIRefused), ("OTHER", AIRefused)])
def test_failed_terminal_status_never_returns_partial_evidence(service, call, finish, error):
    adapter, _, streams = service([chunk('{"ok": true}'), chunk(finish=finish)])
    with pytest.raises(error):
        call(adapter)
    assert streams[0].closed


@pytest.mark.parametrize("call", [generate, research])
@pytest.mark.parametrize("chunks", [[], [chunk('{"ok": true}')]])
def test_silent_eof_is_not_a_complete_answer_even_when_text_looks_valid(service, call, chunks):
    adapter, _, streams = service(chunks)
    with pytest.raises(AIUnavailable):
        call(adapter)
    assert streams[0].closed


@pytest.mark.parametrize("call", [generate, research])
def test_blocked_prompt_closes_stream_without_using_later_text(service, call):
    adapter, _, streams = service([
        {"promptFeedback": {"blockReason": "SAFETY"}},
        chunk('{"ok": true}', finish="STOP"),
    ])
    with pytest.raises(AIRefused):
        call(adapter)
    assert streams[0].closed


class Fit(BaseModel):
    requirement: str


def test_disconnection_retries_a_fresh_complete_answer(service):
    adapter, requests, streams = service(
        [chunk('{"requirement":"met"}', usage={"promptTokenCount": 900}),
         httpx.RemoteProtocolError("fictional connection interruption")],
        [chunk('{"requirement":"unknown"}', finish="STOP",
               usage={"promptTokenCount": 100, "candidatesTokenCount": 20})],
    )
    settings = Settings()
    settings.ai.provider, settings.ai.model = "gemini", "fictional-model"
    waits = []
    client = AIClient(settings, adapter=adapter, sleep=waits.append)
    answer = client.generate(Fit, step="scoring", system="Fictional nurse",
                             prompt="Registration evidence missing")
    assert answer.requirement == "unknown"
    assert len(requests) == 2 and len(waits) == 1
    assert all(stream.closed for stream in streams)
    assert requests[0]["body"] == requests[1]["body"]


def test_closing_failed_stream_does_not_interrupt_another_request():
    together = threading.Barrier(2)
    failed_closed = threading.Event()

    class ConcurrentEvents(Events):
        def __iter__(self):
            together.wait(timeout=5)
            if self.chunks[0]["candidates"][0]["finishReason"] == "STOP":
                assert failed_closed.wait(timeout=5)
                assert not self.closed
            yield from super().__iter__()

        def close(self):
            super().close()
            if self.chunks[0]["candidates"][0]["finishReason"] == "MAX_TOKENS":
                failed_closed.set()

    bad = ConcurrentEvents([chunk("partial", finish="MAX_TOKENS")])
    good = ConcurrentEvents([chunk('{"requirement":"unknown"}', finish="STOP")])
    adapter = GeminiAdapter("fictional-key")

    def handle(request):
        prompt = json.loads(request.content)["contents"][0]["parts"][0]["text"]
        return httpx.Response(200, headers={"Content-Type": "text/event-stream"},
                              stream=bad if prompt == "bad" else good)

    with genai.Client(api_key="fictional-key", http_options=types.HttpOptions(client_args={
            "transport": httpx.MockTransport(handle),
            "event_hooks": {"response": [adapter._capture_response]}})) as sdk:
        adapter._genai_client = sdk

        def ask(prompt):
            return adapter.complete_json(model="fictional-model", system="Fictional teacher",
                                         prompt=prompt, schema={"type": "object"},
                                         schema_name="Fit", effort="medium", max_output_tokens=500)

        with ThreadPoolExecutor(max_workers=2) as pool:
            bad_result, good_result = pool.submit(ask, "bad"), pool.submit(ask, "good")
            with pytest.raises(AIOutputTruncated):
                bad_result.result(timeout=5)
            assert good_result.result(timeout=5).text == '{"requirement":"unknown"}'
    assert bad.closed and good.closed
