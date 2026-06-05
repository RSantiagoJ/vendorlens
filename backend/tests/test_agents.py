"""
test_agents.py — Day 3 checkpoint: risk + scoring agents.

Runs ExtractionAgent, RiskAgent, and ScoringAgent against all three
dummy proposals and asserts the expected ordering:
  - Vendor B (Canvas) scores highest overall
  - Vendor A (Blackboard) scores lowest overall
  - Vendor A has 3+ HIGH severity risk flags

Usage:
    cd backend
    python tests/test_agents.py

Prerequisites:
    - ANTHROPIC_API_KEY set in backend/.env
    - ChromaDB index built: python ingest.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    sys.exit("ERROR: ANTHROPIC_API_KEY is not set in backend/.env")

from agents.extraction_agent import ExtractionAgent
from agents.risk_agent import RiskAgent
from agents.scoring_agent import ScoringAgent
from tools.chroma import load_index

VENDORS = [
    ("blackboard.txt", "Blackboard"),
    ("canvas.txt", "Canvas"),
    ("brightspace.txt", "Brightspace"),
]


def run_checks():
    print("Loading ChromaDB index...")
    try:
        index = load_index()
    except Exception as e:
        sys.exit(
            f"ERROR: Could not load ChromaDB index.\n"
            f"  Run 'python ingest.py' first.\n"
            f"  Details: {e}"
        )

    extraction_agent = ExtractionAgent(index)
    risk_agent = RiskAgent()
    scoring_agent = ScoringAgent()
    print(f"Scoring LLM : {scoring_agent.llm_name}\n")

    results: dict[str, dict] = {}

    for filename, label in VENDORS:
        print(f"{'='*60}")
        print(f"{label} — {filename}")

        print("  [1/3] Extracting...")
        proposal = extraction_agent.extract(filename)
        print(f"        vendor_name : {proposal.vendor_name}")
        print(f"        total_cost  : {proposal.total_cost}")
        print(f"        liability   : {proposal.liability_cap}")

        print("  [2/3] Analyzing risks...")
        flags = risk_agent.analyze(proposal)
        high = [f for f in flags if f.severity == "HIGH"]
        med  = [f for f in flags if f.severity == "MEDIUM"]
        low  = [f for f in flags if f.severity == "LOW"]
        print(f"        HIGH={len(high)}  MEDIUM={len(med)}  LOW={len(low)}")
        for f in high:
            print(f"        HIGH  {f.clause}: {f.explanation[:72]}...")

        print("  [3/3] Scoring...")
        scorecard = scoring_agent.score(proposal, flags)
        print(f"        platform_functionality  : {scorecard.platform_functionality.score}")
        print(f"        accessibility_compliance: {scorecard.accessibility_compliance.score}")
        print(f"        integration_capability  : {scorecard.integration_capability.score}")
        print(f"        pricing_transparency    : {scorecard.pricing_transparency.score}")
        print(f"        security_and_compliance : {scorecard.security_and_compliance.score}")
        print(f"        support_and_training    : {scorecard.support_and_training.score}")
        print(f"        enterprise_readiness    : {scorecard.enterprise_readiness.score}")
        print(f"        risk_level              : {scorecard.risk_level.score}")
        print(f"        OVERALL                 : {scorecard.overall}")

        results[label] = {
            "proposal": proposal,
            "flags": flags,
            "high_count": len(high),
            "scorecard": scorecard,
        }

    # ------------------------------------------------------------------
    # Checkpoint assertions
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("CHECKPOINT ASSERTIONS")
    print(f"{'='*60}")

    score_a = results["Vendor A (Blackboard)"]["scorecard"].overall
    score_b = results["Vendor B (Canvas)"]["scorecard"].overall
    score_c = results["Vendor C (Brightspace)"]["scorecard"].overall
    high_a  = results["Vendor A (Blackboard)"]["high_count"]

    print(f"\nOverall scores:")
    print(f"  Vendor A (Blackboard) : {score_a}")
    print(f"  Vendor B (Canvas)     : {score_b}")
    print(f"  Vendor C (Brightspace): {score_c}")
    print(f"  Vendor A HIGH flags   : {high_a}")

    failures = []

    if score_b > score_a and score_b > score_c:
        print("[PASS] Vendor B (Canvas) scored highest")
    else:
        failures.append(
            f"Score ordering FAILED: B={score_b} should be > A={score_a} and C={score_c}"
        )

    if score_a < score_b and score_a < score_c:
        print("[PASS] Vendor A (Blackboard) scored lowest")
    else:
        failures.append(
            f"Vendor A not lowest: A={score_a}, B={score_b}, C={score_c}"
        )

    if high_a >= 3:
        print(f"[PASS] Vendor A has {high_a} HIGH risk flags (≥ 3 expected)")
    else:
        failures.append(
            f"Vendor A HIGH flags FAILED: expected ≥ 3, got {high_a}"
        )

    print()
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        sys.exit(1)
    else:
        print("All checks passed. Day 3 checkpoint complete.")


if __name__ == "__main__":
    run_checks()
