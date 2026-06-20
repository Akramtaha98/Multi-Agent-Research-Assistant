"""
LLM factory — returns the correct ChatModel based on LLM_PROVIDER env var.

Set in .env:
  LLM_PROVIDER=groq        → uses GROQ_API_KEY + llama-3.3-70b-versatile
  LLM_PROVIDER=anthropic   → uses ANTHROPIC_API_KEY + claude-sonnet-4-5  (default)
"""

import os
from langchain_core.language_models import BaseChatModel


def get_llm(temperature: float = 0, max_tokens: int = 4096) -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Default: Anthropic / Claude
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        temperature=temperature,
        max_tokens=max_tokens,
    )
