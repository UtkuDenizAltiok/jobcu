"""Decode stateless native event streams without treating partial text as an answer."""

from collections import Counter

from google.genai import errors

from jobcu.ai.base import (
    MSG_BAD_REQUEST,
    MSG_QUOTA,
    MSG_REFUSED,
    MSG_TRUNCATED,
    MSG_UNAVAILABLE,
    AIBadRequest,
    AIOutputTruncated,
    AIQuotaExhausted,
    AIRefused,
    AIUnavailable,
    Citation,
    ResearchReply,
    Source,
    Usage,
    unique_sources,
)

# Dated API/locked-SDK capability list, not a model recommendation or default selection.
# Unverified model IDs continue through the supported Generate Content adapter.
EVENT_MODELS = frozenset({
    "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
    "gemini-3-flash-preview", "gemini-3.1-pro-preview", "gemini-3.1-flash-lite",
    "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash",
    "gemini-3.7-flash", "gemini-3.8-flash", "gemini-4-argon",
    "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-pro-latest",
})


class EventAnswer:
    def __init__(self, *, model: str, web_search: bool):
        self.web_search = web_search
        self.query_billed = not model.startswith("gemini-2.")
        self.steps: dict[int, dict] = {}
        self.queries: set[str] = set()
        self.counts: Counter = Counter()
        self.search_count = 0
        self.search_seen = False
        self.complete = self.final_usage = False

    def _usage(self, usage):
        if not isinstance(usage, dict):
            return
        self.counts |= Counter({key: max(0, value) for key, value in usage.items()
                               if isinstance(value, int)})
        for item in usage.get("grounding_tool_count") or []:
            if item.get("type", "").lower() == "google_search":
                self.search_count = max(self.search_count, item.get("count") or 0)

    def _queries(self, arguments):
        if isinstance(arguments, dict):
            self.queries.update(q.strip() for q in arguments.get("queries") or []
                                if isinstance(q, str) and q.strip())

    def _start(self, index, step):
        if step.get("type") == "function_call":
            raise AIBadRequest(MSG_BAD_REQUEST, "The provider requested an undeclared client tool.")
        if step.get("error"):
            raise AIRefused(MSG_REFUSED, "The provider blocked the model output.")
        self.steps[index] = {"kind": step.get("type"), "parts": []}
        if step.get("type") == "model_output":
            for content in step.get("content") or []:
                if content.get("type") == "text":
                    self.steps[index]["parts"].append({
                        "text": content.get("text") or "",
                        "annotations": content.get("annotations") or [],
                    })
        if step.get("type") == "google_search_call":
            self.search_seen = True
            self._queries(step.get("arguments"))

    def add(self, event: dict) -> None:
        kind = event.get("event_type")
        if kind == "step.start":
            self._start(event["index"], event["step"])
        elif kind == "step.delta":
            self._usage((event.get("metadata") or {}).get("total_usage"))
            delta = event.get("delta") or {}
            if delta.get("type") == "google_search_call":
                self.search_seen = True
                self._queries(delta.get("arguments"))
            step = self.steps.get(event["index"])
            if step and step["kind"] == "model_output":
                parts = step["parts"]
                if not parts:
                    parts.append({"text": "", "annotations": []})
                if delta.get("type") == "text":
                    parts[-1]["text"] += delta.get("text") or ""
                elif delta.get("type") == "text_annotation_delta":
                    parts[-1]["annotations"].extend(delta.get("annotations") or [])
        elif kind == "step.stop":
            self._usage(event.get("usage"))
        elif kind == "interaction.completed":
            interaction = event.get("interaction") or {}
            self._usage(interaction.get("usage"))
            self.final_usage = bool(interaction.get("usage"))
            # Some responses repeat the complete canonical steps at the end. Replace
            # streamed text instead of duplicating it, and retain their annotations.
            if interaction.get("steps"):
                self.steps = {}
                for index, step in enumerate(interaction["steps"]):
                    self._start(index, step)
            status = interaction.get("status")
            if status and status != "completed":
                self._terminal(status)
            self.complete = True
        elif kind == "interaction.status_update":
            if event.get("status") in (
                    "failed", "cancelled", "incomplete", "requires_action", "budget_exceeded"):
                self._terminal(event["status"])
        elif kind == "error":
            error = event.get("error") or {}
            code = str(error.get("code") or "").lower()
            if code in ("quota_exceeded", "insufficient_quota", "payment_required"):
                raise AIQuotaExhausted(MSG_QUOTA, error.get("message") or code)
            if code in ("safety", "recitation", "content_filter"):
                raise AIRefused(MSG_REFUSED, code)
            status = {
                "invalid_argument": 400, "invalid_request": 400, "unsupported_feature": 400,
                "context_length_exceeded": 400, "authentication_error": 401,
                "unauthenticated": 401, "permission_denied": 403, "model_not_found": 404,
                "not_found": 404, "rate_limit_exceeded": 429, "too_many_requests": 429,
            }.get(code, int(code) if code.isdigit() else 503)
            raise errors.APIError(status, {"error": {
                "message": error.get("message") or code, "status": code.upper()}})

    @staticmethod
    def _terminal(status):
        if status == "budget_exceeded":
            raise AIQuotaExhausted(MSG_QUOTA, "The provider's execution budget was exceeded.")
        if status == "incomplete":
            raise AIOutputTruncated(MSG_TRUNCATED)
        if status == "requires_action":
            raise AIBadRequest(MSG_BAD_REQUEST, "The provider requested an undeclared client tool.")
        raise AIUnavailable(MSG_UNAVAILABLE, f"AI interaction ended with status {status}.")

    def usage(self, *, interrupted=False) -> Usage:
        searches = max(self.search_count, len(self.queries), int(self.search_seen))
        unknown_search_count = (self.web_search and self.query_billed and self.search_seen
                                and not self.search_count and not self.queries)
        thoughts = self.counts["total_thought_tokens"]
        return Usage(
            input_tokens=self.counts["total_input_tokens"],
            output_tokens=self.counts["total_output_tokens"] + thoughts,
            cached_input_tokens=self.counts["total_cached_tokens"],
            reasoning_tokens=thoughts,
            web_searches=(searches if self.query_billed else int(bool(searches)))
            if self.web_search else 0,
            unreported_requests=int(interrupted or not self.final_usage or unknown_search_count),
        )

    def reply(self) -> ResearchReply:
        if not self.complete:
            raise AIUnavailable(MSG_UNAVAILABLE, "AI event stream ended before completion.")
        parts = [part for index in sorted(self.steps)
                 if self.steps[index]["kind"] == "model_output"
                 for part in self.steps[index]["parts"]]
        text = "".join(part["text"] for part in parts)
        sources, citations = [], {}
        for part in parts:
            encoded = part["text"].encode("utf-8")
            for annotation in part["annotations"]:
                if annotation.get("type") != "url_citation" or not annotation.get("url"):
                    continue
                url = annotation["url"]
                sources.append(Source(url, annotation.get("title") or ""))
                start, end = annotation.get("start_index"), annotation.get("end_index")
                if not (type(start) is int and type(end) is int
                        and 0 <= start < end <= len(encoded)):
                    continue
                try:
                    words = encoded[start:end].decode("utf-8")
                except UnicodeDecodeError:
                    continue  # never guess a claim from a split character or another part
                if text.count(words) == 1:
                    citations[words, url] = Citation(words, url)
        return ResearchReply(text=text, usage=self.usage(), sources=unique_sources(sources),
                             citations=list(citations.values()) if self.web_search else None)
