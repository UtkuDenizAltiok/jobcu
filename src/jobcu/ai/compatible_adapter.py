"""Custom API addresses using Chat Completions, Responses or Messages.

These services differ in what they support. Chat format negotiates explicit schema
refusals through plain JSON and a schema prompt. Responses/Messages require native
schema support. Every answer is validated and chosen reasoning controls are preserved.
"""

import json
from typing import ClassVar
from urllib.parse import urlsplit
from uuid import uuid4

import anthropic
import openai

from jobcu import __version__
from jobcu.ai.anthropic_adapter import AnthropicAdapter
from jobcu.ai.base import (
    MSG_REFUSED,
    MSG_TRUNCATED,
    AIBadRequest,
    AIInvalidOutput,
    AIModelNotFound,
    AIOutputTruncated,
    AIRefused,
    ProviderAdapter,
    RawReply,
    Usage,
)
from jobcu.ai.openai_adapter import OpenAIAdapter, list_openai_style_models, translate_openai_error
from jobcu.settings import CompatibleReasoning, Effort

MODES = ("json_schema", "json_object", "prompt_only")
# A router picks the serving host per request. A CV and a job search may reach only hosts that
# neither keep nor train on request data, and that honour every requested parameter (the JSON
# schema and the reasoning effort), never a host that quietly ignores them.
ROUTER_REQUIREMENTS = {"openrouter.ai": {"provider": {
    "data_collection": "deny", "zdr": True, "require_parameters": True}}}


