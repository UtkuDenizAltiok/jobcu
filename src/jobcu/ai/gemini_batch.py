"""Google's Batch API: answers that can wait, at half the token price, when Flex is busy.

Flex (half price, answered in minutes) uses Google's spare capacity and is refused when the
model is busy: on 2026-11-28 Gemini 4 Hydrogen's Flex was refused at every attempt, in every
way of sending (plain, streamed, in the background), while the Batch API answered the same model
in about two minutes, also at half price. So when Flex is refused, structured requests that can
wait are gathered into one batch job instead of being sent at the normal price.

A batch job keeps its requests and answers at Google until Jobcu deletes it, like a recoverable
request, so it is used only with request recovery on. The job is in the recovery journal while it
runs: Stop cancels it, and a job left behind by a closed Jobcu is cancelled and deleted at the
next start (`GeminiAdapter.cleanup_pending`), its bill recorded. A job that gives no answer for
a request, fails, or takes longer than `PATIENCE_SECONDS` leaves that request to be sent the
normal way, so a search always finishes.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import uuid4

import httpx
from google.genai import errors, types

from jobcu.ai import request_recovery
from jobcu.ai.base import (
    MSG_REFUSED,
    MSG_TRUNCATED,
    AIOutputTruncated,
    AIRefused,
    RawReply,
    Usage,
)
from jobcu.ai.request_recovery import RecoveryContext
from jobcu.settings import Effort

log = logging.getLogger(__name__)

TIER = "batch"
# A job is sent once no new request has joined it for GATHER_QUIET_SECONDS, at most
# GATHER_MOST_SECONDS after its first request, or when it is full.
GATHER_QUIET_SECONDS = 3.0
GATHER_MOST_SECONDS = 30.0
# Requests waiting for batch answers at once (AIClient); also the most in one job. Google takes
# up to 20 MB of inline requests a job; a scoring request is about 40 KB.
MOST_REQUESTS = 100
MOST_CHARACTERS = 8_000_000
POLL_SECONDS = 15.0
# Google's target is 24 hours; measured 2.1-2.6 minutes for a small job (2026-11-28, 11:29 and
# 19:00 CET). A job still unanswered after an hour is cancelled, its requests go the normal way,
# and the search stops using Batch (a slow day would otherwise make every later job wait as long).
PATIENCE_SECONDS = 3600.0
# How long a cancelled job may take to end before its requests go the normal way.
CANCEL_SECONDS = 120.0
# A job whose every request Google refused is sent again once, this many seconds later.
JOB_ATTEMPTS = 2
AGAIN_SECONDS = 60.0
NOTICE = ("Google's half-price Flex processing was busy, so Jobcu sent the work that can wait "
          "through Google's Batch processing, also at half price. It can take a few minutes "
          "longer.")
UNAVAILABLE_NOTICE = ("Google's Batch processing didn't answer in time or isn't available, so "
                      "this search sends the rest of its work the normal way, at the normal price "
                      "while Flex is busy.")
_ENDED = {"JOB_STATE_SUCCEEDED", "JOB_STATE_PARTIALLY_SUCCEEDED", "JOB_STATE_FAILED",
          "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}
_REFUSAL_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}


class BatchUnanswered(Exception):
    """The batch gave no answer for this request: send it the normal way."""


@dataclass
class Answer:
    """What a finished job holds for one request."""

    response: types.GenerateContentResponse | None = None
    error: str = ""


@dataclass
class JobView:
    state: str
    answers: dict[str, Answer] = field(default_factory=dict)


class BatchService:
    """The Batch API calls Jobcu makes, through the google-genai library (tests replace it)."""

    def __init__(self, client: Callable[[], object]) -> None:
        self._client = client

    def create(self, model: str, display_name: str,
               requests: list[tuple[str, types.InlinedRequest]]) -> str:
        job = self._client().batches.create(
            model=model, src=[request for _, request in requests],
            config=types.CreateBatchJobConfig(display_name=display_name))
        return job.name

    def find(self, display_name: str) -> str | None:
        """The job of a create whose answer was lost: it may exist and be running."""
        for job in self._client().batches.list(config={"page_size": 50}):
            if job.display_name == display_name:
                return job.name
        return None

    def get(self, name: str, keys: list[str]) -> JobView:
        job = self._client().batches.get(name=name)
        state = getattr(job.state, "name", None) or str(job.state or "")
        found = (job.dest.inlined_responses if job.dest else None) or []
        answers: dict[str, Answer] = {}
        tagged = [(item.metadata or {}).get("key") for item in found]
        if found and all(tagged):
            pairs = zip(tagged, found, strict=True)
        elif keys and len(found) == len(keys):  # answers come in the order of the requests
            pairs = zip(keys, found, strict=True)
        else:  # only the bill can be read (cleanup of a job left behind)
            pairs = ((f"#{index}", item) for index, item in enumerate(found))
        for key, item in pairs:
            error = ""
            if item.error is not None:
                error = item.error.message or str(item.error.code or "error")
            answers[key] = Answer(item.response, error)
        return JobView(state, answers)

    def cancel(self, name: str) -> None:
        self._client().batches.cancel(name=name)

    def delete(self, name: str) -> None:
        self._client().batches.delete(name=name)


def request_for(key: str, *, system: str, prompt: str, schema: dict,
                effort: Effort | None, max_output_tokens: int) -> types.InlinedRequest:
    """The same structured request the event path sends, in the Batch API's form.

    The answer's format goes as Gemini's own schema (`response_schema`), not as JSON Schema
    (`response_json_schema`): on 2026-11-28 a batch request ignored a JSON Schema (asked for
    "town_name" and "country_code", it answered {"city": "London"}) and followed the same
    schema given the other way, while plain requests followed both. The library carries the
    properties' order over ("propertyOrdering"), so the evidence is still written before the
    scores; "additionalProperties" has no place in that form and is left out (the answer is
    validated against the full model either way)."""
    return types.InlinedRequest(
        contents=prompt,
        metadata={"key": key},
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=_without(schema, "additionalProperties"),
            max_output_tokens=max_output_tokens,
            thinking_config=(types.ThinkingConfig(thinking_level=effort.upper())
                             if effort else None),
        ),
    )


def _without(node, word: str):
    if isinstance(node, dict):
        return {key: _without(value, word) for key, value in node.items() if key != word}
    if isinstance(node, list):
        return [_without(value, word) for value in node]
    return node


def reply_from(response: types.GenerateContentResponse) -> RawReply:
    """The answer and its bill, or the refusal/truncation the normal path would raise."""
    meta = response.usage_metadata
    thoughts = (meta.thoughts_token_count or 0) if meta else 0
    usage = Usage(
        input_tokens=(meta.prompt_token_count or 0) if meta else 0,
        output_tokens=((meta.candidates_token_count or 0) + thoughts) if meta else 0,
        cached_input_tokens=(meta.cached_content_token_count or 0) if meta else 0,
        reasoning_tokens=thoughts,
        unreported_requests=0 if meta else 1,
        service_tier=TIER,
    )
    feedback = response.prompt_feedback
    if feedback is not None and feedback.block_reason:
        error = AIRefused(MSG_REFUSED, str(feedback.block_reason))
        error.usage = usage
        raise error
    candidate = response.candidates[0] if response.candidates else None
    if candidate is None:
        raise BatchUnanswered("no answer in the batch result")
    finish = getattr(candidate.finish_reason, "name", None) or str(candidate.finish_reason or "")
    if finish == "MAX_TOKENS":
        error = AIOutputTruncated(MSG_TRUNCATED)
        error.usage = usage
        raise error
    if finish in _REFUSAL_REASONS or finish not in ("", "FINISH_REASON_UNSPECIFIED", "STOP"):
        error = AIRefused(MSG_REFUSED, finish)
        error.usage = usage
        raise error
    parts = candidate.content.parts if candidate.content is not None else None
    text = "".join(part.text for part in parts or [] if part.text and not part.thought)
    return RawReply(text, usage)


@dataclass
class _Item:
    key: str
    request: types.InlinedRequest
    characters: int
    context: RecoveryContext
    done: threading.Event = field(default_factory=threading.Event)
    reply: RawReply | None = None
    error: BaseException | None = None
    stopped: bool = False


@dataclass
class _Group:
    model: str
    started: float
    last: float
    items: list[_Item] = field(default_factory=list)
    closed: bool = False

    def room_for(self, characters: int) -> bool:
        return (not self.closed and len(self.items) < MOST_REQUESTS
                and sum(item.characters for item in self.items) + characters
                <= MOST_CHARACTERS)


class BatchQueue:
    """Gathers the structured requests of one search's threads into batch jobs, one model each.

    The first request of a job leads it: it waits for others to join, sends the job, polls it
    and hands every request its answer; the others wait for theirs. Every request's bill is
    recorded with its own context, also when its thread stopped waiting.
    """

    def __init__(self, service: BatchService, *, clock: Callable[[], float] = time.monotonic,
                 pause: Callable[[float], None] = time.sleep) -> None:
        self.service = service
        self.clock = clock
        self.pause = pause  # waiting for other requests to join (real time; tests shorten it)
        self.quiet = GATHER_QUIET_SECONDS
        self.most = GATHER_MOST_SECONDS
        self.poll = POLL_SECONDS
        self.patience = PATIENCE_SECONDS
        self.again = AGAIN_SECONDS
        self._lock = threading.Condition()
        self._groups: dict[str, _Group] = {}
        # Set when Batch didn't answer in time or refused the model: this search stops using it.
        self.unavailable = False

    def ask(self, *, model: str, system: str, prompt: str, schema: dict,
            effort: Effort | None, max_output_tokens: int, context: RecoveryContext) -> RawReply:
        """This request's answer from a batch job. Raises BatchUnanswered when the job gave
        none, so the caller sends it the normal way."""
        key = uuid4().hex[:16]
        item = _Item(key, request_for(key, system=system, prompt=prompt, schema=schema,
                                      effort=effort, max_output_tokens=max_output_tokens),
                     len(system) + len(prompt), context)
        with self._lock:
            if self.unavailable:
                raise BatchUnanswered("Batch is not used for the rest of this search")
            now = self.clock()
            group = self._groups.get(model)
            leads = group is None or not group.room_for(item.characters)
            if leads:
                group = self._groups[model] = _Group(model, now, now)
            group.items.append(item)
            group.last = now
            self._lock.notify_all()
        if leads:
            self._lead(group, context)
        else:
            self._wait(item)
        if item.error is not None:
            raise item.error
        if item.reply is None:
            raise BatchUnanswered("no answer in the batch result")
        return item.reply

    def _wait(self, item: _Item) -> None:
        while not item.done.wait(1.0):
            item.context.checkpoint()
        if item.stopped:
            item.context.checkpoint()  # the search was stopped: raise that here, too

    def _gather(self, group: _Group, context: RecoveryContext) -> None:
        while True:
            with self._lock:
                now = self.clock()
                if (len(group.items) >= MOST_REQUESTS or now - group.last >= self.quiet
                        or now - group.started >= self.most):
                    group.closed = True
                    if self._groups.get(group.model) is group:
                        del self._groups[group.model]
                    return
            context.checkpoint()
            self.pause(0.25)

    def _lead(self, group: _Group, context: RecoveryContext) -> None:
        stopped = False
        try:
            self._gather(group, context)
            refused = 0
            while self._run(group, context) == "refused":
                refused += 1
                if refused == JOB_ATTEMPTS:
                    self._give_up(context)  # every request refused twice: no passing fault
                    break
                # Google refused every request of the job ("invalid argument" for all, plain
                # ones included, for a quarter of an hour on 2026-11-28; the same requests were
                # answered before and after): sent again once, a little later.
                log.info("Batch refused every request of a job; sending it again in %.0f s",
                         self.again)
                context.wait(self.again)
        except BaseException:
            stopped = True
            raise
        finally:
            for item in group.items:
                item.stopped = stopped
                item.done.set()

    def _run(self, group: _Group, context: RecoveryContext) -> str:
        """One job for the group's requests, the answers kept on the items: "answered",
        "refused" when Google refused every request (a reason to send them again), or
        "not sent"."""
        name = self._create(group, context)
        if name is None:
            return "not sent"
        view = None
        try:
            view = self._follow(name, group, context)
            refused = 0
            for item in group.items:
                answer = view.answers.get(item.key)
                if answer is None or answer.response is None:
                    if answer is not None and answer.error:
                        refused += 1
                        log.info("A batch request gave no answer: %s", answer.error[:300])
                    continue
                try:
                    item.reply = reply_from(answer.response)
                    item.reply.recovery_id = f"{name}#{item.key}"
                    item.context.account(item.reply.usage, item.reply.recovery_id)
                except BatchUnanswered:
                    pass
                except Exception as error:  # a refusal or truncation, with its bill
                    error.recovery_id = f"{name}#{item.key}"
                    usage = getattr(error, "usage", None)
                    if isinstance(usage, Usage):
                        item.context.account(usage, error.recovery_id)
                    item.error = error
            return "refused" if refused == len(group.items) else "answered"
        finally:
            self._remove(name, context, ended=view is not None and view.state in _ENDED)

    def _create(self, group: _Group, context: RecoveryContext) -> str | None:
        display_name = f"jobcu {uuid4().hex[:12]}"
        requests = [(item.key, item.request) for item in group.items]
        try:
            name = self.service.create(group.model, display_name, requests)
        except errors.APIError as error:
            # Answered: no job exists. A refused model or request format won't change within
            # this search; anything else (busy, too many jobs) may next time.
            log.info("Batch job refused (%s): %s", error.code, str(error)[:300])
            if error.code in (400, 403, 404):
                self._give_up(context)
            return None
        except httpx.TransportError as error:
            # The answer was lost: the job may exist and run (and bill). Find it by its name.
            log.info("Batch job creation unanswered: %s", type(error).__name__)
            try:
                name = self.service.find(display_name)
            except Exception:
                name = None
            if name is None:
                return None
        except Exception as error:  # the library refused the request's form: never retried
            log.info("Batch job not sent: %s: %s", type(error).__name__, str(error)[:300])
            self._give_up(context)
            return None
        log.info("Batch job sent: %s with %d requests", name, len(requests))
        request_recovery.track(context, name, group.model)
        return name

    def _follow(self, name: str, group: _Group, context: RecoveryContext) -> JobView:
        keys = [item.key for item in group.items]
        deadline = self.clock() + self.patience
        failures = 0
        while True:
            try:
                view = self.service.get(name, keys)
                failures = 0
            except Exception as error:  # unreadable now (outage, an answer the library rejects)
                failures += 1
                log.info("Batch job not readable (%d): %s", failures, str(error)[:200])
                if failures > 4:
                    self._cancel(name, keys, context)
                    return JobView("unreadable")
                view = JobView("unknown")
            if view.state in _ENDED:
                waited = self.clock() - (deadline - self.patience)
                log.info("Batch job %s ended %s after %.0f s: %d of %d answered", name,
                         view.state, waited, len(view.answers), len(keys))
                return view
            request_recovery.heartbeat(context.provider, name)
            if self.clock() >= deadline:
                log.info("Batch job %s still unanswered after %.0f s: cancelled", name,
                         self.patience)
                self._give_up(context)
                return self._cancel(name, keys, context)
            context.wait(self.poll)

    def _cancel(self, name: str, keys: list[str], context: RecoveryContext) -> JobView:
        """Cancels the job and returns what it answered before it ended."""
        try:
            self.service.cancel(name)
        except Exception as error:
            log.info("Batch job %s could not be cancelled: %s", name, str(error)[:200])
        deadline = self.clock() + CANCEL_SECONDS
        while self.clock() < deadline:
            try:
                view = self.service.get(name, keys)
            except Exception:
                view = JobView("unknown")
            if view.state in _ENDED:
                return view
            context.wait(min(self.poll, 10.0))
        return JobView("cancelling")

    def _remove(self, name: str, context: RecoveryContext, *, ended: bool) -> None:
        """Ends the job's stay at Google: cancelled if it still runs (Stop), then deleted."""
        if not ended:
            try:
                self.service.cancel(name)
            except Exception:
                pass
        deleted = False
        if ended:
            request_recovery.terminal(context.provider, name)
            try:
                self.service.delete(name)
                deleted = True
            except Exception as error:
                deleted = (getattr(error, "code", None) or getattr(error, "status_code", None)) \
                    == 404
        # A job not yet ended or not deleted stays in the journal for the next cleanup.
        request_recovery.release(context.provider, name, deleted=deleted)

    def _give_up(self, context: RecoveryContext) -> None:
        with self._lock:
            first = not self.unavailable
            self.unavailable = True
        if first:
            context.notify(UNAVAILABLE_NOTICE)


def cleanup(service: BatchService, row: dict, account: Callable[[Usage, str], None]) -> bool:
    """A job left in the journal by an earlier Jobcu process: cancel it if it still runs, record
    the bill of what it answered, delete it. True when it is gone from Google."""
    name = row["interaction_id"]
    try:
        view = service.get(name, [])
    except errors.APIError as error:
        return error.code == 404
    if view.state not in _ENDED:
        try:
            service.cancel(name)
        except Exception:
            return False
        return False  # deleted at a later cleanup, once it has ended
    for key, answer in view.answers.items():
        if answer.response is not None:
            try:
                usage = reply_from(answer.response).usage
            except BatchUnanswered:
                continue
            except Exception as error:
                usage = getattr(error, "usage", None)
            if isinstance(usage, Usage):
                account(usage, f"{name}#{key}")
    try:
        service.delete(name)
    except errors.APIError as error:
        return error.code == 404
    return True
