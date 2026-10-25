"""OpenAI through the official `openai` library (Responses API), plus shared helpers
for "Other API" providers."""

import openai

from jobcu.ai.base import (
    MSG_BAD_REQUEST,
    MSG_KEY_REJECTED,
    MSG_MODEL_NOT_FOUND,
    MSG_NO_PERMISSION,
    MSG_QUOTA,
    MSG_RATE_LIMITED,
    MSG_REFUSED,
    MSG_TRUNCATED,
    MSG_UNAVAILABLE,
    TRANSPORT_ERRORS,
    AIAuthError,
    AIBadRequest,
    AIError,
    AIInvalidOutput,
    AIModelNotFound,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIReasoningUnsupported,
    AIRefused,
    AIUnavailable,
    ProviderAdapter,
    RawReply,
    ResearchReply,
    Source,
    Usage,
    connection_problem,
    parse_retry_after,
    reasoning_control_refused,
    unique_sources,
)
from jobcu.settings import Effort

# Words in model names that mean the model can't write text answers
# (image, audio, embedding models and similar). Used only to tidy the model list.
_NON_TEXT_MODEL_WORDS = (
    "embedding",
    "tts",
    "whisper",
    "dall-e",
    "image",
    "audio",
    "realtime",
    "moderation",
    "transcribe",
    "speech",
    "sora",
    "video",
)


class OpenAIAdapter(ProviderAdapter):
    can_search_the_web = True
    # Requests stream: a streamed answer keeps the connection busy, while a plain request can
    # wait silently past a network's idle limit (cut at 60.0 s on 2026-10-24, see Claude's).
    stream_requests = True
    _sdk_client: openai.OpenAI | None = None

    def _client(self) -> openai.OpenAI:
        with self._client_lock:
            if self._sdk_client is None:
                self._sdk_client = openai.OpenAI(
                    api_key=self.api_key, max_retries=0, timeout=self.timeout
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
        extra: dict = {}
        if effort:
            extra["reasoning"] = {"effort": effort}
        try:
            response = self._create(
                model=model,
                instructions=system,
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": schema,
                        "strict": True,
                    }
                },
                max_output_tokens=max_output_tokens,
                store=False,  # don't keep the user's data on OpenAI's side
                **extra,
            )
        except Exception as exc:
            raise translate_openai_error(exc) from exc

        usage = _response_usage(response)
        _check_response(response, usage)
        return RawReply(text=response.output_text, usage=usage)

    def research(
        self, *, model: str, system: str, prompt: str, max_searches: int, max_output_tokens: int,
        effort: Effort | None = None,
    ) -> ResearchReply:
        extra: dict = {}
        if effort:
            # Web search needs at least "low" reasoning where a model has reasoning at all.
            extra["reasoning"] = {"effort": "low" if effort == "minimal" else effort}
        try:
            response = self._create(
                model=model,
                instructions=system,
                input=prompt,
                tools=[{"type": "web_search"}],
                max_tool_calls=max_searches,
                max_output_tokens=max_output_tokens,
                store=False,
                **extra,
            )
        except Exception as exc:
            raise translate_openai_error(exc) from exc
        sources, searches = [], 0
        for item in response.output:
            if getattr(item, "type", "") == "web_search_call":
                searches += 1
            for part in getattr(item, "content", None) or []:
                for annotation in getattr(part, "annotations", None) or []:
                    url = getattr(annotation, "url", None)
                    if url:
                        sources.append(Source(url, getattr(annotation, "title", "") or ""))
        usage = _response_usage(response, searches=searches)
        _check_response(response, usage)
        return ResearchReply(
            text=response.output_text,
            sources=unique_sources(sources),
            usage=usage,
        )

    def list_models(self) -> list[str]:
        return list_openai_style_models(self._client())

    def _create(self, **request):
        """The final response. A stream that broke after it began did paid work: its usage is
        marked unknown rather than left out."""
        if not self.stream_requests:
            return self._client().responses.create(**request)
        began = False
        try:
            for event in self._client().responses.create(**request, stream=True):
                began = True
                kind = getattr(event, "type", "")
                if kind in ("response.completed", "response.incomplete", "response.failed"):
                    return event.response
                if kind == "error":
                    raise AIUnavailable(MSG_UNAVAILABLE, str(getattr(event, "message", "")))
        except Exception as exc:
            error = translate_openai_error(exc)
            if began and error.usage is None:
                error.usage = Usage(unreported_requests=1)
            raise error from exc
        error = AIInvalidOutput("The AI provider's answer stream ended without a final answer.")
        error.usage = Usage(unreported_requests=int(began))
        raise error