class _CustomEndpoint:
    def __init__(self, *args, session_id: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._session_id = session_id or str(uuid4())

    def _router_body(self, model: str = "") -> dict:
        """Router requirements; "model@host" also pins one serving host, with no fallback, so
        a test and later searches meet the same weights and quantization."""
        body = ROUTER_REQUIREMENTS.get(urlsplit(self.base_url).hostname or "")
        if body is None:
            return {}
        provider = dict(body["provider"])
        host = model.rpartition("@")[2] if "@" in model else ""
        if host:
            provider.update(order=[host], allow_fallbacks=False)
        return {**body, "provider": provider}

    def _model_name(self, model: str) -> str:
        """The router's own model name, without a pinned host."""
        return model.rpartition("@")[0] if self._router_body() and "@" in model else model

    def _headers(self) -> dict[str, str]:
        headers = {"User-Agent": f"Jobcu/{__version__}"}
        # A gateway-specific routing requirement, not a coding-client impersonation. The ID
        # lasts for this client/search only and contains no user, document or query identifier.
        if urlsplit(self.base_url).hostname == "opencode.ai":
            headers["x-opencode-session"] = self._session_id
        return headers


class CompatibleAdapter(_CustomEndpoint, ProviderAdapter):
    strict_reasoning = True
    formats = MODES
    # Remembers which mode worked for each (address, model) while Jobcu runs.
    _mode_cache: ClassVar[dict[tuple[str, str], str]] = {}

    _sdk_client: openai.OpenAI | None = None

    def __init__(self, *args, reasoning: CompatibleReasoning = "effort",
                 medium: str = "medium", **kwargs):
        super().__init__(*args, **kwargs)
        self.reasoning = reasoning
        self.medium = medium

    def _client(self) -> openai.OpenAI:
        with self._client_lock:
            if self._sdk_client is None:
                self._sdk_client = openai.OpenAI(
                    # Local services often need no key, but the library requires some value.
                    api_key=self.api_key or "not-needed",
                    base_url=self.base_url,
                    default_headers=self._headers(),
                    max_retries=0,
                    timeout=self.timeout,
                )
        return self._sdk_client

    def complete_json(
        self,
        *,
        model: str,
        system: str,
        prompt: str,
        schema: dict,
        schema_name: str,
        effort: Effort | None,
        max_output_tokens: int,
    ) -> RawReply:
        cache_key = (self.base_url, model)
        cached = self._mode_cache.get(cache_key, self.formats[0])
        start = self.formats.index(cached) if cached in self.formats else 0
        last_error: Exception | None = None
        for mode in self.formats[start:]:
            try:
                reply = self._request(mode, model, system, prompt, schema, schema_name,
                                      max_output_tokens, effort)
            except (AIBadRequest, AIModelNotFound) as exc:
                # Schema negotiation is not permission to retry an unrelated refusal or
                # discard thinking. Only an explicit format rejection changes format; for a
                # router, also "no host supports these parameters" (never its data policy).
                detail = exc.detail.lower()
                if self._router_body() and "data policy" in detail:
                    raise AIModelNotFound(
                        "No host for this model meets Jobcu's privacy requirements (no "
                        "training on and no retention of your documents). Choose another "
                        "model.", exc.detail) from exc
                router = bool(self._router_body()) and "requested parameters" in detail
                if not router and (isinstance(exc, AIModelNotFound) or not any(
                        word in detail for word in (
                            "response_format", "json_schema", "json_object"))):
                    raise
                last_error = exc
                continue
            self._mode_cache[cache_key] = mode
            return reply
        assert last_error is not None
        raise last_error

    def _request(self, mode, model, system, prompt, schema, schema_name, max_output_tokens,
                 effort):
        extra: dict = {}
        body = self._router_body(model)
        if self.reasoning == "effort" and effort:
            extra["reasoning_effort"] = self.medium if effort == "medium" else effort
        elif self.reasoning == "thinking":
            body["thinking"] = {"type": "enabled"}
        if body:
            extra["extra_body"] = body
        if mode == "json_schema":
            extra["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            }
        else:
            if mode == "json_object":
                extra["response_format"] = {"type": "json_object"}
            prompt = (
                f"{prompt}\n\nReply with only a JSON object that follows this JSON schema, "
                f"with no other text:\n{json.dumps(schema)}"
            )
        try:
            response = self._client().chat.completions.create(
                model=self._model_name(model),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                **self._token_limit(max_output_tokens),
                **extra,
            )
        except Exception as exc:
            raise translate_openai_error(exc) from exc

        return _chat_reply(response)

    def _token_limit(self, maximum: int) -> dict:
        return {"max_tokens": maximum}

    def list_models(self) -> list[str]:
        return list_openai_style_models(self._client())


class CompatibleResponsesAdapter(_CustomEndpoint, OpenAIAdapter):
    """Native Responses format at the chosen address, without assuming hosted search rights."""

    can_search_the_web = False
    strict_reasoning = True

    def _client(self) -> openai.OpenAI:
        with self._client_lock:
            if self._sdk_client is None:
                self._sdk_client = openai.OpenAI(
                    api_key=self.api_key or "not-needed", base_url=self.base_url,
                    default_headers=self._headers(),
                    max_retries=0, timeout=self.timeout,
                )
        return self._sdk_client


class CompatibleMessagesAdapter(_CustomEndpoint, AnthropicAdapter):
    """Native Messages format at the chosen address; upstream tools are not a proxy entitlement."""

    can_search_the_web = False
    strict_reasoning = True

    def _messages_base(self) -> str:
        # The Messages SDK adds /v1 itself. Accept the same /v1 base people use with
        # Chat/Responses, as well as a documented unversioned Messages base.
        return self.base_url.rstrip("/").removesuffix("/v1")

    def _client(self) -> anthropic.Anthropic:
        with self._client_lock:
            if self._sdk_client is None:
                self._sdk_client = anthropic.Anthropic(
                    api_key=self.api_key or "not-needed", base_url=self._messages_base(),
                    default_headers=self._headers(),
                    max_retries=0, timeout=self.timeout,
                )
        return self._sdk_client


def _chat_usage(usage) -> Usage:
    input_tokens = getattr(usage, "prompt_tokens", None)
    output_tokens = getattr(usage, "completion_tokens", None)
    return Usage(input_tokens=input_tokens or 0, output_tokens=output_tokens or 0,
                 cached_input_tokens=_detail(usage, "prompt_tokens_details", "cached_tokens"),
                 reasoning_tokens=_detail(usage, "completion_tokens_details", "reasoning_tokens"),
                 unreported_requests=int(input_tokens is None or output_tokens is None))


def _chat_reply(response, usage: Usage | None = None) -> RawReply:
    usage = usage if usage is not None else _chat_usage(response.usage)
    if not response.choices:
        error = AIInvalidOutput("The custom AI provider sent no answer to check.")
        error.usage = usage
        raise error
    choice = response.choices[0]
    error = None
    if choice.finish_reason == "length":
        error = AIOutputTruncated(MSG_TRUNCATED)
    elif choice.finish_reason == "content_filter" or getattr(choice.message, "refusal", None):
        error = AIRefused(MSG_REFUSED)
    elif (choice.finish_reason != "stop" or choice.message is None
          or getattr(choice.message, "tool_calls", None)
          or getattr(choice.message, "function_call", None)):
        error = AIInvalidOutput("The custom AI provider did not confirm a completed answer.")
    elif choice.message.content is not None and not isinstance(choice.message.content, str):
        error = AIInvalidOutput("The custom AI provider returned an unsupported answer format.")
    if error is not None:
        error.usage = usage
        raise error
    return RawReply(text=choice.message.content or "", usage=usage)


def _detail(usage, group: str, name: str) -> int:
    details = getattr(usage, group, None) if usage else None
    return (getattr(details, name, 0) or 0) if details else 0
