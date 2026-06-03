"""
llm_factory — returns a LangChain chat LLM based on available API keys.

Priority: Gemini 3.5 Flash (GOOGLE_API_KEY) → Claude Sonnet 4.6 (ANTHROPIC_API_KEY).
Raises ValueError if neither key is set.

Usage:
    from tools.llm_factory import make_llm

    llm, llm_name = make_llm()
"""

import os


def make_llm():
    """Return (llm, model_name) using the best available API key.

    Returns:
        Tuple of (LangChain chat model, human-readable model name string).

    Raises:
        ValueError: If neither GOOGLE_API_KEY nor ANTHROPIC_API_KEY is set.
    """
    google_key = os.getenv("GOOGLE_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return (
            ChatGoogleGenerativeAI(
                model="gemini-3.5-flash",
                google_api_key=google_key,
                max_output_tokens=4096,
            ),
            "Gemini 3.5 Flash",
        )

    if anthropic_key:
        from langchain_anthropic import ChatAnthropic
        return (
            ChatAnthropic(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                api_key=anthropic_key,
            ),
            "Claude Sonnet 4.6",
        )

    raise ValueError(
        "No LLM API key found. Set GOOGLE_API_KEY (Gemini 3.5 Flash, primary) "
        "or ANTHROPIC_API_KEY (Claude Sonnet 4.6, fallback) in backend/.env"
    )
