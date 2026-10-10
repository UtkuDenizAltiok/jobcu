"""Google (Gemini) through the official `google-genai` library."""

import re
import threading
from collections import Counter

import httpx
from google import genai
from google.genai import errors, types

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
    AIAuthError,
    AIBadRequest,
    AIError,
    AIModelNotFound,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIRefused,
    AIUnavailable,
    AIWebSearchUnavailable,
    ProviderAdapter,
    RawReply,
    ResearchReply,
    Source,
    Usage,
    unique_sources,
)
from jobcu.settings import Effort

_REFUSAL_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}


class GeminiAdapter(ProviderAdapter):
    can_search_the_web = True
    _genai_client: genai.Client | None = None

    def __init__(self, api_key: str, base_url: str = "", timeout: float = 180.0) -> None:
        super().__init__(api_key, base_url, timeout)
        self._stream_responses = threading.local()

    def _capture_response(self, response: httpx.Response) -> None:
        responses = getattr(self._stream_responses, "current", None)
        if responses is not None:
            responses.append(response)

    def _client(self) -> genai.Client:
        # Kept for the adapter's lifetime: the library closes its connection when the
        # client object is discarded, which would break results that are still loading.
        with self._client_lock:
            if self._genai_client is None:
                self._genai_client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        timeout=int(self.timeout * 1000),
                        client_args={"event_hooks": {"response": [self._capture_response]}},
                    ),
                )
        return self._genai_client

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
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_level=effort.upper()) if effort else None,
            # Jobcu gives the model no tools here, so the library's tool loop stays off.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        reply = self._stream(model, prompt, config)
        return RawReply(reply.text, reply.usage)

    def research(
        self, *, model: str, system: str, prompt: str, max_searches: int, max_output_tokens: int,
        effort: Effort | None = None,
    ) -> ResearchReply:
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_level=effort.upper()) if effort else None,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        return self._stream(model, prompt, config, web_search=True)

    def _stream(self, model: str, prompt: str, config: types.GenerateContentConfig,
                *, web_search: bool = False) -> ResearchReply:
        """Receive long answers in chunks; publish only a complete, successful answer.

        Metadata can arrive separately from text, and repeated cumulative counts are not
        additional tokens/queries. Keep every source and ignore thought text, as the SDK's
        ordinary response.text does. A broken stream never supplies a partial judgement.
        """
        text, sources = [], []
        queries: Counter[str] = Counter()
        counts: Counter[str] = Counter()
        finished = False
        stream = None
        self._stream_responses.current = []
        try:
            stream = self._client().models.generate_content_stream(
                model=model, contents=prompt, config=config)
            for response in stream:
                feedback = response.prompt_feedback
                if feedback is not None and feedback.block_reason:
                    raise AIRefused(MSG_REFUSED, str(feedback.block_reason))
                meta = response.usage_metadata
                if meta is not None:
                    counts |= Counter({name: getattr(meta, name) or 0 for name in (
                        "prompt_token_count", "candidates_token_count",
                        "cached_content_token_count", "thoughts_token_count")})
                candidate = response.candidates[0] if response.candidates else None
                if candidate is None:
                    continue  # final usage can arrive without another text candidate
                finish = _name(candidate.finish_reason)
                if finish == "MAX_TOKENS":
                    raise AIOutputTruncated(MSG_TRUNCATED)
                if finish in _REFUSAL_REASONS or finish not in (
                        "", "FINISH_REASON_UNSPECIFIED", "STOP"):
                    raise AIRefused(MSG_REFUSED, finish)
                finished |= finish == "STOP"
                if candidate.content is not None:
                    text.extend(part.text for part in candidate.content.parts or []
                                if part.text and not part.thought)
                grounding = candidate.grounding_metadata
                if grounding is not None:
                    queries |= Counter(grounding.web_search_queries or [])
                    for chunk in grounding.grounding_chunks or []:
                        web = chunk.web
                        if web is not None and web.uri:
                            sources.append(Source(web.uri, web.title or ""))
            if not finished:
                raise AIUnavailable(MSG_UNAVAILABLE, "AI answer stream ended before completion.")
        except Exception as exc:
            raise _translate(exc, web_search=web_search) from exc
        finally:
            try:
                if stream is not None:
                    stream.close()
            finally:
                # The SDK's synchronous iterator does not close an interrupted HTTP body.
                # Close only this thread's responses; keep the shared client/pool alive.
                for response in self._stream_responses.current:
                    response.close()
                del self._stream_responses.current
        thoughts = counts["thoughts_token_count"]
        return ResearchReply(
            text="".join(text),
            sources=unique_sources(sources),
            usage=Usage(
                input_tokens=counts["prompt_token_count"],
                output_tokens=counts["candidates_token_count"] + thoughts,
                cached_input_tokens=counts["cached_content_token_count"],
                reasoning_tokens=thoughts,
                web_searches=sum(queries.values()),
            ),
        )

    def list_models(self) -> list[str]:
        try:
            models = list(self._client().models.list())
        except Exception as exc:
            raise _translate(exc) from exc
        return sorted(
            (model.name or "").removeprefix("models/")
            for model in models
            if "generateContent" in (model.supported_actions or [])
        )