def _response_usage(response, *, searches: int = 0) -> Usage:
    receipt = response.usage
    complete = all(type(getattr(receipt, name, None)) is int
                   and getattr(receipt, name) >= 0 for name in ("input_tokens", "output_tokens"))
    return Usage(
        input_tokens=_attr(receipt, "input_tokens"),
        output_tokens=_attr(receipt, "output_tokens"),  # already includes reasoning
        cached_input_tokens=_attr(getattr(receipt, "input_tokens_details", None), "cached_tokens"),
        reasoning_tokens=_attr(getattr(receipt, "output_tokens_details", None), "reasoning_tokens"),
        web_searches=searches,
        unreported_requests=int(not complete),
    )


def _check_response(response, usage: Usage) -> None:
    """Partial text is not a completed answer; a failure can still have a bill."""
    failure = None
    if response.status == "incomplete":
        reason = getattr(response.incomplete_details, "reason", "")
        failure = AIRefused(MSG_REFUSED) if reason == "content_filter" \
            else AIOutputTruncated(MSG_TRUNCATED)
    elif response.status == "failed":
        failure = AIUnavailable("The AI provider reported that its request failed. "
                                "Completed work was kept. Try again later.",
                                getattr(response.error, "code", "") or "")
    elif response.status != "completed":
        failure = AIInvalidOutput("The AI provider did not confirm a completed answer.")
    for item in response.output:
        for part in getattr(item, "content", None) or []:
            if getattr(part, "type", "") == "refusal":
                failure = AIRefused(MSG_REFUSED, getattr(part, "refusal", ""))
    if failure is not None:
        failure.usage = usage
        raise failure


def list_openai_style_models(client: openai.OpenAI) -> list[str]:
    try:
        names = [model.id for model in client.models.list()]
    except Exception as exc:
        raise translate_openai_error(exc) from exc
    return sorted(
        name for name in names if not any(word in name.lower() for word in _NON_TEXT_MODEL_WORDS)
    )


def translate_openai_error(exc: Exception) -> Exception:
    detail = str(exc)
    if isinstance(exc, openai.AuthenticationError):
        return AIAuthError(MSG_KEY_REJECTED, detail)
    if isinstance(exc, openai.PermissionDeniedError):
        return AIAuthError(MSG_NO_PERMISSION, detail)
    if isinstance(exc, openai.NotFoundError):
        return AIModelNotFound(MSG_MODEL_NOT_FOUND, detail)
    if isinstance(exc, openai.RateLimitError):
        if "insufficient_quota" in detail or getattr(exc, "code", None) == "insufficient_quota":
            return AIQuotaExhausted(MSG_QUOTA, detail)
        retry_after = parse_retry_after(exc.response.headers.get("retry-after"))
        return AIRateLimited(MSG_RATE_LIMITED, detail, retry_after)
    if isinstance(exc, openai.APIStatusError):
        if exc.status_code == 402:
            return AIQuotaExhausted(MSG_QUOTA, detail)
        if exc.status_code >= 500:
            return AIUnavailable(MSG_UNAVAILABLE, detail)
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get("error", body)
        if exc.status_code == 400 and isinstance(error, dict):
            controls = ("reasoning", "reasoning.effort", "reasoning_effort")
            code, param = error.get("code"), error.get("param")
            if (code == "unsupported_parameter" and param in controls) or (
                    code in (None, "unsupported_parameter", "invalid_request_error")
                    and param in (None, *controls)
                    and reasoning_control_refused(error.get("message"), controls)):
                return AIReasoningUnsupported(MSG_BAD_REQUEST, detail)
        return AIBadRequest(MSG_BAD_REQUEST, detail)
    if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError, *TRANSPORT_ERRORS)):
        return connection_problem(exc)
    if isinstance(exc, openai.APIError):
        # An error event inside a stream that had already started: the service failed after
        # accepting the request, so it carries no HTTP status of its own.
        body = exc.body if isinstance(exc.body, dict) else {}
        code = str(body.get("code") or body.get("type") or "").lower()
        if code == "429" or "rate" in code:
            return AIRateLimited(MSG_RATE_LIMITED, detail)
        if code == "402" or "quota" in code:
            return AIQuotaExhausted(MSG_QUOTA, detail)
        return AIUnavailable(MSG_UNAVAILABLE, detail)
    if isinstance(exc, AIError):
        return exc
    return AIBadRequest(MSG_BAD_REQUEST, detail)


def _attr(obj, name: str) -> int:
    value = getattr(obj, name, None)
    return value if type(value) is int and value >= 0 else 0
