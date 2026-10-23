"""The one place where Jobcu asks an AI anything.

Every AI request in Jobcu goes through `AIClient.generate`, which:
- picks the provider and model from the user's settings
- checks the user's monthly limit first
- waits and retries on rate limits and short outages, without losing progress
- sends a few requests at a time for steps with many (`in_parallel`), and only one at a time
  once the provider has said "too many requests"
- preserves explicit custom reasoning controls; handles legacy native model settings
- checks the answer against the expected format, and asks once more if it's wrong
- records the tokens used
"""

import hashlib
import json
import logging
import random
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ClassVar, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from jobcu.ai import budgets
from jobcu.ai.base import (
    MSG_NO_WEB_SEARCH,
    MSG_RATE_LIMITED,
    AIAuthError,
    AIConnectionError,
    AIError,
    AIInvalidOutput,
    AILimitReached,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRateLimited,
    AIReasoningUnsupported,
    AIUnavailable,
    AIUsageUncertain,
    AIWebSearchUnavailable,
    ProviderAdapter,
    ResearchReply,
    Usage,
)
from jobcu.ai.providers import PROVIDERS, configured_adapter
from jobcu.ai.request_recovery import RecoveryContext
from jobcu.ai.schema import extract_json, strict_json_schema
from jobcu.ai.usage import UsageLog, estimate_cost, total_tokens
from jobcu.keystore import KeyStore
from jobcu.settings import Effort, Settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

MAX_RATE_LIMIT_WAITS = 10
MAX_OUTAGE_RETRIES = 4
MAX_WAIT_SECONDS = 300

# Requests sent at the same time by a step with many of them (scoring, the quick check, the look
# at career-site titles, the online look-up). One at a time, search 10 (2026-09-30) spent 36 of
# its 46 minutes waiting for them. Paid tiers allow far more than this; a free tier may not, so
# the first "too many requests" answer puts the rest of the search back to one at a time.
PARALLEL_REQUESTS = 4


# Thinking counts towards the output limit with every provider, but only what is used is paid
# for. Each request gets this room on top of its answer: without it, medium thinking cut off the
# answer of the step that sorts location conditions (2,000 tokens), and Jobcu fell back to
# looking everything up on the web (2026-09-24).
THINKING_ROOM = {"minimal": 1_000, "low": 4_000, "medium": 12_000, "high": 16_000}
MAX_OUTPUT_TOKENS = 32_000  # within every current provider's own limit
# Web look-ups allowed in one search when Settings has no limit (the person answered "Always").
NO_LIMIT = 1_000_000


def with_thinking_room(max_output_tokens: int, effort: Effort | None) -> int:
    return min(max_output_tokens + THINKING_ROOM.get(effort or "", 0),
               max(max_output_tokens, MAX_OUTPUT_TOKENS))


