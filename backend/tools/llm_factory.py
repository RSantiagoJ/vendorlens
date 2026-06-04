"""
llm_factory — LLM selection, prompt loading, and shared utilities.

Priority: Gemini 3.5 Flash (GOOGLE_API_KEY) → Claude Sonnet 4.6 (ANTHROPIC_API_KEY).
Raises ValueError if neither key is set.

Usage:
    from tools.llm_factory import load_prompt, make_llm, make_claude_llm, parse_llm_json

    system_prompt = load_prompt("extraction_agent")
    llm, llm_name = make_llm()
    llm = make_claude_llm()          # always Claude, used by MemoAgent
    data = parse_llm_json(response.content)
"""

import json
import os
from pathlib import Path

import yaml

_PROMPTS_PATH = Path(__file__).parent.parent / "prompts.yaml"
_PROMPTS: dict | None = None


def load_prompt(role: str) -> str:
    """Return the system prompt for a given agent role from prompts.yaml."""
    global _PROMPTS
    if _PROMPTS is None:
        with open(_PROMPTS_PATH, "r") as f:
            _PROMPTS = yaml.safe_load(f)
    return _PROMPTS[role]["system"]


def make_claude_llm():
    """Return ChatAnthropic(claude-sonnet-4-6) with retry. Raises ValueError if key not set."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is not set in backend/.env")
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=4096, api_key=key)
    return llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)


def make_llm():
    """Return (llm, model_name) using the best available API key, with retry.

    Priority: Gemini 3.5 Flash (GOOGLE_API_KEY) → Claude Sonnet 4.6 (ANTHROPIC_API_KEY).
    Note: MemoAgent calls make_claude_llm() directly and is unaffected by this priority.
    Google API key is also required for embeddings regardless of which LLM is used here.

    Returns:
        Tuple of (LangChain chat model, human-readable model name string).

    Raises:
        ValueError: If neither GOOGLE_API_KEY nor ANTHROPIC_API_KEY is set.
    """
    google_key = os.getenv("GOOGLE_API_KEY")

    if google_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash",
            google_api_key=google_key,
            max_output_tokens=8192,
        )
        return (
            llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True),
            "Gemini 3.5 Flash",
        )

    if os.getenv("ANTHROPIC_API_KEY"):
        return make_claude_llm(), "Claude Sonnet 4.6"

    raise ValueError(
        "No LLM API key found. Set GOOGLE_API_KEY (Gemini 3.5 Flash, primary) "
        "or ANTHROPIC_API_KEY (Claude Sonnet 4.6, fallback) in backend/.env"
    )


def dedup_ordered(items: list[str]) -> list[str]:
    """Return items with duplicates removed, preserving first-seen order.

    Empty strings are also filtered out.
    """
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_llm_json(raw: str):
    """Parse JSON from an LLM response robustly.

    Handles markdown code fences, preamble text, and unescaped characters
    by extracting the outermost JSON object or array before parsing.

    Args:
        raw: Raw string content from response.content.

    Returns:
        Parsed Python object (dict or list).

    Raises:
        ValueError: If no valid JSON block can be found.
    """
    if isinstance(raw, list):
        raw = "".join(part["text"] if isinstance(part, dict) else str(part) for part in raw)

    raw = raw.strip()

    # Strip markdown code fences
    if raw.startswith("```"):
        lines = raw.split("\n")
        end = -1 if lines[-1].strip() == "```" else len(lines)
        raw = "\n".join(lines[1:end]).strip()

    # Try parsing as-is first (fast path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Extract the outermost JSON object or array — handles preamble/postamble text
    for open_char, close_char in [('{', '}'), ('[', ']')]:
        start = raw.find(open_char)
        end = raw.rfind(close_char)
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No valid JSON found in LLM response. First 200 chars: {raw[:200]!r}")
