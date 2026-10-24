"""Anthropic (Claude) through the official `anthropic` library.

Research uses web search to find pages and web fetch to read whole pages and PDFs the request or
a search named (for example a job ad's own URL). Fetching costs only the text it adds, which is
bounded; searches stay within the shared allowance. Claude links each written passage to the
pages it rests on, so Jobcu validates its claims like any other provider's citations.
"""

import re

import anthropic

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
    Citation,
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

# Text one fetched page may add. Pages and PDFs beyond it are cut, never silently dropped; the
# bound also keeps a research request within lower-priced context tiers.
FETCH_CONTENT_TOKENS = 6_000
# A server-side research turn may pause after its own step limit; continue it this many times.
MAX_CONTINUATIONS = 4
# Mid-stream error events carry the error type instead of an HTTP status.
_RETRYABLE_ERRORS = {"overloaded_error", "api_error", "timeout_error"}


def web_tools(model: str, max_searches: int, *, fetch: bool = True) -> list[dict]:
    """The newest web tool versions the model supports, within this request's allowance."""
    found = re.match(r"claude-(opus|sonnet|fable|mythos)-(\d+)(?:-(\d+))?(?:-|$)", model)
    version = (int(found[2]), int(found[3] or 0)) if found else (0, 0)
    # Dynamic filtering arrived with the 4.6 generation; Haiku and older models keep the basic
    # tools, which every Claude model with web tools accepts.
    dynamic = found is not None and (found[1] in {"fable", "mythos"} or version >= (4, 6))
    tools = [{"type": "web_search_20260209" if dynamic else "web_search_20250305",
              "name": "web_search", "max_uses": max_searches}]
    if fetch:
        tools.append({"type": "web_fetch_20260209" if dynamic else "web_fetch_20250910",
                      "name": "web_fetch", "max_uses": max(2, max_searches),
                      "citations": {"enabled": True},
                      "max_content_tokens": FETCH_CONTENT_TOKENS})
    return tools


class AnthropicAdapter(ProviderAdapter):
    can_search_the_web = True
    # Every request streams. A streamed answer starts at once and keeps the connection busy;
    # a plain request can wait silently past a network's idle limit (cut at exactly 60.0 s on
    # 2026-10-24, which stopped every later Claude research request in that search).
    stream_requests = True
    _sdk_client: anthropic.Anthropic | None = None

    def _client(self) -> anthropic.Anthropic:
        with self._client_lock:
            if self._sdk_client is None:
                self._sdk_client = anthropic.Anthropic(
                    api_key=self.api_key, max_retries=0, timeout=self.timeout
                )
        return self._sdk_client

    def _send(self, **request):
        """The final message. A broken stream keeps the usage it reported as a lower bound."""
        if not self.stream_requests:
            return self._client().messages.create(**request)
        stream = None
        try:
            with self._client().messages.stream(**request) as stream:
                return stream.get_final_message()
        except Exception as exc:
            error = _translate(exc) if isinstance(
                exc, (anthropic.APIError, AIError, *TRANSPORT_ERRORS)) else AIInvalidOutput(
                "The AI provider sent an answer stream Jobcu could not read.", str(exc)[:300])
            try:
                started = stream.current_message_snapshot if stream is not None else None
            except AssertionError:  # nothing arrived: the library has no message yet
                started = None
            if started is not None:
                partial = _usage(getattr(started, "usage", None))
                partial.unreported_requests = 1
                error.usage = partial
            elif isinstance(error, AIInvalidOutput):
                error.usage = Usage(unreported_requests=1)  # an answer arrived: work was done
            raise error from exc

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
        output_config: dict = {"format": {"type": "json_schema", "schema": schema}}
        # The instructions are the same in every request of a step (scoring asks about several
        # batches of jobs), so Anthropic is asked to keep them ready and charge less for them.
        system_blocks = [{"type": "text", "text": system,
                          "cache_control": {"type": "ephemeral"}}]
        if effort:
            # Anthropic has no "minimal" level; "low" is its lowest.
            output_config["effort"] = "low" if effort == "minimal" else effort
        try:
            response = self._send(
                model=model,
                max_tokens=max_output_tokens,
                system=system_blocks,
                messages=[{"role": "user", "content": prompt}],
                output_config=output_config,
            )
        except Exception as exc:
            raise _translate(exc) from exc

        usage = _check_response(response)
        text = "".join(block.text for block in response.content if block.type == "text")
        return RawReply(text=text, usage=usage)

    def research(
        self, *, model: str, system: str, prompt: str, max_searches: int, max_output_tokens: int,
        effort: Effort | None = None,
    ) -> ResearchReply:
        extra: dict = {}
        if effort:
            extra["output_config"] = {"effort": "low" if effort == "minimal" else effort}
        tools = web_tools(model, max_searches)
        blocks: list = []
        usage = Usage()
        for _ in range(MAX_CONTINUATIONS + 1):
            messages = [{"role": "user", "content": prompt}]
            if blocks:
                # A paused server turn resumes from its own content; no new instruction.
                messages.append({"role": "assistant", "content": [
                    block.to_dict() for block in blocks]})
            try:
                response = self._send(
                    model=model, max_tokens=max_output_tokens, system=system,
                    messages=messages, tools=tools, **extra)
            except Exception as exc:
                error = _translate(exc)
                if (not blocks and isinstance(error, AIBadRequest) and len(tools) > 1
                        and any(word in error.detail.lower()
                                for word in ("web_fetch", "web fetch", "_20260209"))):
                    # The account or model refused the newer/optional tool before any work:
                    # keep the basic search every Claude model with web tools accepts.
                    tools = web_tools("", max_searches, fetch=False)
                    continue
                if usage != Usage():
                    error.usage = usage + (error.usage or Usage())
                raise error from exc
            usage = usage + _usage(getattr(response, "usage", None))
            blocks.extend(getattr(response, "content", None) or [])
            if getattr(response, "stop_reason", None) != "pause_turn":
                break
        _check_response(response, usage)
        return _research_reply(blocks, usage)

    def list_models(self) -> list[str]:
        try:
            return sorted(model.id for model in self._client().models.list())
        except Exception as exc:
            raise _translate(exc) from exc


