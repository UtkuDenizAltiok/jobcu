"""Each provider's errors become the same plain Jobcu errors."""

import anthropic
import httpx
import httpx2
import openai
import pytest
from google.genai import errors as genai_errors

from jobcu.ai import anthropic_adapter, gemini_adapter, openai_adapter
from jobcu.ai.base import (
    AIAuthError,
    AIBadRequest,
    AIModelNotFound,
    AIQuotaExhausted,
    AIRateLimited,
    AIReasoningUnsupported,
    AIUnavailable,
    AIWebSearchUnavailable,
)


def _response(status, headers=None):
    return httpx2.Response(status, headers=headers, request=httpx2.Request("POST", "https://x.test"))


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (openai.AuthenticationError("bad key", response=_response(401), body=None), AIAuthError),
        (openai.NotFoundError("no model", response=_response(404), body=None), AIModelNotFound),
        (openai.BadRequestError("bad", response=_response(400), body=None), AIBadRequest),
        (openai.InternalServerError("oops", response=_response(500), body=None), AIUnavailable),
        (
            openai.RateLimitError(
                "insufficient_quota", response=_response(429), body={"code": "insufficient_quota"}
            ),
            AIQuotaExhausted,
        ),
    ],
)
def test_openai_errors(error, expected):
    assert isinstance(openai_adapter.translate_openai_error(error), expected)


def test_openai_rate_limit_keeps_retry_after():
    error = openai.RateLimitError(
        "slow down", response=_response(429, {"retry-after": "7"}), body=None
    )
    result = openai_adapter.translate_openai_error(error)
    assert isinstance(result, AIRateLimited) and result.retry_after == 7


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (anthropic.AuthenticationError("bad", response=_response(401), body=None), AIAuthError),
        (anthropic.NotFoundError("no", response=_response(404), body=None), AIModelNotFound),
        (anthropic.APIStatusError("busy", response=_response(529), body=None), AIUnavailable),
        (
            anthropic.BadRequestError(
                "Your credit balance is too low", response=_response(400), body=None
            ),
            AIQuotaExhausted,
        ),
    ],
)
def test_anthropic_errors(error, expected):
    assert isinstance(anthropic_adapter._translate(error), expected)


def test_anthropic_rate_limit_keeps_retry_after():
    error = anthropic.RateLimitError(
        "slow down", response=_response(429, {"retry-after": "30"}), body=None
    )
    result = anthropic_adapter._translate(error)
    assert isinstance(result, AIRateLimited) and result.retry_after == 30


def _gemini_error(code, status, message, details=()):
    body = {"error": {"code": code, "status": status, "message": message, "details": list(details)}}
    return genai_errors.ClientError(code, body)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            _gemini_error(400, "INVALID_ARGUMENT", "API key not valid. Please pass a valid key."),
            AIAuthError,
        ),
        (_gemini_error(404, "NOT_FOUND", "models/x is not found"), AIModelNotFound),
        (_gemini_error(400, "INVALID_ARGUMENT", "thinking level not supported"), AIBadRequest),
        (
            _gemini_error(
                429,
                "RESOURCE_EXHAUSTED",
                "Quota exceeded",
                [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}],
            ),
            AIQuotaExhausted,
        ),
        (genai_errors.ServerError(503, {"error": {"code": 503, "message": "busy"}}), AIUnavailable),
        (httpx.ConnectError("offline"), AIUnavailable),
    ],
)
def test_gemini_errors(error, expected):
    assert isinstance(gemini_adapter._translate(error), expected)


def test_gemini_per_minute_limit_keeps_suggested_wait():
    error = _gemini_error(
        429, "RESOURCE_EXHAUSTED", "Quota exceeded",
        [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "31s"}],
    )
    result = gemini_adapter._translate(error)
    assert isinstance(result, AIRateLimited) and result.retry_after == 31


