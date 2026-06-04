"""Shared ChromaDB constants and index loader used by pipeline, tests, and ingest."""

import os
from pathlib import Path

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

BASE_DIR = Path(__file__).parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "vendor_proposals"
EMBEDDING_MODEL = "models/gemini-embedding-001"


def load_index() -> VectorStoreIndex:
    """Load the VectorStoreIndex from the persisted ChromaDB collection."""
    embed_model = GoogleGenAIEmbedding(
        model_name=EMBEDDING_MODEL,
        api_key=os.environ["GOOGLE_API_KEY"],
    )
    Settings.embed_model = embed_model
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(vector_store)
