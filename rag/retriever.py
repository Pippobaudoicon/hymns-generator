"""Retriever: combines embedder + vector store to find relevant chunks."""

from .embedder import Embedder
from .schemas import Language, SourceChunk, SourceType
from .vector_store import VectorStore


class Retriever:
    """Retrieves relevant source chunks for a query."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self._embedder = embedder
        self._vector_store = vector_store

    def search(
        self,
        query: str,
        sources: list[SourceType],
        language: Language = Language.ITA,
        top_k: int = 5,
    ) -> list[SourceChunk]:
        """Search for relevant chunks across one or more source namespaces.

        Args:
            query: The search query text.
            sources: Source namespaces to search in.
            language: Filter results by language.
            top_k: Number of results per namespace.

        Returns:
            List of SourceChunk results, sorted by score descending.
        """
        query_vector = self._embedder.embed_query(query)

        all_chunks: list[SourceChunk] = []
        lang_filter = {"language": language.value}

        for source in sources:
            matches = self._vector_store.query(
                vector=query_vector,
                namespace=source.value,
                top_k=top_k,
                filter_dict=lang_filter,
            )

            for match in matches:
                meta = match.get("metadata", {})
                chunk = SourceChunk(
                    id=match["id"],
                    text=meta.get("text", ""),
                    source=source,
                    score=match["score"],
                    language=language,
                    book=meta.get("book"),
                    chapter=meta.get("chapter"),
                    verse=meta.get("verse"),
                    speaker=meta.get("speaker"),
                    title=meta.get("title"),
                    date=meta.get("date"),
                    section=meta.get("section"),
                    url=meta.get("url"),
                )
                all_chunks.append(chunk)

        # Sort all results by score descending and return top_k overall
        all_chunks.sort(key=lambda c: c.score, reverse=True)
        return all_chunks[:top_k]