class AIClient:
    # Explicitly unsupported native reasoning controls with a successful fallback.
    _effort_unsupported: ClassVar[set[tuple[str, str]]] = set()

    def __init__(
        self,
        settings: Settings,
        keys: KeyStore | None = None,
        *,
        usage_log: UsageLog | None = None,
        search_id: int | None = None,
        notify: Callable[[str], None] | None = None,
        patient: bool = True,
        sleep: Callable[[float], None] = time.sleep,
        adapter: ProviderAdapter | None = None,
        research_adapter: ProviderAdapter | None = None,
        checkpoint: Callable[[], None] | None = None,
        on_wait: Callable[[float], None] | None = None,
        on_progress: Callable[[str], None] | None = None,
        reference_research_cache: dict | None = None,
        capture=None,
        budget_id: str | None = None,
    ) -> None:
        self.settings = settings
        self.keys = keys or KeyStore()
        self.usage_log = usage_log
        self.search_id = search_id
        self.budget_id = budget_id or (budgets.for_search(search_id)
                                       if search_id is not None else None)
        self.notify = notify or (lambda message: None)
        self.patient = patient  # False for quick checks: report limits instead of waiting
        self.sleep = sleep
        self.checkpoint = checkpoint or (lambda: None)
        self._cancellable = checkpoint is not None
        self.on_wait = on_wait or (lambda seconds: None)
        self.on_progress = on_progress or (lambda message: None)
        self.capture = capture
        self._adapter = adapter
        self._session_id = str(uuid4())
        self._research_adapter = research_adapter
        self._reasoning_note_sent = False
        self._native_reasoning_notices: set[str] = set()
        # Web look-ups used in this search, against the cap in Settings, and those promised to
        # requests still running, so requests sent together never go past the cap.
        previous = (usage_log.for_search(search_id)
                    if usage_log is not None and search_id is not None else {})
        # Employer discovery has its own allowance (own_web_searches), also after reopening.
        self.web_searches_used = sum(u.web_searches for step, u in previous.items()
                                    if step != "employers")
        self._web_searches_reserved = 0
        # How many requests may be waiting for an answer at the same time (see `_slot`).
        self.parallel_requests = PARALLEL_REQUESTS
        self._requests_running = 0
        self._endpoint_running: dict[tuple[str, str, bool], int] = {}
        self._connection_recovery: set[tuple[str, str, bool]] = set()
        self._uncertain_requests: dict[tuple[str, str, bool], AIError] = {}
        self._gate = threading.Condition()
        self._adapter_lock = threading.Lock()
        # Remember a definite capability refusal for this search only. A later search
        # gets a fresh client, so changing a model or enabling billing takes effect.
        self._web_unavailable: str | None = None
        self._quota_errors: dict[tuple[str, str], AIQuotaExhausted] = {}
        self._failed_research: set[str] = set()
        # Transient same-search recovery only: never serialized, shared with another search
        # or used as a general provider-answer/scoring cache.
        self.reference_research_cache = (reference_research_cache
                                         if reference_research_cache is not None else {})

    @property
    def provider_id(self) -> str:
        provider = self.settings.ai.provider
        if provider is None:
            raise AIAuthError("Please choose an AI provider in Settings first.")
        return provider

    def model_for(self, reasoning: bool) -> str:
        ai = self.settings.ai
        model = (ai.reasoning_model if reasoning and ai.reasoning_model else ai.model).strip()
        if not model:
            raise AIAuthError("Please choose an AI model in Settings first.")
        return model

    def adapter(self) -> ProviderAdapter:
        with self._adapter_lock:
            if self._adapter is None:
                self._adapter = self._make_adapter(self.provider_id)
        return self._adapter

    def _make_adapter(self, provider: str) -> ProviderAdapter:
        info = PROVIDERS[provider]
        key = self.keys.get(info.key_name) or ""
        if not key and not info.key_optional:
            raise AIAuthError("Please enter your AI key in Settings first.")
        if info.needs_base_url and not self.settings.ai.base_url.strip():
            raise AIAuthError("Please enter the provider's address in Settings first.")
        return configured_adapter(provider, key, self.settings.ai, session_id=self._session_id)

    def research_endpoint(self) -> tuple[str, str, ProviderAdapter]:
        ai = self.settings.ai
        if ai.research_provider is None:
            return self.provider_id, self.model_for(True), self.adapter()
        model = ai.research_model.strip()
        if not model:
            raise AIAuthError("Please choose the online research model in Settings first.")
        with self._adapter_lock:
            if self._research_adapter is None:
                self._research_adapter = self._make_adapter(ai.research_provider)
        return ai.research_provider, model, self._research_adapter

    @contextmanager
    def _slot(self, endpoint: tuple[str, str, bool]) -> Iterator[None]:
        """Keep interrupted paths to one real request until a complete answer restores them."""
        with self._gate:
            recovery_wait = 0.0
            try:
                while True:
                    recovering = (endpoint in self._connection_recovery
                                  and self._endpoint_running.get(endpoint, 0) >= 1)
                    if self._requests_running < self.parallel_requests and not recovering:
                        break
                    self.checkpoint()
                    started = time.monotonic()
                    try:
                        self._gate.wait(timeout=0.25)
                    finally:
                        if recovering:
                            recovery_wait += max(0, time.monotonic() - started)
                self.checkpoint()
            finally:
                if recovery_wait:
                    log.info("AI connection recovery queue wait finished: elapsed=%.3fs "
                             "request_kind=%s", recovery_wait,
                             "research" if endpoint[2] else "structured")
            self._requests_running += 1
            self._endpoint_running[endpoint] = self._endpoint_running.get(endpoint, 0) + 1
        try:
            yield
        finally:
            with self._gate:
                self._requests_running -= 1
                self._endpoint_running[endpoint] -= 1
                self._gate.notify_all()

    @contextmanager
    def _request(self, step: str, provider: str, model: str,
                 *, research: bool = False) -> Iterator[None]:
        """Every dispatch, including repairs/retries, obeys Stop and recorded limits."""
        self.checkpoint()
        endpoint = provider, model, research
        with self._slot(endpoint):
            with self._gate:
                quota = self._quota_errors.get((provider, model))
                uncertain = self._uncertain_requests.get(endpoint)
            if quota is not None:
                raise quota
            if uncertain is not None:
                raise uncertain
            self._check_monthly_limit(provider=provider, model=model, research=research)
            attempt = uuid4().hex[:12]
            started = time.monotonic()
            outcome = "complete"
            request_kind = "research" if research else "structured"
            log.info("AI attempt started: id=%s step=%s request_kind=%s",
                     attempt, step, request_kind)
            try:
                yield
            except AIError as exc:
                outcome = type(exc).__name__
                if isinstance(exc, AIUsageUncertain):
                    with self._gate:
                        self._uncertain_requests[endpoint] = exc
                    self.notify(exc.message)
                if isinstance(exc, AIConnectionError):
                    with self._gate:
                        self._connection_recovery.add(endpoint)
                        if exc.request_sent is True:
                            self._uncertain_requests[endpoint] = exc
                    if exc.request_sent is True:
                        self.notify("The AI provider may already have charged for the interrupted "
                                    "request. Jobcu kept completed work and stopped automatic "
                                    "requests on this path. Retry incomplete checks explicitly "
                                    "after checking service and billing.")
                usage = exc.usage
                if usage is None and isinstance(exc, (AIUnavailable, AIOutputTruncated)):
                    unsent = isinstance(exc, AIConnectionError) and exc.request_sent is False
                    usage = Usage(unreported_requests=0 if unsent else 1)
                guard = None
                if (research and isinstance(exc, (AIUnavailable, AIRateLimited))
                        and usage is not None and usage.web_searches > 0
                        and usage.unreported_requests
                        and not (isinstance(exc, AIConnectionError)
                                 and exc.request_sent is True)):
                    # A tool ran before a service/rate failure. Repeating it may buy the
                    # same research again, while its missing bill defeats the local cap.
                    guard = AIUsageUncertain(
                        "Online research failed after using search tools, without complete "
                        "usage. Jobcu kept completed work and stopped automatic research on "
                        "this path. Check service and billing before explicitly retrying "
                        "incomplete checks.", exc.detail)
                    guard.usage = usage
                    guard.recovery_id = exc.recovery_id
                    with self._gate:
                        first = endpoint not in self._uncertain_requests
                        self._uncertain_requests[endpoint] = guard
                    if first:
                        self.notify(guard.message)
                if usage is not None:
                    self._record(step, provider, model, usage, recovery_id=exc.recovery_id)
                    if research:
                        with self._gate:
                            self.web_searches_used += usage.web_searches
                if isinstance(exc, AIQuotaExhausted):
                    with self._gate:
                        first = (provider, model) not in self._quota_errors
                        self._quota_errors[(provider, model)] = exc
                    if first:
                        # Discovery/ad checks can retain partial results after an account
                        # refusal. Surface its reason even when their caller catches it.
                        self.notify(exc.message)
                if guard is not None:
                    outcome = type(guard).__name__
                    raise guard from exc
                raise
            except BaseException as exc:
                # Stop can cancel a background request which already incurred a bill.
                outcome = type(exc).__name__
                usage = getattr(exc, "usage", None)
                if isinstance(usage, Usage):
                    self._record(step, provider, model, usage,
                                 recovery_id=getattr(exc, "recovery_id", None))
                    if research:
                        with self._gate:
                            self.web_searches_used += usage.web_searches
                raise
            else:
                with self._gate:
                    self._connection_recovery.discard(endpoint)
            finally:
                log.info("AI attempt finished: id=%s step=%s elapsed=%.3fs outcome=%s "
                         "request_kind=%s", attempt, step,
                         max(0, time.monotonic() - started), outcome, request_kind)

    def _one_at_a_time(self) -> None:
        """The provider said "too many requests": the rest of this search asks one at a time,
        as a free tier's per-minute limit expects."""
        with self._gate:
            self.parallel_requests = 1

    def generate(
        self,
        output: type[T],
        *,
        step: str,
        system: str,
        prompt: str,
        reasoning: bool = False,
        max_output_tokens: int = 4000,
    ) -> T:
        provider = self.provider_id
        model = self.model_for(reasoning)
        adapter = self.adapter()
        self._note_native_reasoning(adapter)
        self._check_monthly_limit()

        effort = self.settings.ai.reasoning_effort if reasoning else self.settings.ai.scoring_effort
        if not getattr(adapter, "strict_reasoning", False) and (
                (provider, model) in self._effort_unsupported):
            effort = None
        if provider == "openai_compatible":
            self._note_custom_reasoning()
        schema = strict_json_schema(output)
        request_prompt = prompt
        rate_waits = outage_retries = 0
        effort_dropped = truncation_retried = repair_used = False

        while True:
            try:
                with self._request(step, provider, model):
                    reply = self._call_adapter(adapter.complete_json, step, provider,
                        model=model,
                        system=system,
                        prompt=request_prompt,
                        schema=schema,
                        schema_name=output.__name__,
                        effort=effort,
                        max_output_tokens=with_thinking_room(max_output_tokens, effort),
                    )
                    self._record(step, provider, model, reply.usage,
                                 recovery_id=reply.recovery_id)
            except AIRateLimited as exc:
                self._one_at_a_time()
                rate_waits += 1
                if not self.patient or rate_waits > MAX_RATE_LIMIT_WAITS:
                    raise
                self.notify(MSG_RATE_LIMITED)
                self._wait(exc.retry_after or min(10 * 2 ** (rate_waits - 1), 120), exc,
                           retry=rate_waits, maximum=MAX_RATE_LIMIT_WAITS)
                continue
            except AIUnavailable as exc:
                outage_retries += 1
                if (isinstance(exc, AIConnectionError) and exc.request_sent is True
                        or not self.patient or outage_retries > MAX_OUTAGE_RETRIES):
                    raise
                self._wait(min(5 * 2 ** (outage_retries - 1), 60), exc,
                           retry=outage_retries, maximum=MAX_OUTAGE_RETRIES)
                continue
            except AIReasoningUnsupported:
                if getattr(adapter, "strict_reasoning", False):
                    raise
                if effort is not None:
                    # Only a definite control refusal permits this compatibility retry.
                    effort, effort_dropped = None, True
                    continue
                raise
            except AIOutputTruncated:
                if truncation_retried:
                    raise
                truncation_retried = True
                max_output_tokens *= 2
                continue

            self.checkpoint()
            try:
                answer = output.model_validate(extract_json(reply.text))
            except (ValueError, ValidationError) as exc:
                if repair_used:
                    raise AIInvalidOutput(
                        "The AI's answer wasn't in the format Jobcu needs, even after asking "
                        "again. A different model may work better.",
                        str(exc)[:500],
                    ) from exc
                repair_used = True
                request_prompt = (
                    f"{prompt}\n\nIMPORTANT: your previous answer did not follow the required "
                    "JSON format. Answer again with only valid JSON in exactly that format."
                )
                continue
            if effort_dropped:
                self._effort_unsupported.add((provider, model))
            return answer

    def _web_search_cap(self) -> int:
        cap = self.settings.limits.web_search_cap
        return NO_LIMIT if cap is None else cap

    def web_searches_left(self) -> int:
        """What is left of this search's allowance of web look-ups (Settings)."""
        return self._web_search_cap() - self.web_searches_used - self._web_searches_reserved

    def allow_more_web_searches(self, count: int | None = None) -> None:
        """The person said yes to more web look-ups: this many more for this search (by
        default another allowance as big as the one in Settings)."""
        more = self._web_search_cap() if count is None else count
        self.web_searches_used = min(self.web_searches_used, self._web_search_cap())
        self.web_searches_used -= more

    @contextmanager
    def own_web_searches(self, count: int) -> Iterator[None]:
        """Web look-ups for a step with its own allowance of `count`, outside the search's
        allowance in Settings: what the step uses is never taken from the rest of the search."""
        with self._gate:
            before = self.web_searches_used
            self.web_searches_used = min(before, self._web_search_cap()) - count
        try:
            yield
        finally:
            with self._gate:
                self.web_searches_used = before

    def research(
        self,
        *,
        step: str,
        system: str,
        prompt: str,
        max_searches: int = 4,
        max_output_tokens: int = 3000,
        effort: Effort | None = None,
    ) -> ResearchReply:
        """Ask the AI to look something up on the web and say which pages it used. The
        reasoning effort is the person's setting for reasoning steps unless `effort` says.

        Used for conditions Jobcu can only answer by checking current information.
        The user's own AI provider does the searching; Jobcu never contacts
        a search engine itself.
        """
        reason = self.web_research_unavailable_reason()
        if reason:
            raise AIWebSearchUnavailable(reason)
        provider, model, adapter = self.research_endpoint()
        self._note_native_reasoning(adapter)
        self._check_monthly_limit()
        with self._gate:
            allowed = min(max_searches, self.web_searches_left())
            if allowed <= 0:
                raise AILimitReached(
                    "Jobcu has used this search's allowance of web look-ups. You can raise it "
                    "in Settings."
                )
            self._web_searches_reserved += allowed
        held = allowed

        def completed(usage: Usage) -> None:
            nonlocal held
            with self._gate:
                self.web_searches_used += max(1, usage.web_searches)
                self._web_searches_reserved -= held
                held = 0

        try:
            reply = self._research(adapter, provider, model, step, system, prompt, allowed,
                                   max_output_tokens, effort, completed)
        finally:
            with self._gate:
                self._web_searches_reserved -= held
        self.checkpoint()
        return reply

    def web_research_unavailable_reason(self) -> str | None:
        if not self.settings.use_web_search:
            return (
                "Looking things up on the web is switched off in Settings, so anything that "
                'needs checking is shown as "not checked".'
            )
        if self._web_unavailable:
            return self._web_unavailable
        if not self.research_endpoint()[2].can_search_the_web:
            return MSG_NO_WEB_SEARCH
        return None

    def _note_native_reasoning(self, adapter: ProviderAdapter) -> None:
        notice = getattr(adapter, "reasoning_notice", None)
        if notice:
            with self._gate:
                first = notice not in self._native_reasoning_notices
                self._native_reasoning_notices.add(notice)
            if first:
                self.notify(notice)

    def _note_custom_reasoning(self) -> None:
        ai = self.settings.ai
        if ai.compatible_protocol != "chat_completions":
            return
        message = None
        if ai.compatible_reasoning == "provider_default":
            message = "This custom API uses its own reasoning default; Jobcu cannot confirm " \
                      "the selected effort. Check its reasoning controls in Settings."
        elif ai.compatible_reasoning == "thinking":
            message = "This custom API is asked to enable thinking. It does not receive a " \
                      "medium effort level; its thinking depth is provider controlled."
        elif ai.compatible_medium != "medium":
            message = f"This custom API receives {ai.compatible_medium} for Jobcu's medium " \
                      "setting. This is a native mapping, not measured equivalent effort."
        with self._gate:
            first = message is not None and not self._reasoning_note_sent
            if first:
                self._reasoning_note_sent = True
        if first:
            self.notify(message)

    def _research(self, adapter: ProviderAdapter, provider: str, model: str, step: str, system: str,
                  prompt: str, max_searches: int, max_output_tokens: int,
                  effort: Effort | None, completed: Callable[[Usage], None]) -> ResearchReply:
        effort = effort or self.settings.ai.reasoning_effort
        if not getattr(adapter, "strict_reasoning", False) and (
                (provider, model) in self._effort_unsupported):
            effort = None
        request_key = hashlib.sha256(json.dumps([
            provider, model, system, prompt, max_searches, max_output_tokens, effort,
        ], ensure_ascii=False).encode("utf-8")).hexdigest()
        with self._gate:
            failed = request_key in self._failed_research
        if failed:
            raise AIConnectionError(
                "This identical online check already exhausted its connection retries in "
                "this search. Jobcu keeps completed work and leaves missing facts unchecked; "
                "different checks can still run."
            )
        waits = outages = 0
        effort_dropped = False
        while True:
            try:
                with self._request(step, provider, model, research=True):
                    if self._web_unavailable:
                        raise AIWebSearchUnavailable(self._web_unavailable)
                    with self._gate:
                        allowed = min(max_searches, self.web_searches_left() + max_searches)
                    if allowed <= 0:
                        raise AILimitReached("Jobcu has used this search's allowance of web "
                                             "look-ups, including failed attempts.")
                    reply = self._call_adapter(adapter.research, step, provider,
                        model=model,
                        system=system,
                        prompt=prompt,
                        max_searches=allowed,
                        max_output_tokens=with_thinking_room(max_output_tokens, effort),
                        effort=effort,
                    )
                    completed(reply.usage)
                    self._record(step, provider, model, reply.usage,
                                 recovery_id=reply.recovery_id)
            except AIWebSearchUnavailable as exc:
                with self._gate:
                    first = self._web_unavailable is None
                    self._web_unavailable = exc.message
                if first:
                    self.notify(exc.message)
                raise
            except AIReasoningUnsupported:
                if effort is None or getattr(adapter, "strict_reasoning", False):
                    raise
                effort, effort_dropped = None, True
            except AIRateLimited as exc:
                self._one_at_a_time()
                waits += 1
                if not self.patient or waits > MAX_RATE_LIMIT_WAITS:
                    raise
                self.notify(MSG_RATE_LIMITED)
                self._wait(exc.retry_after or min(10 * 2 ** (waits - 1), 120), exc,
                           retry=waits, maximum=MAX_RATE_LIMIT_WAITS)
            except AIUnavailable as exc:
                outages += 1
                if (isinstance(exc, AIConnectionError) and exc.request_sent is True
                        or not self.patient or outages > MAX_OUTAGE_RETRIES):
                    if (self.patient and isinstance(exc, AIConnectionError)
                            and exc.request_sent is not True):
                        with self._gate:
                            self._failed_research.add(request_key)
                        self.notify(
                            "An online check exhausted its connection retries. Jobcu won't "
                            "repeat the identical failed check in this search; independent "
                            "checks can continue. Failed requests may still have charges."
                        )
                    raise
                self._wait(min(5 * 2 ** (outages - 1), 60), exc,
                           retry=outages, maximum=MAX_OUTAGE_RETRIES)
            else:
                if effort_dropped and reply.text.strip():
                    self._effort_unsupported.add((provider, model))
                return reply

    def _wait(self, seconds: float, reason: AIError, *, retry: int, maximum: int) -> None:
        seconds = min(max(seconds, 1.0), MAX_WAIT_SECONDS) + random.uniform(0, 1)
        log.info("AI request waiting %.0fs: %s", seconds, reason.detail or reason.message)
        if isinstance(reason, AIUnavailable):
            problem = "connection problem" if isinstance(reason, AIConnectionError) \
                else "connection or service problem"
            self.notify(f"Some AI requests needed retries after a {problem}; "
                        "completed work was kept.")
        self.checkpoint()
        self.on_wait(seconds)
        self.on_progress(f"Waiting about {seconds:.0f} seconds before AI retry {retry} of "
                         f"{maximum}. Stop cancels waiting.")
        started = time.monotonic()
        if self.capture:
            self.capture.event("ai_wait_start", requested=seconds, retry=retry,
                               error=type(reason).__name__)
        try:
            if not self._cancellable:
                self.sleep(seconds)
            else:
                remaining = seconds
                while remaining > 0:
                    pause = min(remaining, 1.0)
                    self.sleep(pause)
                    remaining -= pause
                    self.checkpoint()
        finally:
            if self.capture:
                self.capture.event("ai_wait_end", started=started,
                                   elapsed=max(0, time.monotonic() - started))
            log.info("AI retry wait finished: elapsed=%.3fs requested=%.3fs kind=%s",
                     max(0, time.monotonic() - started), seconds, type(reason).__name__)
            self.on_wait(0)
            self.on_progress(f"Retrying an AI request ({retry} of {maximum})")

    def _call_adapter(self, method, step: str, provider: str, **arguments):
        adapter = getattr(method, "__self__", None)
        if isinstance(adapter, ProviderAdapter):
            def account(usage, request_id):
                if self.usage_log is not None:
                    self.usage_log.record(
                        step=step, provider=provider, model=arguments["model"], usage=usage,
                        search_id=self.search_id, recovery_id=request_id, budget_id=self.budget_id)

            def observe(usage, request_id):
                account(usage, request_id)
                self._check_monthly_limit(provider=provider, model=arguments["model"],
                                          research=method.__name__ == "research")

            adapter.configure_request_recovery(RecoveryContext(
                self.settings.ai.recover_interrupted_requests, provider, step,
                search_id=self.search_id, checkpoint=self.checkpoint, sleep=self.sleep,
                notify=self.notify, progress=self.on_progress, observe=observe,
                account=account, capture=self.capture, budget_id=self.budget_id))
        if self.capture:
            return self.capture.call(method, step=step, provider=provider, **arguments)
        return method(**arguments)

    def _record(self, step: str, provider: str, model: str, usage, *, recovery_id=None) -> None:
        if self.usage_log is not None:
            options = {"recovery_id": recovery_id} if recovery_id is not None else {}
            if self.budget_id is not None:
                options["budget_id"] = self.budget_id
            self.usage_log.record(
                step=step, provider=provider, model=model, usage=usage, search_id=self.search_id,
                **options,
            )
            if usage.unreported_requests:
                self.notify("Some AI requests did not report complete usage. Jobcu's estimate "
                            "may omit charges; check the provider's billing page.")

    def check_search_budget(self) -> None:
        """Check recorded limits before collection, even when setup answers are cached.

        This reads local usage only. It never constructs a provider adapter or sends a probe.
        Per-request checks still protect spending after a search starts.
        """
        ai = self.settings.ai
        models = {model for model in (ai.model, ai.reasoning_model) if model.strip()}
        if not models:
            self._check_monthly_limit()
        for model in models:
            self._check_monthly_limit(provider=ai.provider, model=model)

    def _check_monthly_limit(self, *, provider: str | None = None, model: str | None = None,
                             research: bool = False) -> None:
        if self.usage_log is None:
            return
        limits = self.settings.limits
        allowance = budgets.get(self.budget_id) if self.budget_id is not None else None
        if allowance is not None and not allowance.active:
            raise AILimitReached("This separate AI allowance is closed. Its spending is kept; "
                                 "Jobcu has not charged it to your ordinary monthly budget.")
        if allowance is None and (limits.monthly_token_limit is None
                                  and limits.monthly_cost_limit is None):
            return
        month = (self.usage_log.for_budget(allowance.id,
                    after_id=allowance.accounted_through_usage_id) if allowance else
                 getattr(self.usage_log, "ordinary_this_month", self.usage_log.this_month)())
        if allowance is None and limits.monthly_token_limit is not None and total_tokens(month) >= (
            limits.monthly_token_limit
        ):
            raise AILimitReached(
                "Your monthly AI limit in Jobcu's settings is reached, so Jobcu stopped using "
                "the AI. You can raise the limit in Settings."
            )
        if allowance is not None or limits.monthly_cost_limit is not None:
            prices = {(p.provider, p.model): p for p in self.settings.prices}
            needed = {(u.provider, u.model) for u in month if (
                u.usage.input_tokens or u.usage.output_tokens or u.usage.web_searches)}
            if provider is not None and model is not None:
                needed.add((provider, model))
            currencies = {p.currency.strip().upper() for p in self.settings.prices}
            missing = needed - prices.keys()
            web_unpriced = any(u.usage.web_searches and prices.get((u.provider, u.model))
                               is not None and prices[(u.provider, u.model)]
                               .web_search_per_thousand is None for u in month)
            if research and (provider, model) in prices:
                web_unpriced |= prices[(provider, model)].web_search_per_thousand is None
            if (missing or web_unpriced or len(currencies) != 1
                    or allowance is not None and currencies != {allowance.price_currency}):
                raise AILimitReached(
                    "Jobcu cannot apply this estimated spending limit until every "
                    "used model has input/output and applicable search prices in one currency. "
                    "Save current prices in Settings before continuing."
                )
            cost, _ = estimate_cost(month, self.settings.prices)
            if allowance is not None:
                if allowance.opening_spent + cost * allowance.cost_multiplier >= allowance.ceiling:
                    raise AILimitReached("This search's separate extra AI allowance is reached. "
                                         "Previous spending is retained and your ordinary "
                                         "monthly budget is unchanged.")
            elif cost >= limits.monthly_cost_limit:
                raise AILimitReached(
                    "Your monthly AI spending limit in Jobcu's settings is reached, so Jobcu "
                    "stopped using the AI. You can raise the limit in Settings."
                )


