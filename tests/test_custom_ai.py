"""Fictional requests through real SDK serialization; no provider traffic or saved keys."""

import json

import anthropic
import httpx
import httpx2
import openai
import pytest
from test_ai_client import GOOD, Answer, ScriptedAdapter, SearchingAdapter

from jobcu.ai.base import AIAuthError, AIBadRequest, AILimitReached, AIWebSearchUnavailable
from jobcu.ai.client import AIClient, check_research_setup
from jobcu.ai.compatible_adapter import (
    CompatibleAdapter,
    CompatibleMessagesAdapter,
    CompatibleResponsesAdapter,
)
from jobcu.ai.providers import configured_adapter
from jobcu.ai.usage import UsageLog
from jobcu.keystore import KeyStore
from jobcu.settings import AISettings, Settings


@pytest.fixture(autouse=True)
def forget_custom_formats():
    CompatibleAdapter._mode_cache.clear()
    yield
    CompatibleAdapter._mode_cache.clear()


def reply_for(protocol):
    if protocol == "responses":
        return {
            "id": "resp_fictional", "object": "response", "created_at": 1,
            "model": "fictional-model", "status": "completed",
            "output": [{"id": "msg_fictional", "type": "message", "role": "assistant",
                        "status": "completed", "content": [{"type": "output_text",
                                                             "text": GOOD, "annotations": []}]}],
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
                      "input_tokens_details": {"cached_tokens": 2},
                      "output_tokens_details": {"reasoning_tokens": 3}},
        }
    if protocol == "messages":
        return {
            "id": "msg_fictional", "type": "message", "role": "assistant",
            "model": "fictional-model", "stop_reason": "end_turn", "stop_sequence": None,
            "content": [{"type": "text", "text": GOOD}],
            "usage": {"input_tokens": 7, "output_tokens": 5, "cache_read_input_tokens": 2,
                      "cache_creation_input_tokens": 1},
        }
    return {
        "id": "chat_fictional", "object": "chat.completion", "created": 1,
        "model": "fictional-model",
        "choices": [{"index": 0, "finish_reason": "stop",
                     "message": {"role": "assistant", "content": GOOD}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                  "prompt_tokens_details": {"cached_tokens": 2},
                  "completion_tokens_details": {"reasoning_tokens": 3}},
    }


def sdk_transport(adapter, protocol, handler):
    transport = httpx.MockTransport(handler)
    if protocol == "messages":
        def handle_messages(request):
            response = handler(request)
            return httpx2.Response(response.status_code, content=response.content,
                                   headers=dict(response.headers))
        adapter._sdk_client = anthropic.Anthropic(
            api_key=adapter.api_key, base_url=adapter._messages_base(),
            http_client=httpx2.Client(transport=httpx2.MockTransport(handle_messages)),
            max_retries=0,
            default_headers=adapter._headers(),
        )
    else:
        adapter._sdk_client = openai.OpenAI(
            api_key=adapter.api_key, base_url=adapter.base_url,
            http_client=httpx.Client(transport=transport), max_retries=0,
            default_headers=adapter._headers(),
        )


@pytest.mark.parametrize("protocol", ["chat_completions", "responses", "messages"])
def test_custom_formats_use_chosen_host_key_schema_and_medium(protocol):
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional-model",
                             base_url="https://provider.example/v1",
                             compatible_protocol=protocol)
    adapter = configured_adapter("openai_compatible", "fake-custom-key", settings.ai)
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=reply_for(protocol))

    sdk_transport(adapter, protocol, handle)
    client = AIClient(settings, adapter=adapter, usage_log=UsageLog())
    assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional nurse").ok
    request = requests[0]
    body = json.loads(request.content)
    assert request.url.host == "provider.example"
    assert request.headers["user-agent"].startswith("Jobcu/")
    assert "x-opencode-session" not in request.headers
    assert body["model"] == "fictional-model"
    assert body.get("max_tokens", body.get("max_output_tokens")) == 16_000
    if protocol == "responses":
        assert request.url.path == "/v1/responses"
        assert request.headers["authorization"] == "Bearer fake-custom-key"
        assert body["reasoning"] == {"effort": "medium"}
        assert body["text"]["format"]["strict"] is True and body["store"] is False
    elif protocol == "messages":
        assert request.url.path == "/v1/messages"
        assert request.headers["x-api-key"] == "fake-custom-key"
        assert body["output_config"]["effort"] == "medium"
        assert body["output_config"]["format"]["type"] == "json_schema"
    else:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer fake-custom-key"
        assert body["reasoning_effort"] == "medium"
        assert body["response_format"]["json_schema"]["strict"] is True
    assert UsageLog().this_month()[0].usage.input_tokens == 10
    assert UsageLog().this_month()[0].usage.output_tokens == 5  # thinking not counted twice


