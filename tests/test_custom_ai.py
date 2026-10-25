"""Fictional requests through real SDK serialization; no provider traffic or saved keys."""

import json

import anthropic
import httpx
import httpx2
import openai
import pytest
from streams import as_stream
from test_ai_client import GOOD, Answer, ScriptedAdapter, SearchingAdapter

from jobcu.ai.base import (
    AIAuthError,
    AIBadRequest,
    AILimitReached,
    AIModelNotFound,
    AIRateLimited,
    AIUnavailable,
    AIWebSearchUnavailable,
)
from jobcu.ai.client import AIClient, check_research_setup
from jobcu.ai.compatible_adapter import (
    CompatibleAdapter,
    CompatibleMessagesAdapter,
    CompatibleResponsesAdapter,
    OpenRouterAdapter,
)
from jobcu.ai.providers import configured_adapter
from jobcu.ai.usage import UsageLog
from jobcu.keystore import KeyStore
from jobcu.settings import AISettings, Settings


@pytest.fixture(autouse=True)
def forget_custom_formats():
    CompatibleAdapter._mode_cache.clear()
    CompatibleAdapter._reasons_only_by_choice.clear()
    yield
    CompatibleAdapter._mode_cache.clear()
    CompatibleAdapter._reasons_only_by_choice.clear()


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
    transport = httpx.MockTransport(lambda request: as_stream(request, handler(request)))
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


def router_client(handle, base_url="https://openrouter.ai/api/v1"):
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional/model",
                             base_url=base_url)
    adapter = configured_adapter("openai_compatible", "fake-router-key", settings.ai)
    sdk_transport(adapter, "chat_completions", handle)
    return AIClient(settings, adapter=adapter, usage_log=UsageLog())


@pytest.mark.parametrize("base_url,routed", [("https://openrouter.ai/api/v1", True),
                                             ("https://provider.example/v1", False)])
def test_router_requests_require_private_hosts_that_honour_every_parameter(base_url, routed):
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply_for("chat_completions"))

    assert router_client(handle, base_url).generate(
        Answer, step="scoring", system="Rules", prompt="Fictional teacher").ok
    expected = {"data_collection": "deny", "zdr": True, "require_parameters": True}
    assert bodies[0].get("provider") == (expected if routed else None)
    assert bodies[0]["response_format"]["type"] == "json_schema"


def test_router_without_a_schema_host_keeps_privacy_and_uses_plain_json():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        if len(bodies) == 1:
            return httpx.Response(404, json={"error": {
                "message": "No endpoints found that can handle the requested parameters.",
                "code": 404}})
        return httpx.Response(200, json=reply_for("chat_completions"))

    assert router_client(handle).generate(
        Answer, step="scoring", system="Rules", prompt="Fictional chef").ok
    assert [b["response_format"]["type"] for b in bodies] == ["json_schema", "json_object"]
    assert all(b["provider"]["zdr"] is True for b in bodies)


def test_a_router_model_no_host_serves_with_jobcu_s_controls_is_named_truthfully():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(404, json={"error": {
            "message": "No endpoints found that can handle the requested parameters.",
            "code": 404}})

    settings = Settings()
    settings.ai = AISettings(provider="openrouter", model="fictional/plain-model")
    adapter = configured_adapter("openrouter", "fake-router-key", settings.ai)
    sdk_transport(adapter, "chat_completions", handle)
    client = AIClient(settings, adapter=adapter, usage_log=UsageLog())
    with pytest.raises(AIModelNotFound, match="reasoning setting") as refused:
        client.generate(Answer, step="scoring", system="Rules", prompt="Fictional welder")
    assert "doesn't know this model" not in refused.value.message
    assert [b.get("response_format", {}).get("type") for b in bodies] == [
        "json_schema", "json_object", None]
    assert all(b["reasoning"] == {"effort": "medium"} for b in bodies)  # never quietly removed
    assert all("reasoning_effort" not in b for b in bodies)