def _usage(usage) -> Usage:
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    tool_use = getattr(usage, "server_tool_use", None)
    input_tokens = getattr(usage, "input_tokens", None)
    output_tokens = getattr(usage, "output_tokens", None)
    return Usage(
        # Anthropic reports cached and uncached input separately; Jobcu counts the total.
        input_tokens=(input_tokens or 0) + cache_write + cache_read,
        output_tokens=output_tokens or 0,
        cached_input_tokens=cache_read,
        web_searches=(tool_use.web_search_requests or 0) if tool_use else 0,
        unreported_requests=int(input_tokens is None or output_tokens is None),
    )


def _research_reply(blocks: list, usage: Usage) -> ResearchReply:
    """Notes, the pages searched or read, and which written passage rests on which page."""
    text, sources, citations = [], [], []
    fetched = []  # documents in the order Claude's char/page citations index them
    for block in blocks:
        if block.type == "web_fetch_tool_result":
            result = getattr(block, "content", None)
            url = getattr(result, "url", None)
            if getattr(result, "type", "") == "web_fetch_result" and url:
                title = getattr(getattr(result, "content", None), "title", None) or ""
                fetched.append(Source(url, title))
                sources.append(Source(url, title))
        elif block.type == "web_search_tool_result":
            for item in getattr(block, "content", None) or []:
                url = getattr(item, "url", None)
                if url:
                    sources.append(Source(url, getattr(item, "title", "") or ""))
        elif block.type == "text":
            text.append(block.text)
            for citation in getattr(block, "citations", None) or []:
                source = _cited_source(citation, fetched)
                if source is not None:
                    sources.append(source)
                    if block.text.strip():
                        citations.append(Citation(block.text, source.url))
    return ResearchReply("".join(text), unique_sources(sources), usage,
                         citations=citations)


def _cited_source(citation, fetched: list[Source]) -> Source | None:
    url = getattr(citation, "url", None)
    if url:
        return Source(url, getattr(citation, "title", "") or "")
    index = getattr(citation, "document_index", None)
    if not isinstance(index, int) or not 0 <= index < len(fetched):
        return None
    # A fetched page cited under another title is not provably this page.
    title = getattr(citation, "document_title", None)
    if title and fetched[index].title and title != fetched[index].title:
        return None
    return fetched[index]


def _check_response(response, usage: Usage | None = None) -> Usage:
    usage = usage if usage is not None else _usage(getattr(response, "usage", None))
    reason = getattr(response, "stop_reason", None)
    error = None
    if reason == "refusal":
        error = AIRefused(MSG_REFUSED)
    elif reason == "max_tokens":
        error = AIOutputTruncated(MSG_TRUNCATED)
    elif reason == "model_context_window_exceeded":
        # Raising the output allowance cannot repair an exhausted input/context window.
        error = AIInvalidOutput("The AI provider reached its text limit before finishing.")
    elif reason not in {"end_turn", "stop_sequence"}:
        error = AIInvalidOutput("The AI provider has not confirmed a finished answer.")
    elif not isinstance(getattr(response, "content", None), list):
        error = AIInvalidOutput("The AI provider returned no supported answer content.")
    if error is not None:
        error.usage = usage
        raise error
    return usage


def _translate(exc: Exception) -> Exception:
    detail = str(exc)
    if isinstance(exc, anthropic.AuthenticationError):
        return AIAuthError(MSG_KEY_REJECTED, detail)
    if isinstance(exc, anthropic.PermissionDeniedError):
        return AIAuthError(MSG_NO_PERMISSION, detail)
    if isinstance(exc, anthropic.NotFoundError):
        return AIModelNotFound(MSG_MODEL_NOT_FOUND, detail)
    if isinstance(exc, anthropic.RateLimitError):
        retry_after = parse_retry_after(exc.response.headers.get("retry-after"))
        return AIRateLimited(MSG_RATE_LIMITED, detail, retry_after)
    if isinstance(exc, anthropic.APIStatusError):
        if exc.status_code == 402 or "credit balance" in detail.lower():
            return AIQuotaExhausted(MSG_QUOTA, detail)
        if exc.status_code == 529 or exc.status_code >= 500:
            return AIUnavailable(MSG_UNAVAILABLE, detail)
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get("error", body)
        kind = error.get("type") if isinstance(error, dict) else None
        if kind in _RETRYABLE_ERRORS:  # reported inside a stream that had already started
            return AIUnavailable(MSG_UNAVAILABLE, detail)
        if kind == "rate_limit_error":
            return AIRateLimited(MSG_RATE_LIMITED, detail)
        if exc.status_code == 400 and isinstance(error, dict) and reasoning_control_refused(
                error.get("message"), ("effort", "output_config.effort")):
            return AIReasoningUnsupported(MSG_BAD_REQUEST, detail)
        return AIBadRequest(MSG_BAD_REQUEST, detail)
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError,
                        *TRANSPORT_ERRORS)):
        return connection_problem(exc)
    if isinstance(exc, AIError):
        return exc
    return AIBadRequest(MSG_BAD_REQUEST, detail)
