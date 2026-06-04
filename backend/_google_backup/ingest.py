"""
ingest.py — VendorLens RAG ingestion script.

Loads all vendor proposal text files from data/vendor_proposals/ (all bundle
subfolders: lms/, payroll/, erp/) into ChromaDB using LlamaIndex with Google
embeddings. Stores the bare filename as metadata so agents can filter retrieval
to a specific vendor document regardless of which subfolder it lives in.

Run once before starting the pipeline:
    cd backend
    python scripts/ingest.py

Re-run with --force if vendor_proposals/ changes. ChromaDB is persisted to
data/chroma_db/ and skipped on subsequent runs unless --force is passed.
"""

import argparse
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Validate required env var before importing heavy dependencies
# ---------------------------------------------------------------------------
if not os.getenv("GOOGLE_API_KEY"):
    sys.exit("ERROR: GOOGLE_API_KEY is not set. Add it to backend/.env")

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

from tools.chroma import BASE_DIR, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL

DOCS_DIR = BASE_DIR / "data" / "vendor_proposals"


def build_index(force: bool = False) -> VectorStoreIndex:
    """
    Ingest all .txt files in DOCS_DIR into ChromaDB.

    Each document is chunked with SentenceSplitter (512 tokens, 50 overlap).
    The LlamaIndex default metadata for each node includes `file_name` which
    agents use as a filter key when retrieving chunks for a specific vendor.

    Returns the populated VectorStoreIndex so it can be used immediately
    in test_rag.py without re-loading from disk.
    """
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if not force:
        existing = chroma_client.list_collections()
        if any(c.name == COLLECTION_NAME for c in existing):
            count = chroma_client.get_collection(COLLECTION_NAME).count()
            print(f"ChromaDB collection '{COLLECTION_NAME}' already exists "
                  f"({count} chunks). Skipping ingestion. Use --force to rebuild.")
            # Still return a usable index
            chroma_collection = chroma_client.get_collection(COLLECTION_NAME)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            embed_model = GoogleGenAIEmbedding(
                model_name=EMBEDDING_MODEL,
                api_key=os.environ["GOOGLE_API_KEY"],
            )
            Settings.embed_model = embed_model
            return VectorStoreIndex.from_vector_store(vector_store)

    print(f"Loading documents from: {DOCS_DIR}")
    documents = SimpleDirectoryReader(
        input_dir=str(DOCS_DIR),
        required_exts=[".txt"],
        filename_as_id=True,
        recursive=True,
        file_metadata=lambda p: {"file_name": Path(p).name},
    ).load_data()
    print(f"  Loaded {len(documents)} document(s): "
          f"{[d.metadata.get('file_name') for d in documents]}")

    # Configure embedding model globally for LlamaIndex
    embed_model = GoogleGenAIEmbedding(
        model_name=EMBEDDING_MODEL,
        api_key=os.environ["GOOGLE_API_KEY"],
    )
    Settings.embed_model = embed_model

    # Chunking
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)

    # ChromaDB vector store
    if force:
        try:
            chroma_client.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection '{COLLECTION_NAME}' (--force)")
        except Exception:
            pass

    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("Building index (this calls the Google Embeddings API)...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[splitter],
        show_progress=True,
    )

    count = chroma_collection.count()
    print(f"  Done. {count} chunks stored in ChromaDB at {CHROMA_DIR}")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest vendor proposals into ChromaDB")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing collection and rebuild from scratch",
    )
    args = parser.parse_args()
    build_index(force=args.force)
    print("Ingestion complete.")

    # Signal the running API to reload its index cache.
    # If the API isn't running yet, this step is skipped — the fresh index
    # will be loaded automatically when the API starts.
    try:
        req = urllib.request.Request(
            "http://localhost:8000/reload",
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                print("  API cache reloaded — new index is live immediately.")
    except urllib.error.URLError:
        print("  API not running — fresh index will load on next 'docker compose up api'.")
