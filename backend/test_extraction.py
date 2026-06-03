"""
test_extraction.py — Day 2 checkpoint: verify ExtractionAgent works.

Runs ExtractionAgent against all three dummy proposals and asserts
key field values against the expected data in dummy_data.md.

Usage:
    cd backend
    python test_extraction.py

Prerequisites:
    - GOOGLE_API_KEY set in backend/.env (required — embeddings + Gemini 3.5 Flash)
    - ChromaDB index built (run python ingest.py first)

Expected output:
    [PASS] Vendor B total_cost contains $158,000
    [PASS] Vendor B renewal_terms: no auto-renewal
    [PASS] Vendor B liability_cap contains $3,000,000
    [PASS] Vendor A total_cost contains $195,000
    [PASS] Vendor A renewal_terms: 30-day opt-out window
    [PASS] Vendor A liability_cap contains $16,250
    [PASS] Vendor C vendor_name: CampusVoice
    All checks passed. Day 2 checkpoint complete.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    sys.exit("ERROR: GOOGLE_API_KEY is not set in backend/.env")

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from agents.extraction_agent import ExtractionAgent as AgentClass

print("Using Gemini 3.5 Flash")

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "vendor_proposals"

VENDOR_A = "vendor_a_pulsemedia.txt"
VENDOR_B = "vendor_b_socialbridge.txt"
VENDOR_C = "vendor_c_campusvoice.txt"


def load_index() -> VectorStoreIndex:
    embed_model = GoogleGenAIEmbedding(
        model_name="models/gemini-embedding-001",
        api_key=os.environ["GOOGLE_API_KEY"],
    )
    Settings.embed_model = embed_model
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    chroma_collection = chroma_client.get_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return VectorStoreIndex.from_vector_store(vector_store)


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

    agent = AgentClass(index)
    failures = []

    # ------------------------------------------------------------------
    # Vendor B — SocialBridge Solutions (expected: highest score, clean)
    # ------------------------------------------------------------------
    print(f"\nExtracting {VENDOR_B}...")
    b = agent.extract(VENDOR_B)
    print(f"  vendor_name:    {b.vendor_name}")
    print(f"  total_cost:     {b.total_cost}")
    print(f"  renewal_terms:  {b.renewal_terms}")
    print(f"  liability_cap:  {b.liability_cap}")
    print(f"  governing_law:  {b.governing_law}")
    print(f"  security_certs: {b.security_certifications}")

    if b.total_cost and "158,000" in b.total_cost:
        print("  [PASS] total_cost contains $158,000")
    else:
        failures.append(f"Vendor B total_cost FAILED: expected '$158,000', got '{b.total_cost}'")

    renewal_b = (b.renewal_terms or "").lower()
    if "no auto" in renewal_b or "does not auto" in renewal_b or "affirmative" in renewal_b:
        print("  [PASS] renewal_terms: no auto-renewal")
    else:
        failures.append(f"Vendor B renewal_terms FAILED: expected no auto-renewal, got '{b.renewal_terms}'")

    if b.liability_cap and "3,000,000" in b.liability_cap:
        print("  [PASS] liability_cap contains $3,000,000")
    else:
        failures.append(f"Vendor B liability_cap FAILED: expected '$3,000,000', got '{b.liability_cap}'")

    # ------------------------------------------------------------------
    # Vendor A — PulseMedia Inc. (expected: most HIGH risk flags)
    # ------------------------------------------------------------------
    print(f"\nExtracting {VENDOR_A}...")
    a = agent.extract(VENDOR_A)
    print(f"  vendor_name:    {a.vendor_name}")
    print(f"  total_cost:     {a.total_cost}")
    print(f"  renewal_terms:  {a.renewal_terms}")
    print(f"  liability_cap:  {a.liability_cap}")
    print(f"  governing_law:  {a.governing_law}")
    print(f"  security_certs: {a.security_certifications}")

    if a.total_cost and "195,000" in a.total_cost:
        print("  [PASS] total_cost contains $195,000")
    else:
        failures.append(f"Vendor A total_cost FAILED: expected '$195,000', got '{a.total_cost}'")

    if a.renewal_terms and "30" in a.renewal_terms:
        print("  [PASS] renewal_terms: 30-day opt-out window")
    else:
        failures.append(f"Vendor A renewal_terms FAILED: expected 30-day opt-out, got '{a.renewal_terms}'")

    if a.liability_cap and "16,250" in a.liability_cap:
        print("  [PASS] liability_cap contains $16,250")
    else:
        failures.append(f"Vendor A liability_cap FAILED: expected '$16,250', got '{a.liability_cap}'")

    # ------------------------------------------------------------------
    # Vendor C — CampusVoice Technologies (sanity check)
    # ------------------------------------------------------------------
    print(f"\nExtracting {VENDOR_C}...")
    c = agent.extract(VENDOR_C)
    print(f"  vendor_name:    {c.vendor_name}")
    print(f"  total_cost:     {c.total_cost}")
    print(f"  governing_law:  {c.governing_law}")
    print(f"  security_certs: {c.security_certifications}")

    if c.vendor_name and "campus" in c.vendor_name.lower():
        print("  [PASS] vendor_name: CampusVoice")
    else:
        failures.append(f"Vendor C vendor_name FAILED: expected CampusVoice, got '{c.vendor_name}'")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print()
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        sys.exit(1)
    else:
        print("All checks passed. Day 2 checkpoint complete.")


if __name__ == "__main__":
    run_checks()