@pytest.mark.parametrize("provider, message, unsupported", [
    ("gemini", "Thinking level is not supported for this model.", True),
    ("gemini", "thinking level not supported", True),
    ("gemini", "This model does not support thinking.", True),
    ("openai", "Unsupported parameter: 'reasoning.effort' is not supported with this model.",
     True),
    ("anthropic", "This model does not support the effort parameter.", True),
    ("anthropic", "output_config.effort is not supported for this model.", True),
    ("gemini", "Thinking level MEDIUM is not supported for this model.", False),
    ("gemini", "Invalid schema: property 'thinking' is not supported.", False),
    ("gemini", "Invalid JSON payload: unknown field thinking_config in response_schema.", False),
    ("gemini", "thinking level not supported when combined with this tool", False),
    ("openai", "Unsupported value: 'medium' is not supported with this model.", False),
    ("openai", "Invalid schema 'reasoning': unsupported type.", False),
    ("openai", "Unsupported parameter: 'tools' is not supported with this model.", False),
    ("anthropic", "output_config.effort 'medium' is not supported on this model.", False),
    ("anthropic", "adaptive thinking is not supported on this model", False),
    ("anthropic", "effort is not supported when thinking is disabled", False),
    ("anthropic", "output_config.effort requires a model that supports per-turn effort; "
     "this model does not", False),
])
def test_native_reasoning_refusals_must_identify_the_whole_control(provider, message, unsupported):
    if provider == "gemini":
        error = _gemini_error(400, "INVALID_ARGUMENT", message)
        result = gemini_adapter._translate(error)
    elif provider == "openai":
        error = openai.BadRequestError(message, response=_response(400),
                                      body={"message": message})
        result = openai_adapter.translate_openai_error(error)
    else:
        error = anthropic.BadRequestError(message, response=_response(400), body={
            "error": {"type": "invalid_request_error", "message": message},
        })
        result = anthropic_adapter._translate(error)
    assert isinstance(result, AIBadRequest)
    assert isinstance(result, AIReasoningUnsupported) is unsupported
    assert result.detail == str(error)


@pytest.mark.parametrize("code, param, unsupported", [
    ("unsupported_parameter", "reasoning", True),
    ("unsupported_parameter", "reasoning.effort", True),
    ("unsupported_parameter", "tools", False),
    ("unsupported_value", "reasoning.effort", False),
    ("invalid_json_schema", "text.format.schema", False),
])
def test_openai_structured_error_identity_is_distinct_from_unsupported_values(code, param,
                                                                            unsupported):
    error = openai.BadRequestError("Request refused", response=_response(400), body={
        "code": code, "param": param, "message": "Request refused",
    })
    result = openai_adapter.translate_openai_error(error)
    assert isinstance(result, AIReasoningUnsupported) is unsupported


def test_gemini_diagnostics_cannot_reclassify_a_schema_failure_as_reasoning_refusal():
    error = _gemini_error(400, "INVALID_ARGUMENT", "Invalid JSON schema", [{
        "description": "thinking level not supported",
    }])
    assert type(gemini_adapter._translate(error)) is AIBadRequest


@pytest.mark.parametrize("error", [
    _gemini_error(400, "INVALID_ARGUMENT", "Google Search grounding is not available on free tier"),
    _gemini_error(400, "INVALID_ARGUMENT", "Google Search is not supported for this model"),
    _gemini_error(403, "PERMISSION_DENIED", "Enable billing to use Google Search"),
    _gemini_error(429, "RESOURCE_EXHAUSTED", "Grounding quota exceeded, limit: 0"),
])
def test_gemini_definite_web_refusals_are_separate_from_normal_ai_errors(error):
    result = gemini_adapter._translate(error, web_search=True)
    assert isinstance(result, AIWebSearchUnavailable)
    assert "continue searching job sources and scoring" in result.message
    # The same error during text generation must not disable research.
    assert not isinstance(gemini_adapter._translate(error), AIWebSearchUnavailable)


@pytest.mark.parametrize("error, expected", [
    (_gemini_error(429, "RESOURCE_EXHAUSTED", "Grounding quota exceeded, limit: 20"),
     AIRateLimited),
    (_gemini_error(429, "RESOURCE_EXHAUSTED", "GenerateRequests quota exceeded, limit: 0"),
     AIRateLimited),
    (_gemini_error(403, "PERMISSION_DENIED", "Google Search permission denied"), AIAuthError),
    (_gemini_error(400, "INVALID_ARGUMENT", "API key not valid. Google Search not supported"),
     AIAuthError),
    (_gemini_error(400, "INVALID_ARGUMENT", "thinking level not supported"), AIBadRequest),
])
def test_web_refusal_detection_keeps_auth_and_transient_errors(error, expected):
    assert isinstance(gemini_adapter._translate(error, web_search=True), expected)


def test_anthropic_asks_to_keep_the_instructions_ready():
    """Provider-side prompt caching: the same instructions cost less in later requests."""
    sent = {}

    class FakeMessages:
        def stream(self, **request):
            sent.update(request)
            raise anthropic.APIStatusError("busy", response=_response(529), body=None)

    class FakeClient:
        messages = FakeMessages()
        models = None

    adapter = anthropic_adapter.AnthropicAdapter("fake-key")
    adapter._sdk_client = FakeClient()
    with pytest.raises(AIUnavailable):
        adapter.complete_json(model="m", system="Rules", prompt="Jobs", schema={}, schema_name="s",
                              effort=None, max_output_tokens=100)
    assert sent["system"] == [
        {"type": "text", "text": "Rules", "cache_control": {"type": "ephemeral"}}
    ]
