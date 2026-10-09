"""Supported AI providers, listed alphabetically. Users choose their provider and model."""

from dataclasses import dataclass

from jobcu.ai.anthropic_adapter import AnthropicAdapter
from jobcu.ai.base import ProviderAdapter
from jobcu.ai.compatible_adapter import (
    CompatibleAdapter,
    CompatibleMessagesAdapter,
    CompatibleResponsesAdapter,
)
from jobcu.ai.gemini_adapter import GeminiAdapter
from jobcu.ai.openai_adapter import OpenAIAdapter
from jobcu.settings import AISettings


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    name: str
    adapter: type[ProviderAdapter]
    key_page: str  # where users create a key
    needs_base_url: bool = False
    key_optional: bool = False

    @property
    def key_name(self) -> str:
        return f"ai_{self.id}"


PROVIDERS: dict[str, ProviderInfo] = {
    info.id: info
    for info in (
        ProviderInfo(
            "anthropic", "Anthropic (Claude)", AnthropicAdapter,
            key_page="https://platform.claude.com/settings/keys",
        ),
        ProviderInfo(
            "gemini", "Google (Gemini)", GeminiAdapter,
            key_page="https://aistudio.google.com/apikey",
        ),
        ProviderInfo(
            "openai", "OpenAI", OpenAIAdapter,
            key_page="https://platform.openai.com/api-keys",
        ),
        ProviderInfo(
            "openai_compatible", "Other (OpenAI-compatible)", CompatibleAdapter,
            key_page="", needs_base_url=True, key_optional=True,
        ),
    )
}


def configured_adapter(provider: str, key: str, ai: AISettings, *, timeout=180.0, session_id=""
                       ) -> ProviderAdapter:
    """Keep native keys on their native hosts; only Other uses the supplied address."""
    if provider != "openai_compatible":
        return PROVIDERS[provider].adapter(key, timeout=timeout)
    options = {"base_url": ai.base_url.strip(), "timeout": timeout, "session_id": session_id}
    if ai.compatible_protocol == "responses":
        return CompatibleResponsesAdapter(key, **options)
    if ai.compatible_protocol == "messages":
        return CompatibleMessagesAdapter(key, **options)
    return CompatibleAdapter(key, reasoning=ai.compatible_reasoning,
                             medium=ai.compatible_medium, **options)
