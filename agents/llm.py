"""
LLM factory — returns the correct ChatModel based on LLM_PROVIDER env var.

Set in .env:
  LLM_PROVIDER=groq        → uses GROQ_API_KEY
  LLM_PROVIDER=anthropic   → uses ANTHROPIC_API_KEY (default)

speed="fast"  → llama-3.1-8b-instant  (Orchestrator, Writer)
speed="smart" → llama-3.3-70b-versatile (Analysis — needs reasoning)
"""

import os
from langchain_core.language_models import BaseChatModel

GROQ_FAST_MODEL = "llama-3.1-8b-instant"
GROQ_SMART_MODEL = "llama-3.3-70b-versatile"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"       # fast tier
ANTHROPIC_SMART_MODEL = "claude-sonnet-4-5"         # smart tier


def get_llm(temperature: float = 0, max_tokens: int = 4096, speed: str = "fast") -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

    if provider == "groq":
        from langchain_groq import ChatGroq
        model = GROQ_SMART_MODEL if speed == "smart" else GROQ_FAST_MODEL
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", model),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    from langchain_anthropic import ChatAnthropic
    model = ANTHROPIC_SMART_MODEL if speed == "smart" else ANTHROPIC_MODEL
    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", model),
        temperature=temperature,
        max_tokens=max_tokens,
    )
