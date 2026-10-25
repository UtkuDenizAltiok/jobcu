"""Google (Gemini) through the official `google-genai` library."""

import logging
import re
import threading
import time
from collections import Counter
from dataclasses import replace

import httpx
from google import genai
from google.genai import errors, types

from jobcu.ai import request_recovery
from jobcu.ai.base import (
    MSG_BAD_REQUEST,
    MSG_CONNECTION,
    MSG_KEY_REJECTED,
    MSG_MODEL_NOT_FOUND,
    MSG_QUOTA,
    MSG_RATE_LIMITED,
    MSG_REFUSED,
    MSG_TRUNCATED,
    MSG_UNAVAILABLE,
    AIAuthError,
    AIBadRequest,
    AIConnectionError,
    AIError,
    AIModelNotFound,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIReasoningUnsupported,
    AIRefused,
    AIUnavailable,
    AIUsageUncertain,
    AIWebSearchUnavailable,
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
from jobcu.ai.gemini_events import EVENT_MODELS, EventAnswer
from jobcu.ai.request_recovery import RecoveryContext
from jobcu.ai.usage import UsageLog
from jobcu.settings import Effort

_TERMINAL_INTERACTIONS = {
    "completed", "cancelled", "failed", "incomplete", "budget_exceeded", "requires_action"}
# Flex (half price) queues requests for minutes when Google is busy (1-15 minutes is Google's
# target; 435 s for one web-search request on 2026-10-24). Google refuses a request it has no
# capacity for: try again a little later, then send it at the normal price. After this many
# Flex failures in one search, the rest of the search uses normal processing.
FLEX_ATTEMPTS = 3
FLEX_RETRY_SECONDS = 5.0
FLEX_SECONDS = 1200
FLEX_FAILURES = 3
FLEX_NOTICE = ("Google's half-price Flex processing was busy or failed several times, so the "
               "rest of this search uses normal processing at the normal price.")
_REFUSAL_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}
log = logging.getLogger(__name__)


class _FlexRefused(Exception):
    """Google refused a Flex request before accepting any work: nothing was generated."""

    def __init__(self, error: AIError) -> None:
        super().__init__(error.message)
        self.error = error