def test_router_data_policy_refusal_is_never_negotiated_away():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(404, json={"error": {
            "message": "No endpoints found matching your data policy.", "code": 404}})

    with pytest.raises(AIModelNotFound, match="privacy requirements"):
        router_client(handle).generate(Answer, step="scoring", system="Rules",
                                       prompt="Fictional driver")
    assert len(bodies) == 1


def test_a_pinned_router_host_serves_every_request_without_fallback():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply_for("chat_completions"))

    client = router_client(handle)
    client.settings.ai.model = "fictional/model-1017@fictional-host"
    client._adapter = configured_adapter("openai_compatible", "fake-router-key",
                                         client.settings.ai)
    sdk_transport(client._adapter, "chat_completions", handle)
    assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional nurse").ok
    assert bodies[0]["model"] == "fictional/model-1017"
    assert bodies[0]["provider"] == {"data_collection": "deny", "zdr": True,
                                     "require_parameters": True,
                                     "order": ["fictional-host"], "allow_fallbacks": False}


def test_at_signs_stay_part_of_model_names_on_other_hosts():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply_for("chat_completions"))

    client = router_client(handle, "https://provider.example/v1")
    client.settings.ai.model = "fictional-model@2026-10-17"
    client._adapter = configured_adapter("openai_compatible", "fake-key", client.settings.ai)
    sdk_transport(client._adapter, "chat_completions", handle)
    assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional cook").ok
    assert bodies[0]["model"] == "fictional-model@2026-10-17" and "provider" not in bodies[0]


def test_openrouter_needs_only_a_key_and_model_and_keeps_the_router_rules():
    # Other API's address and controls are left over on purpose: OpenRouter never uses them.
    settings = Settings()
    settings.ai = AISettings(provider="openrouter", model="fictional/model-1017@fictional-host",
                             base_url="https://provider.example/v1",
                             compatible_reasoning="provider_default")
    keys = KeyStore()
    keys.set("ai_openrouter", "fake-" + "r" * 20)
    client = AIClient(settings, keys, usage_log=UsageLog())
    adapter = client.adapter()
    assert isinstance(adapter, OpenRouterAdapter)
    requests = []

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json=reply_for("chat_completions"))

    sdk_transport(adapter, "chat_completions", handle)
    assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional baker").ok
    assert str(requests[0].url) == "https://openrouter.ai/api/v1/chat/completions"
    body = json.loads(requests[0].content)
    assert body["model"] == "fictional/model-1017"
    assert body["reasoning"] == {"effort": "medium"} and "reasoning_effort" not in body
    assert body["provider"] == {"data_collection": "deny", "zdr": True,
                                "require_parameters": True,
                                "order": ["fictional-host"], "allow_fallbacks": False}


def openrouter_client(handle):
    settings = Settings()
    settings.ai = AISettings(provider="openrouter", model="fictional/model@fictional-host")
    adapter = configured_adapter("openrouter", "fake-router-key", settings.ai)
    sdk_transport(adapter, "chat_completions", handle)
    return AIClient(settings, adapter=adapter, usage_log=UsageLog())


def router_reply(reasoning_tokens, completion_tokens=40):
    reply = reply_for("chat_completions")
    reply["usage"] = {**reply["usage"], "completion_tokens": completion_tokens,
                      "completion_tokens_details": {"reasoning_tokens": reasoning_tokens}}
    return reply


@pytest.mark.parametrize("loose_reasons", [True, False])
def test_a_router_host_that_drops_reasoning_with_a_json_format_is_asked_in_the_prompt(
        loose_reasons):
    bodies = []

    def handle(request):
        body = json.loads(request.content)
        bodies.append(body)
        constrained = "response_format" in body
        return httpx.Response(200, json=router_reply(
            0 if constrained or not loose_reasons else 30, 20 if constrained else 60))

    client = openrouter_client(handle)
    for _ in range(2):
        assert client.generate(Answer, step="scoring", system="Rules",
                               prompt="Fictional electrician").ok
    formats = [b.get("response_format", {}).get("type") for b in bodies]
    # The format that reasoned stays; a model that reasons in neither is not asked twice again.
    assert formats == (["json_schema", None, None] if loose_reasons
                       else ["json_schema", None, "json_schema"])
    assert "JSON schema" in bodies[1]["messages"][1]["content"]
    assert all(b["reasoning"] == {"effort": "medium"} for b in bodies)
    # Both requests of the check are paid and recorded.
    assert sum(u.usage.output_tokens for u in UsageLog().this_month()) == (
        20 + 60 + (60 if loose_reasons else 20))