def _name(value) -> str:
    return getattr(value, "name", None) or str(value or "")


def _translate(exc: Exception, *, web_search: bool = False) -> Exception:
    detail = str(exc)
    if isinstance(exc, errors.APIError):
        status = (exc.status or "").upper()
        text = f"{status} {exc.message or ''} {exc.details or ''}"
        if "API_KEY_INVALID" in text or "API key not valid" in text or exc.code == 401:
            return AIAuthError(MSG_KEY_REJECTED, detail)
        if web_search and _web_search_refused(exc.code, text):
            return AIWebSearchUnavailable(
                "Google web look-ups aren't available for this model or API project. "
                "Check the model's web-search support and your project's billing in Google "
                "AI Studio. Jobcu will continue searching job sources and scoring ads; "
                'conditions that need web research stay "not checked", and extra employers '
                "and full ads can't be looked up online in this search.",
                detail,
            )
        if exc.code == 429 or status == "RESOURCE_EXHAUSTED":
            # Daily limits (e.g. "...PerDay...") won't reset by waiting a minute.
            if "perday" in text.lower().replace("_", "").replace(" ", ""):
                return AIQuotaExhausted(MSG_QUOTA, detail)
            return AIRateLimited(MSG_RATE_LIMITED, detail, _retry_delay(text))
        if exc.code == 403:
            return AIAuthError(MSG_NO_PERMISSION, detail)
        if exc.code == 404:
            return AIModelNotFound(MSG_MODEL_NOT_FOUND, detail)
        if exc.code and exc.code >= 500:
            return AIUnavailable(MSG_UNAVAILABLE, detail)
        return AIBadRequest(MSG_BAD_REQUEST, detail)
    if isinstance(exc, httpx.HTTPError):
        return AIUnavailable(MSG_UNAVAILABLE, detail)
    if isinstance(exc, AIError):
        return exc
    return AIBadRequest(MSG_BAD_REQUEST, detail)


def _web_search_refused(code: int | None, text: str) -> bool:
    """Only explicit search capability refusals, never a general quota or auth error."""
    lower = text.lower()
    mentions_search = any(word in lower for word in ("grounding", "google search", "googlesearch",
                                                    "google_search"))
    if not mentions_search:
        return False
    if code in (400, 403):
        return any(word in lower for word in ("not supported", "not available", "unsupported",
                                              "not enabled", "billing", "paid tier", "free tier"))
    return code == 429 and bool(re.search(
        r"(?:quota_?value|limit)['\"]?\s*[:=]\s*['\"]?0\b", lower))


def _retry_delay(text: str) -> float | None:
    """Gemini suggests a wait like 'retryDelay': '31s'."""
    match = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", text)
    return float(match.group(1)) if match else None
