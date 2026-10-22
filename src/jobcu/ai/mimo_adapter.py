"""Direct pay-as-you-go Chat API, including its native research plugin.

Keyword/result controls are not a currency or search-round cap. Count both reported search
and page units conservatively; the provider invoice remains authoritative. Unknown receipts
and responses outside the requested envelope stop automatic work on the affected path.
"""

from urllib.parse import urlsplit

from jobcu.ai.base import (
    AIBadRequest,
    AIError,
    AIInvalidOutput,
    AILimitReached,
    AIUsageUncertain,
    AIWebSearchUnavailable,
    ResearchReply,
    Source,
    Usage,
    unique_sources,
)
from jobcu.ai.compatible_adapter import CompatibleAdapter, _chat_reply, _chat_usage
from jobcu.ai.openai_adapter import translate_openai_error
from jobcu.settings import Effort


class MiMoAdapter(CompatibleAdapter):
    can_search_the_web = True
    formats = ("json_object",)  # the native contract does not promise strict JSON Schema
    reasoning_notice = (
        "This provider enables thinking and controls its depth. It does not expose a literal "
        "medium effort setting; this is not measured equivalent reasoning."
    )

    def __init__(self, api_key: str, *, timeout: float = 180.0) -> None:
        super().__init__(api_key, base_url="https://api.xiaomimimo.com/v1", timeout=timeout,
                         reasoning="thinking")

    def _token_limit(self, maximum: int) -> dict:
        return {"max_completion_tokens": maximum}

    def complete_json(self, **kwargs):
        try:
            reply = super().complete_json(**kwargs)
        except AIError as error:
            if error.usage is not None and not _valid_tokens(error.usage):
                raise _uncertain(error.usage) from error
            raise
        if not _valid_tokens(reply.usage):
            raise _uncertain(reply.usage)
        return reply

    def research(
        self, *, model: str, system: str, prompt: str, max_searches: int,
        max_output_tokens: int, effort: Effort | None = None,
    ) -> ResearchReply:
        # Reserve search + returned-page units without silently increasing the shared limit.
        if max_searches < 2:
            raise AILimitReached("This research needs room for at least one search and page "
                                 "unit within your existing web allowance.")
        keywords = min(3, max(1, max_searches // 3))
        results = min(5, max_searches // keywords - 1)
        try:
            response = self._client().chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}],
                max_completion_tokens=max_output_tokens,
                extra_body={"thinking": {"type": "enabled"}},
                tools=[{"type": "web_search", "force_search": True,
                        "max_keyword": keywords, "limit": results}],
            )
        except Exception as exc:
            error = translate_openai_error(exc)
            detail = error.detail.lower()
            if isinstance(error, AIBadRequest) and "search" in detail and any(
                    word in detail for word in ("not activated", "not enabled", "activate")):
                raise AIWebSearchUnavailable(
                    "Enable the Web Search plugin in your AI provider's console before "
                    "using online research.", error.detail) from exc
            raise error from exc

        usage = _chat_usage(response.usage)
        counts = getattr(response.usage, "web_search_usage", None)
        tool_units = _count(counts, "tool_usage")
        page_units = _count(counts, "page_usage")
        usage.web_searches = (tool_units or 0) + (page_units or 0)
        if tool_units is None or page_units is None or not _valid_tokens(usage):
            raise _uncertain(usage)
        if tool_units > keywords or page_units > keywords * results:
            error = AIUsageUncertain(
                "Online research exceeded its requested keyword or result bounds. Jobcu "
                "stopped automatic requests on this path; check service usage before retrying.")
            error.usage = usage
            raise error

        reply = _chat_reply(response, usage)
        if not reply.text.strip():
            error = AIInvalidOutput("The provider returned no completed research answer.")
            error.usage = usage
            raise error
        message = response.choices[0].message
        if getattr(message, "error_message", None):
            error = AIWebSearchUnavailable(
                "The provider's web research failed. Check its Web Search plugin and "
                "account access before retrying.", str(message.error_message))
            error.usage = usage
            raise error
        sources = []
        for annotation in getattr(message, "annotations", None) or []:
            data = annotation if isinstance(annotation, dict) else annotation.model_dump()
            url = data.get("url")
            # Only provider-returned URLs become sources; links invented in text do not.
            if isinstance(url, str) and _public_url(url):
                title = data.get("title")
                sources.append(Source(url, title if isinstance(title, str) else ""))
        if not tool_units or not sources:
            error = AIWebSearchUnavailable(
                "The provider did not return a sourced web search. Its answer cannot verify "
                "current conditions; check web-search access before retrying.")
            error.usage = usage
            raise error
        # The native annotations do not map generated passages to sources. Do not fabricate it.
        return ResearchReply(reply.text, unique_sources(sources), usage)


def _public_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        return (parts.scheme in {"https", "http"} and bool(parts.hostname)
                and parts.username is None and parts.password is None)
    except ValueError:
        return False


def _count(counts, name: str) -> int | None:
    value = counts.get(name) if isinstance(counts, dict) else getattr(counts, name, None)
    return value if type(value) is int and value >= 0 else None


def _valid_tokens(usage: Usage) -> bool:
    return (not usage.unreported_requests
            and all(type(v) is int and v >= 0 for v in (
                usage.input_tokens, usage.output_tokens, usage.cached_input_tokens,
                usage.reasoning_tokens))
            and usage.cached_input_tokens <= usage.input_tokens
            and usage.reasoning_tokens <= usage.output_tokens)


def _uncertain(usage: Usage) -> AIUsageUncertain:
    usage.unreported_requests = max(1, usage.unreported_requests)
    for name in ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_tokens"):
        value = getattr(usage, name)
        if type(value) is not int or value < 0:
            setattr(usage, name, 0)
    usage.cached_input_tokens = min(usage.cached_input_tokens, usage.input_tokens)
    usage.reasoning_tokens = min(usage.reasoning_tokens, usage.output_tokens)
    error = AIUsageUncertain(
        "The provider did not return complete usable usage. Jobcu stopped automatic "
        "requests on this path; check service billing before explicitly retrying.")
    error.usage = usage
    return error
