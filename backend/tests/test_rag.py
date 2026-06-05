"""
test_rag.py — Day 1 checkpoint: verify RAG retrieval works correctly.

Runs two targeted queries against the ChromaDB index built by ingest.py
and asserts the results come from the correct vendor documents and contain
the expected values.

Usage:
    cd backend
    python tests/test_rag.py

Expected output:
    [PASS] renewal terms query returned chunks from canvas.txt
    [PASS] liability cap query returned chunk from blackboard.txt
           containing expected value "$16,250"
    All checks passed.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core import VectorStoreIndex

from tools.chroma import load_index

VENDOR_A = "blackboard.txt"
VENDOR_B = "canvas.txt"
VENDOR_C = "brightspace.txt"


def query_vendor(index: VectorStoreIndex, query: str, filename: str, top_k: int = 5):
    """Retrieve chunks filtered to a single vendor document."""
    filters = MetadataFilters(filters=[
        MetadataFilter(key="file_name", value=filename)
    ])
    retriever = index.as_retriever(
        filters=filters,
        similarity_top_k=top_k,
    )
    return retriever.retrieve(query)


def run_checks():
    print("Loading index from ChromaDB...")
    try:
        index = load_index()
    except Exception as e:
        sys.exit(
            f"ERROR: Could not load ChromaDB index.\n"
            f"  Run 'python ingest.py' first.\n"
            f"  Details: {e}"
        )

    failures = []

    # ------------------------------------------------------------------
    # Check 1: "renewal terms" filtered to Vendor B returns correct chunks
    # ------------------------------------------------------------------
    print("\nCheck 1: query='renewal terms', vendor=canvas.txt")
    results = query_vendor(index, "renewal terms", VENDOR_B)

    if not results:
        failures.append("Check 1 FAILED: no results returned for 'renewal terms' on Vendor B")
    else:
        filenames = [r.metadata.get("file_name", "") for r in results]
        wrong = [f for f in filenames if f != VENDOR_B]
        if wrong:
            failures.append(
                f"Check 1 FAILED: results include chunks from wrong files: {wrong}"
            )
        else:
            combined = " ".join(r.get_content() for r in results).lower()
            if "renewal" not in combined and "auto-renew" not in combined:
                failures.append(
                    "Check 1 FAILED: chunks don't mention renewal terms"
                )
            else:
                print(f"  [PASS] Got {len(results)} chunk(s) from {VENDOR_B}")
                for r in results:
                    snippet = r.get_content()[:120].replace("\n", " ")
                    print(f"    → {snippet}...")

    # ------------------------------------------------------------------
    # Check 2: "liability cap" filtered to Vendor A returns $16,250
    # ------------------------------------------------------------------
    print("\nCheck 2: query='liability cap', vendor=blackboard.txt")
    results = query_vendor(index, "liability cap", VENDOR_A)

    if not results:
        failures.append("Check 2 FAILED: no results returned for 'liability cap' on Vendor A")
    else:
        filenames = [r.metadata.get("file_name", "") for r in results]
        wrong = [f for f in filenames if f != VENDOR_A]
        if wrong:
            failures.append(
                f"Check 2 FAILED: results include chunks from wrong files: {wrong}"
            )
        else:
            combined = " ".join(r.get_content() for r in results)
            if "16,250" not in combined:
                failures.append(
                    f"Check 2 FAILED: expected '$16,250' not found in retrieved chunks.\n"
                    f"  Retrieved: {combined[:300]}"
                )
            else:
                print(f"  [PASS] Got {len(results)} chunk(s) from {VENDOR_A} containing '$16,250'")
                for r in results:
                    snippet = r.get_content()[:120].replace("\n", " ")
                    print(f"    → {snippet}...")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    if failures:
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("All checks passed. Day 1 checkpoint complete.")


if __name__ == "__main__":
    run_checks()
