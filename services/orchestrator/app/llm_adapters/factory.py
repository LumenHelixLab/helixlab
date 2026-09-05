"""LLMAdapterFactory (spec §5.3) — resolves the provider name from the
neutral request to a concrete adapter. The single reconciliation of the
spec's LLMAdapterManager (§4.3) / LLMAdapterFactory (§5.3) naming split."""
from __future__ import annotations

from typing import Any

from .anthropic_adapter import ClaudeAdapter
from .base import LLMAdapter
from .gemini_adapter import GeminiAdapter
from .kimi_adapter import KimiAdapter
from .llama_adapter import LlamaAdapter
from .openai_adapter import OpenAIAdapter


class LLMAdapterFactory:
    _adapters = {
        "openai": OpenAIAdapter,
        "anthropic": ClaudeAdapter,
        "google": GeminiAdapter,
        "moonshot": KimiAdapter,
        "llama": LlamaAdapter,
    }

    @classmethod
    def get_adapter(cls, provider: str, **kwargs: Any) -> LLMAdapter:
        adapter_class = cls._adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter_class(**kwargs)