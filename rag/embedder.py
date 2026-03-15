"""Voyage AI embedding wrapper."""

import os

import voyageai


class Embedder:
    """Wraps the Voyage AI API for text embedding."""

    MODEL = "voyage-multilingual-2"
    DIMENSION = 1024

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("VOYAGE_API_KEY", "")
        self._client = voyageai.Client(api_key=self._api_key)

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]]:
        """Embed a list of texts using Voyage AI.

        Args:
            texts: Texts to embed.
            input_type: "document" for indexing, "query" for search queries.

        Returns:
            List of embedding vectors (each 1024-dim).
        """
        if not texts:
            return []

        result = self._client.embed(
            texts,
            model=self.MODEL,
            input_type=input_type,
        )
        return result.embeddings

    def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        return self.embed([query], input_type="query")[0]

    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Embed documents for indexing."""
        return self.embed(documents, input_type="document")