def test_reasoning_is_not_rechecked_where_it_was_not_requested_or_is_not_reported():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=router_reply(0))

    # Another address asked for an effort: its reasoning report isn't known to be reliable.
    settings = Settings()
    settings.ai = AISettings(provider="openai_compatible", model="fictional-model",
                             base_url="https://provider.example/v1", compatible_reasoning="effort")
    adapter = configured_adapter("openai_compatible", "fake-key", settings.ai)
    sdk_transport(adapter, "chat_completions", handle)
    client = AIClient(settings, adapter=adapter, usage_log=UsageLog())
    assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional welder").ok
    assert bodies[-1]["reasoning_effort"] == "medium"
    # OpenRouter left to the provider's own reasoning default: nothing was asked for.
    client = router_client(handle)
    assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional welder").ok
    assert [b["response_format"]["type"] for b in bodies] == ["json_schema", "json_schema"]


def test_a_model_that_skips_reasoning_now_and_then_is_asked_again_each_time():
    bodies, schema_replies = [], iter([30, 0])

    def handle(request):
        body = json.loads(request.content)
        bodies.append(body)
        return httpx.Response(200, json=router_reply(
            next(schema_replies) if "response_format" in body else 25))

    client = openrouter_client(handle)
    for _ in range(3):
        assert client.generate(Answer, step="scoring", system="Rules", prompt="Fictional cook").ok
    assert [b.get("response_format", {}).get("type") for b in bodies] == [
        "json_schema", "json_schema", None, None]


def test_router_answers_stream_with_usage_and_other_addresses_stay_plain():
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply_for("chat_completions"))

    assert openrouter_client(handle).generate(Answer, step="scoring", system="Rules",
                                              prompt="Fictional nurse").ok
    assert router_client(handle, "https://provider.example/v1").generate(
        Answer, step="scoring", system="Rules", prompt="Fictional nurse").ok
    assert bodies[0]["stream"] is True and bodies[0]["stream_options"] == {"include_usage": True}
    assert "stream" not in bodies[1]
    usage = [u.usage for u in UsageLog().this_month()]
    assert usage[0].output_tokens == 5 and usage[0].reasoning_tokens == 3
    assert not usage[0].unreported_requests


def broken_stream(*events, then=None):
    def content():
        for event in events:
            yield f"data: {json.dumps(event)}\n\n".encode()
        if then is not None:
            raise then
    return httpx.Response(200, headers={"content-type": "text/event-stream"},
                          content=content())


@pytest.mark.parametrize(("ending", "error"), [
    ({"error": {"code": 502, "message": "Fictional provider failure"}}, AIUnavailable),
    ({"error": {"code": 429, "message": "Fictional rate limit"}}, AIRateLimited),
    (httpx.RemoteProtocolError("Fictional disconnect"), AIUnavailable),
])
def test_a_router_stream_that_breaks_keeps_its_unknown_bill(ending, error):
    first = {"id": "c", "object": "chat.completion.chunk", "created": 1, "model": "m",
             "choices": [{"index": 0, "delta": {"content": '{"ok": '}, "finish_reason": None}]}
    adapter = configured_adapter("openrouter", "fake-router-key",
                                 AISettings(provider="openrouter", model="fictional/model"))
    adapter._sdk_client = openai.OpenAI(
        api_key="fake", base_url=adapter.base_url, max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(lambda request: (
            broken_stream(first, ending) if isinstance(ending, dict)
            else broken_stream(first, then=ending)))))
    with pytest.raises(error) as caught:
        adapter.complete_json(model="fictional/model", system="Rules", prompt="Fictional chef",
                              schema={"type": "object"}, schema_name="Answer", effort=None,
                              max_output_tokens=1000)
    assert caught.value.usage.unreported_requests == 1  # work was done; its bill is unknown
