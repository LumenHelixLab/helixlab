"""Llama 3 adapter via Together AI — OpenAI-compatible (spec §5.3)."""
from __future__ import annotations

from typing import Any

from .openai_adapter import OpenAIAdapter


class LlamaAdapter(OpenAIAdapter):
    def __init__(self, api_key: str | None = None) -> None:
        import os

        super().__init__(
            api_key=api_key or os.getenv("TOGETHER_API_KEY"),
            base_url="https://api.together.xyz/v1",
        )

    def generate(self, prompt: str, tools: list[dict], **kwargs: Any) -> Any:
        kwargs.setdefault("model", "meta-llama/Llama-3-70b-chat-hf")
        return super().generate(prompt, tools, **kwargs)