class GeminiAdapter(ProviderAdapter):
    can_search_the_web = True
    can_recover_requests = True
    can_flex = True
    _genai_client: genai.Client | None = None

    def __init__(self, api_key: str, base_url: str = "", timeout: float = 180.0) -> None:
        super().__init__(api_key, base_url, timeout)
        self._stream_responses = threading.local()
        self._interactions = None
        self._recovery_context = threading.local()
        self._flex_failures = 0

    def configure_request_recovery(self, context: RecoveryContext) -> None:
        self._recovery_context.current = context

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
                        retry_options=types.HttpRetryOptions(attempts=1),
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
        if model.removeprefix("models/") in EVENT_MODELS:
            reply = self._event_stream(model, system, prompt, effort, max_output_tokens, schema)
            return RawReply(reply.text, reply.usage, reply.recovery_id)
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
        if model.removeprefix("models/") in EVENT_MODELS:
            return self._event_stream(model, system, prompt, effort, max_output_tokens,
                                      web_search=True)
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_level=effort.upper()) if effort else None,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        return self._stream(model, prompt, config, web_search=True)

    def _event_resource(self):
        client = self._client()
        with self._client_lock:
            if self._interactions is None:
                self._interactions = client.interactions
                # This SDK resource interprets attempts=1 as an extra retry.
                # Jobcu owns the retry/usage budget; disable the second retry layer.
                self._interactions.sdk_configuration.retry_config = None
        return self._interactions

    def _event_stream(self, model, system, prompt, effort, max_tokens, schema=None,
                      *, web_search=False):
        model = model.removeprefix("models/")
        generation = {"max_output_tokens": max_tokens, "thinking_summaries": "auto"}
        if effort:
            generation["thinking_level"] = effort
        request = dict(model=model, input=prompt, system_instruction=system,
                       stream=True, store=False, background=False, generation_config=generation)
        if schema is not None:
            request["response_format"] = {
                "type": "text", "mime_type": "application/json", "schema": schema}
        if web_search:
            request["tools"] = [{"type": "google_search"}]
        context = getattr(self._recovery_context, "current", None)
        if context is not None:
            self.cleanup_pending(context)
        with self._client_lock:
            # Google can stop a queued Flex request midway. With recovery that is a clean
            # failed operation; over a plain stream it is a dropped connection that may have
            # been billed, which stops research for the rest of the search (search 8 replay,
            # 2026-10-25: 2 of 5 web look-ups dropped after 81-171 s). Flex needs recovery.
            flex = (self.flex and self._flex_failures < FLEX_FAILURES
                    and context is not None and context.enabled)
        if not flex:
            return self._send_events(request, web_search, context)
        for attempt in range(1, FLEX_ATTEMPTS + 1):
            try:
                return self._send_events({**request, "service_tier": "flex"}, web_search,
                                         context)
            except _FlexRefused as refused:
                log.info("Flex request refused before any work (attempt %d of %d): %s",
                         attempt, FLEX_ATTEMPTS, refused.error.detail or refused.error.message)
                if attempt < FLEX_ATTEMPTS:
                    delay = FLEX_RETRY_SECONDS * 2 ** (attempt - 1)
                    (context.wait(delay, retry=True) if context is not None
                     else time.sleep(delay))
            except (AIUnavailable, AIRateLimited) as error:
                # Accepted Flex work that failed is not repeated here: Jobcu's normal retry
                # rules decide, so a request that may have been billed is never doubled.
                if not isinstance(error, AIConnectionError):
                    self._flex_failed(context)
                raise
        self._flex_failed(context)
        return self._send_events(request, web_search, context)

    def _flex_failed(self, context) -> None:
        with self._client_lock:
            self._flex_failures += 1
            last = self._flex_failures == FLEX_FAILURES
        if last and context is not None:
            context.notify(FLEX_NOTICE)

    def _send_events(self, request, web_search, context):
        flex = request.get("service_tier") == "flex"
        state = EventAnswer(model=request["model"], web_search=web_search,
                            service_tier="flex" if flex else "")
        if context is not None and context.enabled:
            request = {**request, "store": True, "background": True, "stream": False}
            return self._background_request(request, state, context)
        if flex:
            # The answer can wait in Google's queue for minutes before its first event.
            request = {**request, "timeout": max(self.timeout, FLEX_SECONDS)}
        stream = None
        started = time.monotonic()
        events = 0
        self._stream_responses.current = []
        try:
            stream = self._event_resource().create(**request)
            for event in stream:
                events += 1
                state.add(event.model_dump(mode="json", exclude_none=True))
                if state.complete:
                    break
            if not state.complete:
                log.info("AI event stream ended without completion after %.1fs: "
                         "headers_received=%s, events_received=%d, final_usage_received=%s",
                         time.monotonic() - started, bool(self._stream_responses.current),
                         events, state.final_usage)
            return state.reply()
        except Exception as exc:
            original = exc
            seen = set()
            while original.__cause__ is not None and id(original) not in seen:
                if isinstance(original, httpx.TransportError):
                    break
                seen.add(id(original))
                original = original.__cause__
            if isinstance(original, httpx.TransportError):
                log.info("AI event stream interrupted after %.1fs: headers_received=%s, "
                         "events_received=%d, completion_received=%s, kind=%s",
                         time.monotonic() - started, bool(self._stream_responses.current),
                         events, state.complete, type(original).__name__)
                exc = original
            translated = self._recovery_error(exc, web_search=web_search)
            if flex and _capacity_refusal(translated) and not (
                    state.steps or state.counts or state.queries or state.search_seen):
                raise _FlexRefused(translated) from exc
            if (isinstance(translated, AIError)
                    and not (isinstance(translated, AIConnectionError)
                             and translated.request_sent is False)
                    and (state.steps or state.counts or state.queries
                         or isinstance(translated, (AIUnavailable, AIOutputTruncated)))):
                # A failed terminal outcome can still carry a complete final bill. A
                # missing/partial receipt stays unknown; failure alone does not erase it.
                translated.usage = state.usage(interrupted=not state.final_usage)
            raise translated from exc
        finally:
            responses = self._stream_responses.current
            del self._stream_responses.current
            for resource in [stream, *responses]:
                if resource is not None:
                    try:
                        resource.close()
                    except httpx.TransportError:
                        pass

    @staticmethod
    def _recovery_error(error, *, web_search=False):
        original, seen = error, set()
        while original.__cause__ is not None and id(original) not in seen:
            status = getattr(original, "status_code", None)
            if (isinstance(original, (httpx.TransportError, errors.APIError))
                    or isinstance(status, int) and 400 <= status <= 599):
                break
            seen.add(id(original))
            original = original.__cause__
        status = getattr(original, "status_code", None)
        if isinstance(status, int) and 400 <= status <= 599:
            body = getattr(original, "body", None)
            original = errors.APIError(status, body if isinstance(body, dict) else {
                "error": {"message": str(body or original)}})
        translated = _translate(original, web_search=web_search)
        response = getattr(error, "response", None)
        if isinstance(translated, AIRateLimited) and response is not None:
            retry_after = parse_retry_after(response.headers.get("Retry-After"))
            if retry_after is not None:
                translated.retry_after = retry_after
        return translated

    @staticmethod
    def _observe_interaction(state, interaction, interaction_id=None):
        if interaction_id is not None and interaction.id != interaction_id:
            raise AIBadRequest(MSG_BAD_REQUEST, "AI retrieval returned a different ID.")
        payload = interaction.model_dump(mode="json", exclude_none=True)
        state.tier(payload)
        state._usage(payload.get("usage"))
        for index, step in enumerate(payload.get("steps") or []):
            if step.get("type") == "google_search_call":
                state._start(index, step)
        return payload

    def _cleanup_interaction(self, interaction_id, state, *, finished, context):
        """Cancel unfinished work before deleting its recoverable remote record."""
        resource = self._event_resource()
        if not finished:
            try:
                response = resource.cancel(id=interaction_id, timeout=15)
                payload = self._observe_interaction(state, response, interaction_id)
                finished = payload.get("status") in _TERMINAL_INTERACTIONS
                if finished:
                    try:
                        state.add({"event_type": "interaction.completed", "interaction": payload})
                    except AIError:
                        pass  # A cancelled answer is unusable; its final bill can be usable.
            except Exception:
                # The operation may have completed while cancellation was being sent.
                try:
                    response = resource.get(id=interaction_id, include_input=False, timeout=15)
                    payload = self._observe_interaction(state, response, interaction_id)
                    finished = payload.get("status") in _TERMINAL_INTERACTIONS
                    if finished:
                        try:
                            state.add({"event_type": "interaction.completed",
                                       "interaction": payload})
                        except AIError:
                            pass
                except Exception:
                    pass
            if not finished:
                context.notify("Jobcu could not confirm cancellation of an interrupted AI "
                               "request. Its local recovery ID is kept for automatic cleanup; "
                               "the provider may still be working and charging.")
        deleted = False
        try:
            # Persist the last bill before deleting the provider's recoverable receipt.
            context.account(state.usage(interrupted=not state.final_usage), interaction_id)
        except Exception:
            context.notify("Jobcu could not save a provider receipt. Its recovery ID is "
                           "kept locally so cleanup can reconcile it later.")
            request_recovery.release(context.provider, interaction_id, deleted=False)
            return finished
        if finished:
            request_recovery.terminal(context.provider, interaction_id)
            for _ in range(2):
                try:
                    resource.delete(id=interaction_id, timeout=15)
                    deleted = True
                    break
                except Exception as error:
                    if (getattr(error, "status_code", None) or getattr(error, "code", None)) == 404:
                        deleted = True
                        break
            if not deleted:
                context.notify("A temporary AI-provider record could not be deleted. Jobcu "
                               "kept its ID and will retry cleanup; the provider's retention "
                               "period can still apply until deletion succeeds.")
        request_recovery.release(context.provider, interaction_id, deleted=deleted)
        return finished

    def cleanup_pending(self, context: RecoveryContext, *, force: bool = False) -> None:
        """Reconcile abandoned work and delete remote records without buying generation."""
        unresolved = False
        for row in request_recovery.pending(context.provider, force=force):
            interaction_id = row["interaction_id"]
            if not request_recovery.claim(context.provider, interaction_id):
                continue
            state = EventAnswer(model=row["model"], web_search=True)
            finished = bool(row["terminal"])
            def account(usage, request_id, row=row):
                UsageLog().record(step=row["step"], provider=row["provider"],
                                  model=row["model"], search_id=row["search_id"],
                                  recovery_id=request_id, created_at=row["created_at"], usage=usage,
                                  budget_id=row["budget_id"])
            cleanup_context = replace(context, account=account)
            try:
                try:
                    response = self._event_resource().get(
                        id=interaction_id, include_input=False, timeout=15)
                    payload = self._observe_interaction(state, response, interaction_id)
                    if payload.get("status") in _TERMINAL_INTERACTIONS:
                        finished = True
                        try:
                            state.add({"event_type": "interaction.completed",
                                       "interaction": payload})
                        except AIError:
                            pass
                except Exception as error:
                    if (getattr(error, "status_code", None) or getattr(error, "code", None)) == 404:
                        finished = True
                    # Cancellation below can recover the bill without another POST.
                finished = self._cleanup_interaction(
                    interaction_id, state, finished=finished, context=cleanup_context)
                unresolved |= not finished
            finally:
                request_recovery.unclaim(context.provider, interaction_id)
        if unresolved:
            raise AIUsageUncertain("An earlier AI request could not be cancelled or "
                                   "reconciled. Jobcu has not sent another generation.")

    def _background_request(self, request, state, context):
        """One paid creation, followed only by retrieval of that same operation."""
        resource = self._event_resource()
        interaction_id = None
        finished = False
        failure = None
        try:
            # An ambiguous create failure has no recoverable ID and must not be replayed.
            try:
                current = resource.create(**request, timeout=30)
            except Exception as error:
                translated = self._recovery_error(error, web_search=state.web_search)
                if request.get("service_tier") == "flex" and _capacity_refusal(translated):
                    raise _FlexRefused(translated) from error
                raise translated from error
            interaction_id = current.id
            if not isinstance(interaction_id, str) or not interaction_id:
                raise AIConnectionError(MSG_CONNECTION, "No recoverable AI operation ID.",
                                        request_sent=True)
            request_recovery.track(context, interaction_id, request["model"])
            context.progress("The AI is processing this request; connection recovery is active")
            deadline = time.monotonic() + max(
                self.timeout, FLEX_SECONDS if request.get("service_tier") == "flex" else 600)
            retries = 0
            poll_delay = 1.0
            while True:
                payload = self._observe_interaction(state, current)
                if current.status not in {"in_progress", "queued"}:
                    if current.status not in _TERMINAL_INTERACTIONS:
                        raise AIConnectionError(MSG_CONNECTION,
                                                "AI operation has no recognized final status.",
                                                request_sent=True)
                    finished = True
                    request_recovery.terminal(context.provider, interaction_id)
                    state.steps = {}  # only the final canonical output can be accepted
                    state.add({"event_type": "interaction.completed", "interaction": payload})
                    context.account(state.usage(), interaction_id)
                    reply = state.reply()
                    reply.recovery_id = interaction_id
                    return reply
                context.observe(state.usage(interrupted=True), interaction_id)
                context.wait(poll_delay)
                poll_delay = min(poll_delay * 2, 5.0)
                if time.monotonic() >= deadline:
                    raise AIConnectionError(MSG_CONNECTION,
                                            "AI recovery reached its processing deadline.",
                                            request_sent=True)
                while True:
                    context.checkpoint()
                    try:
                        current = resource.get(id=interaction_id, include_input=False, timeout=30)
                        if current.id != interaction_id:
                            raise AIBadRequest(MSG_BAD_REQUEST,
                                               "AI retrieval returned a different ID.")
                        retries = 0
                        break
                    except Exception as error:
                        translated = self._recovery_error(error, web_search=state.web_search)
                        if not isinstance(translated, (AIUnavailable, AIRateLimited)):
                            raise translated from error
                        retries += 1
                        if retries > 4:
                            raise AIConnectionError(MSG_CONNECTION,
                                                    "AI result retrieval remained unavailable.",
                                                    request_sent=True) from error
                        delay = getattr(translated, "retry_after", None) or min(2 ** retries, 30)
                        if time.monotonic() + delay >= deadline:
                            raise AIConnectionError(MSG_CONNECTION,
                                                    "AI result retrieval exceeded its deadline.",
                                                    request_sent=True) from error
                        context.progress("Recovering the same AI request after a connection "
                                         "problem; no new generation is being sent")
                        context.wait(delay, retry=True)
        except BaseException as error:
            failure = error
            raise
        finally:
            if interaction_id:
                try:
                    self._cleanup_interaction(interaction_id, state, finished=finished,
                                              context=context)
                except Exception:
                    log.exception("AI recovery cleanup could not finish")
                    context.notify("Temporary AI-provider cleanup could not finish. "
                                   "The original search outcome is preserved.")
                finally:
                    request_recovery.unclaim(context.provider, interaction_id)
            if failure is not None and interaction_id:
                # Cancellation may deliver the final bill even when Stop interrupted polling.
                failure.usage = state.usage(interrupted=not state.final_usage)
                failure.recovery_id = interaction_id

    def _stream(self, model: str, prompt: str, config: types.GenerateContentConfig,
                *, web_search: bool = False) -> ResearchReply:
        """Receive long answers in chunks; publish only a complete, successful answer.

        Metadata can arrive separately from text, and repeated cumulative counts are not
        additional tokens/queries. Keep every source and ignore thought text, as the SDK's
        ordinary response.text does. A broken stream never supplies a partial judgement.
        """
        text, sources, supports, grounding_chunks = [], [], [], []
        queries: Counter[str] = Counter()
        counts: Counter[str] = Counter()
        finished = False
        usage_seen = interrupted = False
        stream = None
        query_billed = not model.removeprefix("models/").startswith("gemini-2.")
        started = time.monotonic()
        chunks_received = 0
        self._stream_responses.current = []
        try:
            stream = self._client().models.generate_content_stream(
                model=model, contents=prompt, config=config)
            for response in stream:
                chunks_received += 1
                feedback = response.prompt_feedback
                if feedback is not None and feedback.block_reason:
                    raise AIRefused(MSG_REFUSED, str(feedback.block_reason))
                meta = response.usage_metadata
                if meta is not None:
                    usage_seen = True
                    counts |= Counter({name: getattr(meta, name) or 0 for name in (
                        "prompt_token_count", "candidates_token_count",
                        "cached_content_token_count", "thoughts_token_count")})
                candidate = response.candidates[0] if response.candidates else None
                if candidate is None:
                    continue  # final usage can arrive without another text candidate
                grounding = candidate.grounding_metadata
                if grounding is not None:
                    queries |= Counter(grounding.web_search_queries or [])
                    for chunk in grounding.grounding_chunks or []:
                        web = chunk.web
                        if web is not None and web.uri:
                            sources.append(Source(web.uri, web.title or ""))
                    # Streaming support indices refer to chunks accumulated in arrival order.
                    grounding_chunks.extend(grounding.grounding_chunks or [])
                    for support in grounding.grounding_supports or []:
                        words = support.segment.text if support.segment else None
                        if words:
                            supports.append((words, support.grounding_chunk_indices or []))
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
            if not finished:
                raise AIConnectionError(MSG_CONNECTION,
                                        "AI answer stream ended before completion.",
                                        request_sent=True)
        except Exception as exc:
            if isinstance(exc, httpx.TransportError):
                log.info(
                    "AI stream connection interrupted after %.1fs: headers_received=%s, "
                    "chunks_received=%d, completion_received=%s, usage_received=%s, kind=%s",
                    time.monotonic() - started, bool(self._stream_responses.current),
                    chunks_received, finished, usage_seen, type(exc).__name__,
                )
            # STOP is the provider's successful terminal outcome, not merely valid JSON.
            # A later body disconnect cannot undo it. Keep metadata already received;
            # unknown trailing usage remains explicit rather than repeating paid work.
            if finished and isinstance(exc, httpx.TransportError):
                interrupted = True
            else:
                translated = _translate(exc, web_search=web_search)
                if (isinstance(translated, AIError)
                        and not (isinstance(translated, AIConnectionError)
                                 and translated.request_sent is False)
                        and (usage_seen or queries
                             or isinstance(translated, (AIUnavailable, AIOutputTruncated)))):
                    translated.usage = _usage(counts, queries, unreported=True,
                                              query_billed=query_billed)
                raise translated from exc
        finally:
            # The SDK's synchronous iterator does not close an interrupted HTTP body.
            # Close only this thread's responses; keep the shared client/pool alive.
            responses = self._stream_responses.current
            del self._stream_responses.current
            for resource in [stream, *responses]:
                if resource is None:
                    continue
                try:
                    resource.close()
                except httpx.TransportError:
                    # Cleanup cannot undo STOP or replace a meaningful refusal/
                    # truncation error and its usage with another connection retry.
                    interrupted = True
        notes = "".join(text)
        citations = {}
        for words, indexes in supports:
            if notes.count(words) != 1:
                continue
            for index in indexes:
                if 0 <= index < len(grounding_chunks):
                    web = grounding_chunks[index].web
                    if web and web.uri:
                        citations[words, web.uri] = Citation(words, web.uri)
        return ResearchReply(
            text=notes,
            sources=unique_sources(sources),
            usage=_usage(counts, queries, unreported=interrupted or not usage_seen,
                         query_billed=query_billed),
            # Segment offsets refer to provider parts in UTF-8 bytes, not Python character
            # offsets across streamed chunks. Require unique literal text instead of guessing.
            citations=list(citations.values()) if web_search else None,
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


def _capacity_refusal(error: Exception) -> bool:
    """An answered refusal (busy or too many requests), not a broken connection."""
    return (isinstance(error, (AIUnavailable, AIRateLimited))
            and not isinstance(error, AIConnectionError))


def _name(value) -> str:
    return getattr(value, "name", None) or str(value or "")


def _usage(counts: Counter, queries: Counter, *, unreported: bool,
           query_billed: bool = True) -> Usage:
    thoughts = counts["thoughts_token_count"]
    searches = len({query.strip() for query in queries if query.strip()})
    return Usage(
        input_tokens=counts["prompt_token_count"],
        output_tokens=counts["candidates_token_count"] + thoughts,
        cached_input_tokens=counts["cached_content_token_count"],
        reasoning_tokens=thoughts,
        # Google bills unique nonempty queries within a request, not repeated cumulative
        # grounding metadata. Keep the same query chargeable again in a separate request.
        web_searches=searches if query_billed else int(bool(searches)),
        unreported_requests=int(unreported),
    )


def _translate(exc: Exception, *, web_search: bool = False) -> Exception:
    detail = str(exc)
    if isinstance(exc, errors.APIError):
        status = (exc.status or "").upper()
        text = f"{status} {exc.message or ''} {exc.details or ''}"
        if "API_KEY_INVALID" in text or "API key not valid" in text or exc.code == 401:
            return AIAuthError(MSG_KEY_REJECTED, detail)
        if exc.code == 402 or ("credit" in text.lower() and any(
                word in text.lower() for word in ("depleted", "exhausted", "insufficient"))):
            return AIQuotaExhausted(
                "The AI provider says your credit is depleted or payment is required. "
                "Jobcu won't retry this billing refusal. Check the provider's billing page.",
                detail,
            )
        if _spend_cap_reached(exc.message or ""):
            return AIQuotaExhausted(
                "The AI provider says a monthly spending cap has been reached. "
                "Jobcu won't retry this account refusal. Check the project's and billing "
                "account's cap/status on the provider's billing page before another search.",
                detail,
            )
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
            return AIAuthError(
                "The AI provider refused access. Check key permissions and the project's "
                "billing or spending-cap status. This refusal alone does not identify "
                "which caused it.", detail,
            )
        if exc.code == 404:
            return AIModelNotFound(MSG_MODEL_NOT_FOUND, detail)
        if exc.code and exc.code >= 500:
            return AIUnavailable(MSG_UNAVAILABLE, detail)
        if exc.code == 400 and reasoning_control_refused(exc.message, (
                "thinking", "thinking level", "thinking_level", "thinkingLevel",
                "thinking_config", "thinkingConfig")):
            return AIReasoningUnsupported(MSG_BAD_REQUEST, detail)
        return AIBadRequest(MSG_BAD_REQUEST, detail)
    if isinstance(exc, httpx.TransportError):
        return connection_problem(exc)
    if isinstance(exc, httpx.HTTPError):
        return AIUnavailable(MSG_UNAVAILABLE, detail)
    if isinstance(exc, AIError):
        return exc
    return AIBadRequest(MSG_BAD_REQUEST, detail)


def _spend_cap_reached(message: str) -> bool:
    """A stated monthly cap is terminal; a generic 403 cannot establish its cause."""
    text = message.casefold().replace("_", " ")
    cap = r"(?:monthly (?:spend(?:ing)? |billing )?(?:cap|limit)|spend(?:ing)? cap)"
    return bool(re.search(
        rf"\b(?:{cap}(?: has been| is)? (?:reached|exceeded|exhausted)"
        rf"|(?:reached|reaching|exceeded|exhausted) (?:the |your |its |a )?{cap})\b", text))


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
