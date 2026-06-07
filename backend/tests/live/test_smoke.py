"""
test_smoke.py — lightweight pipeline smoke test

Two modes:
  python tests/test_smoke.py            # single vendor, full pipeline (~4 LLM calls)
  python tests/test_smoke.py --dry-run  # init only — no LLM calls, just embedding queries

Cost estimate (full run): ~$0.02 total (Sonnet extraction + Sonnet risk + Haiku scoring + Sonnet memo)
The --dry-run validates ChromaDB, policy files, and agent init without invoking the graph.

Usage:
    cd backend
    python tests/test_smoke.py
    python tests/test_smoke.py --dry-run
    python tests/test_smoke.py --vendor blackboard.txt
    pytest tests/test_smoke.py -s
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _build(vendor: str = "canvas.txt"):
    from graph.pipeline import build_pipeline

    print("Initializing agents + loading ChromaDB index...")
    try:
        graph = build_pipeline()
    except Exception as e:
        sys.exit(
            f"ERROR: Could not build pipeline.\n"
            f"  Ensure ingest.py has been run and API keys are set.\n"
            f"  Details: {e}"
        )
    return graph


def run_dry(vendor: str = "canvas.txt"):
    """Verify pipeline compiles and agents initialize — no LLM inference calls."""
    graph = _build(vendor)
    print("[PASS] Pipeline compiled. All agents initialized, ChromaDB accessible.")
    print("       (no LLM inference calls made — run without --dry-run to test end-to-end)")


def run_full(vendor: str = "canvas.txt"):
    """Run one vendor through the full pipeline and assert basic structure."""
    graph = _build(vendor)

    initial_state = {
        "pending": [{"filename": vendor}],
        "proposals": [],
        "memo": None,
        "status": "pending",
        "error": None,
    }

    print(f"\nRunning pipeline on {vendor}...")
    try:
        result = graph.invoke(initial_state)
    except Exception as e:
        sys.exit(f"ERROR: graph.invoke raised: {e}")

    status = result.get("status")
    if status != "done":
        sys.exit(
            f"Pipeline did not complete.\n"
            f"  status : {status}\n"
            f"  error  : {result.get('error')}"
        )

    proposals = result.get("proposals", [])
    if not proposals:
        sys.exit("ERROR: No proposals in result.")

    from graph.state import ProposalState

    p = ProposalState(**proposals[0])

    print("\nResult:")
    print(f"  vendor  : {p.extracted.vendor_name if p.extracted else '(extraction failed)'}")
    print(f"  score   : {p.scores.overall if p.scores else 'N/A'}")
    print(f"  risks   : {len(p.risks or [])} flags")
    print(f"  memo    : {(result.get('memo') or '')[:200]}...")

    if p.error:
        sys.exit(f"FAIL: Vendor processing error: {p.error}")
    if p.scores is None:
        sys.exit(f"FAIL: No scores produced for {vendor}")

    print(f"\n[PASS] Pipeline smoke test passed for {vendor}")


def test_smoke_dry():
    """pytest hook: structure-only check (no LLM calls)."""
    run_dry()


def test_smoke_full():
    """pytest hook: single-vendor end-to-end check."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        import pytest
        pytest.skip("ANTHROPIC_API_KEY not set")
    run_full()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VendorLens pipeline smoke test")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Init agents only — no LLM inference calls",
    )
    parser.add_argument(
        "--vendor",
        default="canvas.txt",
        choices=["canvas.txt", "blackboard.txt", "brightspace.txt"],
        help="Vendor proposal to test (default: canvas.txt)",
    )
    args = parser.parse_args()

    if args.dry_run:
        run_dry(args.vendor)
    else:
        run_full(args.vendor)