@pytest.mark.parametrize(("control", "native"), [("effort", "high"), ("thinking", "medium"),
                                               ("provider_default", "medium")])
def test_chat_native_reasoning_controls_are_explicit_and_reported(control, native):
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional-model",
                             base_url="https://provider.example/v1",
                             compatible_protocol="chat_completions",
                             compatible_reasoning=control, compatible_medium=native)
    adapter = configured_adapter("openai_compatible", "fake-key", settings.ai)
    bodies, notes = [], []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply_for("chat_completions"))

    sdk_transport(adapter, "chat_completions", handle)
    client = AIClient(settings, adapter=adapter, notify=notes.append)
    for _ in range(2):
        client.generate(Answer, step="profile", system="Rules", prompt="Fictional teacher")
    assert len(notes) == 1
    if control == "effort":
        assert bodies[0]["reasoning_effort"] == "high" and "native mapping" in notes[0]
    elif control == "thinking":
        assert bodies[0]["thinking"] == {"type": "enabled"}
        assert "reasoning_effort" not in bodies[0] and "does not receive" in notes[0]
    else:
        assert "reasoning_effort" not in bodies[0] and "cannot confirm" in notes[0]


def test_format_negotiation_preserves_thinking_and_only_retries_format_errors():
    CompatibleAdapter._mode_cache.clear()
    adapter = CompatibleAdapter("fake-key", base_url="https://provider.example/v1")
    bodies = []

    def handle(request):
        body = json.loads(request.content)
        bodies.append(body)
        if len(bodies) == 1:
            return httpx.Response(400, json={"error": {"message": "json_schema unsupported"}})
        return httpx.Response(200, json=reply_for("chat_completions"))

    sdk_transport(adapter, "chat_completions", handle)
    adapter.complete_json(model="fictional-model", system="Rules", prompt="Fictional teacher",
                          schema={"type": "object"}, schema_name="Answer", effort="medium",
                          max_output_tokens=16_000)
    assert [b["response_format"]["type"] for b in bodies] == ["json_schema", "json_object"]
    assert all(b["reasoning_effort"] == "medium" for b in bodies)


@pytest.mark.parametrize("protocol", ["chat_completions", "responses", "messages"])
def test_rejected_custom_reasoning_is_not_silently_dropped(protocol):
    CompatibleAdapter._mode_cache.clear()
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional-model",
                             base_url="https://provider.example/v1", compatible_protocol=protocol)
    adapter = configured_adapter("openai_compatible", "fake-key", settings.ai)
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(400, json={"error": {"type": "invalid_request_error",
                                                  "message": "reasoning effort unsupported"}})

    sdk_transport(adapter, protocol, handle)
    with pytest.raises(AIBadRequest):
        AIClient(settings, adapter=adapter).generate(Answer, step="profile", system="s", prompt="p")
    assert len(requests) == 1


def test_gateway_session_is_stable_opaque_and_client_identifies_itself_honestly():
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional-model",
                             base_url="https://opencode.ai/zen/go/v1",
                             compatible_protocol="responses")
    client = AIClient(settings)
    first = client.adapter()
    assert isinstance(first, CompatibleResponsesAdapter)
    headers = first._headers()
    assert headers["x-opencode-session"] == client.adapter()._headers()["x-opencode-session"]
    assert headers["User-Agent"].startswith("Jobcu/")
    assert first._headers()["x-opencode-session"] != AIClient(settings).adapter()._headers()[
        "x-opencode-session"]


