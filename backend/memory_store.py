"""
Phase 5: Vector DB / RAG Memory Loop
Persistent ChromaDB store for failed experiments with semantic retrieval.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
import uuid

_COLLECTION_NAME = "failed_experiments"
_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")

_embedding_model: SentenceTransformer | None = None
_chroma_client: chromadb.ClientAPI | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embedding_model


def _get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.Client(Settings(
            persist_directory=_PERSIST_DIR,
            anonymized_telemetry=False,
        ))
    return _chroma_client


def _get_collection():
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def save_failed_molecule(smiles: str, failure_reason: str) -> str:
    """Embed the failure reason and store the SMILES + reason in ChromaDB."""
    model = _get_embedding_model()
    collection = _get_collection()

    embedding = model.encode(failure_reason).tolist()
    doc_id = str(uuid.uuid4())

    collection.add(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[failure_reason],
        metadatas=[{"smiles": smiles, "failure_reason": failure_reason}],
    )
    return doc_id


def retrieve_past_failures(query_context: str, n_results: int = 2) -> list[dict]:
    """Similarity search over failed_experiments; returns top-N matches."""
    model = _get_embedding_model()
    collection = _get_collection()

    if collection.count() == 0:
        return []

    query_embedding = model.encode(query_context).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
    )

    failures: list[dict] = []
    if results and results["metadatas"]:
        for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
            failures.append({
                "smiles": meta.get("smiles", ""),
                "failure_reason": doc,
            })
    return failures