def in_parallel[Item, Result](
        client: AIClient, work: Callable[[Item], Result], items: Sequence[Item],
        on_done: Callable[[Item, Result], None] | None = None) -> list[Result]:
    """Runs `work` (which asks `client`) for every item, as many at a time as the client
    allows, and returns the results in the items' order. `on_done` is called here, in the
    calling thread, as each item finishes, so a step can show its progress. The first error
    stops the items not started yet and is raised here once the running ones have finished."""
    at_once = min(client.parallel_requests, len(items))
    if at_once <= 1:
        results = []
        for item in items:
            results.append(work(item))
            if on_done is not None:
                on_done(item, results[-1])
        return results
    done: dict[int, Result] = {}
    failure: BaseException | None = None
    with ThreadPoolExecutor(max_workers=at_once, thread_name_prefix="ai") as pool:
        futures = {pool.submit(work, item): position for position, item in enumerate(items)}
        for future in as_completed(futures):
            if future.cancelled():
                continue
            try:
                position = futures[future]
                done[position] = future.result()
                if on_done is not None:
                    on_done(items[position], done[position])
            except BaseException as exc:
                if failure is None:
                    failure = exc
                    for queued in futures:
                        queued.cancel()
                # Requests already running can finish with useful, billed evidence.
                # Deliver their checkpoints before propagating the original failure.
    if failure is not None:
        raise failure
    return [done[position] for position in range(len(items))]


