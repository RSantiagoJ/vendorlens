"""
llm_factory — LLM selection, prompt loading, and shared utilities.

All LLM calls use Anthropic:
  - Claude Sonnet 4.6 (make_claude_llm / make_llm): extraction, risk, memo
  - Claude Haiku 3.5  (make_haiku_llm):             scoring — mechanical task, 4x faster

Prompt caching:
  Pass cache=True to make_claude_llm() or make_haiku_llm() to enable the
  Anthropic prompt-caching beta on that model instance, then call
  invoke_llm_cached() instead of invoke_llm() to mark the system prompt
  with cache_control. Cache TTL is 5 minutes, refreshed on every hit.
  Savings: ~90% cost + ~85% latency reduction on the cached portion.

Usage:
    from tools.llm_factory import load_prompt, make_llm, make_claude_llm, make_haiku_llm
    from tools.llm_factory import invoke_llm, invoke_llm_cached, parse_llm_json

    llm = make_haiku_llm(cache=True)         # Haiku with caching enabled
    result = invoke_llm_cached(llm, system_prompt, human_content)
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


def make_claude_llm(cache: bool = False):
    """Return ChatAnthropic(claude-sonnet-4-6) with retry.

    Args:
        cache: Enable Anthropic prompt-caching beta. Use with invoke_llm_cached().
    """
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is not set in backend/.env")
    from langchain_anthropic import ChatAnthropic
    extra = {"model_kwargs": {"betas": ["prompt-caching-2024-07-31"]}} if cache else {}
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=4096, api_key=key, **extra)
    return llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)


def make_haiku_llm(cache: bool = False):
    """Return ChatAnthropic(claude-haiku-4-5) with retry. Used for scoring (mechanical task).

    Args:
        cache: Enable Anthropic prompt-caching beta. Use with invoke_llm_cached().
    """
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is not set in backend/.env")
    from langchain_anthropic import ChatAnthropic
    extra = {"model_kwargs": {"betas": ["prompt-caching-2024-07-31"]}} if cache else {}
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=4096, api_key=key, **extra)
    return llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)


def make_llm():
    """Return (llm, model_name) — Claude Sonnet 4.6 for extraction, risk, and memo agents.

    Returns:
        Tuple of (LangChain chat model, human-readable model name string).

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
    """
    return make_claude_llm(), "Claude Sonnet 4.6"


def invoke_llm(llm, system_prompt: str, human_content: str) -> str:
    """Call an LLM with a system + human message and return the response content."""
    from langchain_core.messages import HumanMessage, SystemMessage
    return llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_content)]).content


def invoke_llm_cached(llm, system_prompt: str, human_content: str) -> str:
    """Call an LLM with a cache-marked system prompt (Anthropic prompt caching).

    The system prompt is sent as a content block with cache_control: ephemeral.
    Requires the model to be created with cache=True (the prompt-caching beta header).
    On cache hit: ~90% cost reduction + ~85% latency reduction for the cached portion.
    Cache TTL is 5 minutes, refreshed on every hit.
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    system = SystemMessage(content=[{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"},
    }])
    return llm.invoke([system, HumanMessage(content=human_content)]).content


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

    # On failure, dump the raw response to a file for debugging
    try:
        debug_path = Path(__file__).parent.parent / "raw_response_debug.txt"
        debug_path.write_text(raw, encoding="utf-8")
    except Exception:
        pass

    raise ValueError(f"No valid JSON found in LLM response. First 200 chars: {raw[:200]!r}")
