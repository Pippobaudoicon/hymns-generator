"""Pinecone vector store wrapper."""

import os
from typing import Any

from pinecone import Pinecone

from .embedder import Embedder
from .schemas import SourceType


class VectorStore:
    """Wraps Pinecone for vector storage and retrieval."""

    INDEX_NAME = "lds-rag"
    METRIC = "cosine"
    DIMENSION = Embedder.DIMENSION

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self._pc = Pinecone(api_key=self._api_key)
        self._index = self._pc.Index(self.INDEX_NAME)

    def upsert_chunks(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
        namespace: str,
        batch_size: int = 100,
    ) -> int:
        """Upsert embedding vectors with metadata into a namespace.

        Args:
            ids: Unique IDs for each vector.
            embeddings: Embedding vectors.
            metadata: Metadata dicts (one per vector).
            namespace: Pinecone namespace (e.g. "scriptures", "conference").
            batch_size: Vectors per upsert batch.

        Returns:
            Total number of vectors upserted.
        """
        vectors = [
            {"id": id_, "values": emb, "metadata": meta}
            for id_, emb, meta in zip(ids, embeddings, metadata)
        ]

        total = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self._index.upsert(vectors=batch, namespace=namespace)
            total += len(batch)

        return total

    def query(
        self,
        vector: list[float],
        namespace: str,
        top_k: int = 5,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query the vector index for similar vectors.

        Args:
            vector: Query embedding vector.
            namespace: Pinecone namespace to search.
            top_k: Number of results to return.
            filter_dict: Optional metadata filter.

        Returns:
            List of match dicts with id, score, and metadata.
        """
        kwargs: dict[str, Any] = {
            "vector": vector,
            "namespace": namespace,
            "top_k": top_k,
            "include_metadata": True,
        }
        if filter_dict:
            kwargs["filter"] = filter_dict

        result = self._index.query(**kwargs)

        return [
            {
                "id": match["id"],
                "score": match["score"],
                "metadata": match.get("metadata", {}),
            }
            for match in result["matches"]
        ]

    def describe_namespace(self, namespace: str) -> dict[str, Any]:
        """Get stats for a specific namespace."""
        stats = self._index.describe_index_stats()
        ns_stats = stats.get("namespaces", {}).get(namespace, {})
        return {"namespace": namespace, "vector_count": ns_stats.get("vector_count", 0)}

    def list_namespaces(self) -> dict[str, int]:
        """List all namespaces and their vector counts."""
        stats = self._index.describe_index_stats()
        return {
            ns: info.get("vector_count", 0)
            for ns, info in stats.get("namespaces", {}).items()
        }
