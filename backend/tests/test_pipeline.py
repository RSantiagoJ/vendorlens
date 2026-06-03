"""
test_pipeline.py — Day 4 checkpoint

Runs the full LangGraph pipeline against all three dummy vendor proposals
end to end and verifies the memo recommends Vendor B (Canvas by Instructure).

Usage:
    cd backend
    python tests/test_pipeline.py

Prerequisites:
    - GOOGLE_API_KEY set in backend/.env  (embeddings + Gemini for extraction/risk/scoring)
    - ANTHROPIC_API_KEY set in backend/.env  (required — memo_agent uses Claude Sonnet 4.6)
    - LANGCHAIN_API_KEY set in backend/.env  (optional — enables LangSmith tracing)
    - ChromaDB index built: python ingest.py

Expected output:
    Pipeline complete. Status: done
    [PASS] Memo recommends Vendor B / Canvas
    Day 4 checkpoint complete.
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--count", type=int, default=2, choices=[1, 2, 3],
                    help="Number of vendor proposals to run (default: 2)")
args = parser.parse_args()

if not os.getenv("GOOGLE_API_KEY"):
    sys.exit("ERROR: GOOGLE_API_KEY is not set in backend/.env")
if not os.getenv("ANTHROPIC_API_KEY"):
    sys.exit("ERROR: ANTHROPIC_API_KEY is not set in backend/.env (required for MemoAgent)")

from graph.pipeline import build_pipeline
from graph.state import ProposalState, VendorLensState

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data" / "dummy_docs"

VENDORS = [
    "vendor_a_blackboard.txt",
    "vendor_b_canvas.txt",
    "vendor_c_brightspace.txt",
]


def run_pipeline():
    print("Building pipeline (loads index + initializes agents)...")
    try:
        graph = build_pipeline()
    except Exception as e:
        sys.exit(
            f"ERROR: Could not build pipeline.\n"
            f"  Ensure ingest.py has been run and API keys are set.\n"
            f"  Details: {e}"
        )

    # Load raw text for each vendor file
    pending = []
    for filename in VENDORS[: args.count]:
        path = DATA_DIR / filename
        if not path.exists():
            sys.exit(f"ERROR: {path} not found. Check data/dummy_docs/")
        pending.append({"filename": filename, "raw_text": path.read_text()})

    initial_state = {
        "pending": pending,
        "extracted": [],
        "with_risks": [],
        "proposals": [],
        "memo": None,
        "status": "pending",
        "error": None,
    }

    print(f"\nRunning pipeline on {len(pending)} proposals...")
    print("  Extraction, Risk, and Scoring each run in parallel (3 concurrent LLM calls per stage)")
    print("  Memo runs sequentially after all scoring completes\n")

    result = graph.invoke(initial_state)

    print(f"\nPipeline complete. Status: {result['status']}")

    if result.get("error"):
        print(f"Error recorded: {result['error']}")

    if result["status"] == "error":
        sys.exit("Pipeline ended in error state.")

    if result["status"] != "done":
        sys.exit(f"Pipeline did not complete. status={result['status']}")

    # Convert to VendorLensState for structured access
    proposals = [ProposalState(**p) for p in result["proposals"]]
    state = VendorLensState(
        proposals=proposals,
        memo=result["memo"],
        status=result["status"],
    )

    # Print per-vendor summary
    print("\nVendor summary:")
    for p in state.proposals:
        vendor = (p.extracted.vendor_name if p.extracted else None) or p.filename
        overall = p.scores.overall if p.scores else "N/A"
        risk_counts = Counter(f.severity for f in (p.risks or []))
        print(f"  {vendor}")
        print(f"    Overall score : {overall}")
        print(f"    Risk flags    : HIGH={risk_counts['HIGH']}  MEDIUM={risk_counts['MEDIUM']}")

    # Print memo excerpt
    print("\nMemo excerpt (first 600 chars):")
    print("-" * 60)
    print((state.memo or "(no memo)")[:600])
    print("-" * 60)

    # Checkpoint assertion
    memo_lower = (state.memo or "").lower()
    if "canvas" in memo_lower or "vendor b" in memo_lower:
        print("\n[PASS] Memo recommends Vendor B / Canvas")
    else:
        sys.exit("\nFAIL: Memo does not mention Canvas or Vendor B as recommended vendor")

    print("\nDay 4 checkpoint complete.")
    if os.getenv("LANGCHAIN_API_KEY"):
        print("LangSmith trace visible at: https://smith.langchain.com")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'vendorlens')}")


if __name__ == "__main__":
    run_pipeline()
