"""
context_loader — loads files from data/context_bundle/ for agent injection.

Usage:
    from tools.context_loader import load_context_bundle

    bundle = load_context_bundle()
    rubric_text = bundle["scoring_rubric_lms"]   # injected into scoring agent system prompt
    policy_text = bundle["policy"]               # available for risk agent if needed
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
BUNDLE_DIR = BASE_DIR / "data" / "context_bundle"


def load_context_bundle() -> dict[str, str]:
    """Read all .txt files in data/context_bundle/ and return as {stem: content}.

    Keys are file stems (filename without extension), e.g.:
        "policy"              → policy.txt
        "rfp_criteria_lms"   → rfp_criteria_lms.txt
        "scoring_rubric_lms" → scoring_rubric_lms.txt

    Raises FileNotFoundError if the context_bundle directory does not exist.
    """
    if not BUNDLE_DIR.exists():
        raise FileNotFoundError(f"context_bundle directory not found: {BUNDLE_DIR}")

    bundle: dict[str, str] = {}
    for path in sorted(BUNDLE_DIR.glob("*.txt")):
        bundle[path.stem] = path.read_text(encoding="utf-8")

    return bundle