# ---------------------------------------------------------------------------
# Setup check: does the key work, and does the model answer in Jobcu's format?
# ---------------------------------------------------------------------------


class _ConnectionProbe(BaseModel):
    ok: bool
    word: str


@dataclass
class CheckResult:
    ok: bool
    message: str


def check_setup(settings: Settings, keys: KeyStore | None = None, **client_args) -> CheckResult:
    client = AIClient(settings, keys, patient=False, **client_args)
    models = [client.model_for(False)] if settings.ai.model.strip() else []
    if settings.ai.reasoning_model.strip():
        models.append(client.model_for(True))
    if not models:
        return CheckResult(False, "Please choose an AI model first.")
    try:
        for reasoning in ([False, True] if len(models) == 2 else [False]):
            answer = client.generate(
                _ConnectionProbe,
                step="setup_check",
                system="You are a connection test for an app.",
                prompt='Reply with "ok" set to true and "word" set to "jobcu".',
                reasoning=reasoning,
                max_output_tokens=2000,
            )
            if not answer.ok or answer.word.strip().lower() != "jobcu":
                return CheckResult(
                    False,
                    "The model answered, but not correctly. A different model may work better.",
                )
    except AIRateLimited:
        return CheckResult(
            False,
            "The key works, but the AI provider says you've hit a short-term limit. "
            "Wait a minute and test again.",
        )
    except AIError as exc:
        log.warning("Setup check failed: %s", exc.detail or exc.message)
        return CheckResult(False, exc.message)
    if len(models) == 2:
        return CheckResult(True, "Connection works. Both models answer in the format Jobcu needs.")
    return CheckResult(True, "Connection works. The model answers in the format Jobcu needs.")


def check_research_setup(settings: Settings, keys: KeyStore | None = None,
                         **client_args) -> CheckResult:
    """An explicit generation probe for the separate research key/model, not a web lookup."""
    ai = settings.ai
    if ai.research_provider is None or not ai.research_model.strip():
        return CheckResult(False, "Please choose an online research provider and model first.")
    probe = settings.model_copy(deep=True)
    probe.ai.provider = ai.research_provider
    probe.ai.model = ai.research_model
    probe.ai.reasoning_model = ""
    probe.ai.research_provider = None
    probe.ai.research_model = ""
    result = check_setup(probe, keys, **client_args)
    if result.ok:
        result.message = "Research model connection works. Online search permission was not tested."
    return result
