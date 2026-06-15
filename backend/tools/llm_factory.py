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
    from tools.llm_factory import load_prompt, make_claude_llm, make_haiku_llm
    from tools.llm_factory import invoke_llm_cached, parse_llm_json

    llm = make_haiku_llm(cache=True)
    result = invoke_llm_cached(llm, system_prompt, human_content)
"""

import json
import os
import threading
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# LLM cost tracking
# ---------------------------------------------------------------------------

# Pricing per 1M tokens (as of 2026-06-04)
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,   # 0.1× input
        "cache_write": 3.75,  # 1.25× input (5-min TTL)
    },
    "claude-haiku-4-5-20251001": {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
}

_run_costs: dict[str, float] = {}
_run_costs_lock = threading.Lock()
_current_run_id: threading.local = threading.local()


def begin_cost_tracking(run_id: str) -> None:
    """Call at the start of each pipeline run to zero the cost accumulator."""
    _current_run_id.value = run_id
    with _run_costs_lock:
        _run_costs[run_id] = 0.0


def end_cost_tracking(run_id: str) -> float:
    """Call at the end of each pipeline run. Returns total USD cost and clears the accumulator."""
    _current_run_id.value = None
    with _run_costs_lock:
        return _run_costs.pop(run_id, 0.0)


def compute_llm_cost(usage_metadata: dict | None, model_id: str) -> float:
    """Compute USD cost from Anthropic usage_metadata dict.

    Fields: input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens.
    Falls back to sonnet pricing for unknown model IDs.
    Returns 0.0 if usage_metadata is None (e.g., mocked LLM calls in tests).
    """
    if not usage_metadata:
        return 0.0
    rates = PRICING.get(model_id, PRICING["claude-sonnet-4-6"])
    mtok = 1_000_000.0
    return (
        usage_metadata.get("input_tokens", 0) * rates["input"] / mtok
        + usage_metadata.get("output_tokens", 0) * rates["output"] / mtok
        + usage_metadata.get("cache_read_input_tokens", 0) * rates["cache_read"] / mtok
        + usage_metadata.get("cache_creation_input_tokens", 0) * rates["cache_write"] / mtok
    )


# ---------------------------------------------------------------------------
# Prompt + model cache
# ---------------------------------------------------------------------------

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
    extra = {"betas": ["prompt-caching-2024-07-31"]} if cache else {}
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=16384, api_key=key, **extra)
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
    extra = {"betas": ["prompt-caching-2024-07-31"]} if cache else {}
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=16384, api_key=key, **extra)
    return llm.with_retry(stop_after_attempt=3, wait_exponential_jitter=True)


def invoke_llm_cached(llm, system_prompt: str, human_content: str) -> str:
    """Call an LLM with a cache-marked system prompt (Anthropic prompt caching).

    The system prompt is sent as a content block with cache_control: ephemeral.
    Requires the model to be created with cache=True (the prompt-caching beta header).
    On cache hit: ~90% cost reduction + ~85% latency reduction for the cached portion.
    Cache TTL is 5 minutes, refreshed on every hit.

    As a side effect, accumulates USD cost into the current run's accumulator when
    begin_cost_tracking() has been called on this thread. Warm-cache calls that
    run in sub-threads (ThreadPoolExecutor) will not be captured; that cost is small.
    """
    from langchain_core.messages import HumanMessage, SystemMessage
    system = SystemMessage(content=[{
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"},
    }])
    response = llm.invoke([system, HumanMessage(content=human_content)])

    run_id = getattr(_current_run_id, "value", None)
    if run_id:
        underlying = getattr(llm, "bound", llm)
        model_id = getattr(underlying, "model", "claude-sonnet-4-6")
        usage = getattr(response, "usage_metadata", None)
        if isinstance(usage, dict):
            cost = compute_llm_cost(usage, model_id)
            with _run_costs_lock:
                _run_costs[run_id] = _run_costs.get(run_id, 0.0) + cost

    return response.content


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

    # Extract the outermost JSON object or array — handles preamble/postamble text.
    # Try whichever delimiter appears first so that a leading `[` is not shadowed
    # by a `{` nested inside the array items.
    brace_pos   = raw.find('{')
    bracket_pos = raw.find('[')
    if bracket_pos != -1 and (brace_pos == -1 or bracket_pos < brace_pos):
        pairs = [('[', ']'), ('{', '}')]
    else:
        pairs = [('{', '}'), ('[', ']')]

    for open_char, close_char in pairs:
        start = raw.find(open_char)
        end = raw.rfind(close_char)
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                continue

    # On failure, dump the raw response to a file for debugging
    try:
        debug_dir = Path(__file__).parent.parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        debug_path = debug_dir / "raw_response_debug.txt"
        debug_path.write_text(raw, encoding="utf-8")
    except Exception:
        pass

    raise ValueError(f"No valid JSON found in LLM response. First 200 chars: {raw[:200]!r}")