def test_explicit_research_uses_correct_native_key_and_ignores_custom_address():
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional-model",
                             base_url="https://provider.example/v1", compatible_protocol="messages",
                             research_provider="gemini", research_model="research-example")
    keys = KeyStore()
    keys.set("ai_openai_compatible", "fake-" + "c" * 20)
    keys.set("ai_gemini", "fake-" + "g" * 20)
    client = AIClient(settings, keys)
    assert isinstance(client.adapter(), CompatibleMessagesAdapter)
    assert client.adapter().api_key == keys.get("ai_openai_compatible")
    provider, model, research = client.research_endpoint()
    assert (provider, model) == ("gemini", "research-example")
    assert research.api_key == keys.get("ai_gemini") and research.base_url == ""


@pytest.mark.parametrize("model", ["", "research-example"])
def test_incomplete_research_configuration_never_falls_back_to_main(model):
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="main-example",
                             research_provider="gemini", research_model=model)
    main = ScriptedAdapter(GOOD)
    client = AIClient(settings, adapter=main)
    with pytest.raises(AIAuthError):
        client.research(step="location", system="s", prompt="p")
    assert not main.calls


@pytest.mark.parametrize("base", ["https://provider.example", "https://provider.example/v1/"])
def test_messages_sdk_creation_accepts_unversioned_and_versioned_base(base, monkeypatch):
    sdk = anthropic.Anthropic
    requests = []
    def handle(request):
        requests.append(request)
        return httpx2.Response(200, json=reply_for("messages"))
    def create(**kwargs):
        return sdk(**kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handle)))
    monkeypatch.setattr(anthropic, "Anthropic", create)
    adapter = CompatibleMessagesAdapter("fake-custom-key", base_url=base)
    adapter.complete_json(model="fictional-model", system="Fictional rules", prompt="Teacher",
                          schema={"type": "object"}, schema_name="Answer", effort="medium",
                          max_output_tokens=16_000)
    assert len(requests) == 1 and requests[0].url.path == "/v1/messages"


def test_mixed_research_then_extraction_keeps_one_ledger_and_limits():
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="main-example",
                             compatible_protocol="responses", research_provider="gemini",
                             research_model="research-example")
    settings.limits.web_search_cap = 3
    main, research = ScriptedAdapter(GOOD, GOOD), SearchingAdapter()
    usage = UsageLog()
    client = AIClient(settings, adapter=main, research_adapter=research,
                      usage_log=usage, search_id=8)
    client.research(step="job_places", system="Sources", prompt="Fictional nurse location")
    assert client.generate(Answer, step="job_places", system="Extract", prompt="Saved evidence").ok
    assert research.calls[0]["model"] == "research-example"
    assert research.calls[0]["effort"] == "medium"
    assert main.calls[0]["model"] == "main-example"
    with pytest.raises(AILimitReached):
        client.research(step="location", system="s", prompt="p")
    settings.limits.monthly_token_limit = 715
    with pytest.raises(AILimitReached):
        client.generate(Answer, step="scoring", system="s", prompt="p")
    assert len(main.calls) == len(research.calls) == 1
    rows = usage.this_month()
    assert {(row.provider, row.model) for row in rows} == {
        ("openai_compatible", "main-example"), ("gemini", "research-example")}


def test_research_unavailability_does_not_switch_provider_or_stop_generation():
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="main-example",
                             compatible_protocol="responses",
                             research_provider="gemini", research_model="research-example")

    class Refused(SearchingAdapter):
        def research(self, **request):
            self.calls.append(request)
            raise AIWebSearchUnavailable("Online access unavailable")

    main, research, notes = ScriptedAdapter(GOOD), Refused(), []
    client = AIClient(settings, adapter=main, research_adapter=research, notify=notes.append)
    for _ in range(2):
        with pytest.raises(AIWebSearchUnavailable):
            client.research(step="location", system="s", prompt="p")
    assert len(research.calls) == 1 and client.web_searches_left() > 0
    assert client.generate(Answer, step="scoring", system="s", prompt="p").ok
    assert notes == ["Online access unavailable"]


def test_research_connection_probe_has_correct_provider_and_preserves_settings():
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="main-example",
                             research_provider="gemini", research_model="research-example")
    before = settings.model_dump()
    usage = UsageLog()
    adapter = ScriptedAdapter(GOOD)
    result = check_research_setup(settings, adapter=adapter, usage_log=usage)
    assert result.ok and "permission was not tested" in result.message
    assert adapter.calls[0]["model"] == "research-example"
    assert usage.this_month()[0].provider == "gemini"
    assert settings.model_dump() == before
