"""Shared ChromaDB constants and index loader used by pipeline, tests, and ingest."""

import threading
from pathlib import Path

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

BASE_DIR = Path(__file__).parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "vendor_proposals"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

_index: VectorStoreIndex | None = None
_index_lock = threading.Lock()


def load_index() -> VectorStoreIndex:
    """Load the VectorStoreIndex from the persisted ChromaDB collection."""
    global _index
    if _index is not None:
        return _index
    with _index_lock:
        if _index is not None:
            return _index
        Settings.embed_model = FastEmbedEmbedding(model_name=EMBEDDING_MODEL)
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = chroma_client.get_collection(COLLECTION_NAME)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        _index = VectorStoreIndex.from_vector_store(vector_store)
    return _index
