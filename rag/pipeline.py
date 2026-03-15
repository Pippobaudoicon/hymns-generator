"""RAG pipeline orchestrating embedder, retriever, and generator."""

from .embedder import Embedder
from .generator import Generator
from .retriever import Retriever
from .schemas import Language, RAGQuery, RAGResult, SearchResult, SourceType
from .vector_store import VectorStore


class RAGPipeline:
    """Orchestrates the full RAG pipeline: embed → retrieve → generate."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        vector_store: VectorStore | None = None,
        retriever: Retriever | None = None,
        generator: Generator | None = None,
    ):
        self._embedder = embedder or Embedder()
        self._vector_store = vector_store or VectorStore()
        self._retriever = retriever or Retriever(self._embedder, self._vector_store)
        self._generator = generator or Generator()

    def ask(
        self,
        question: str,
        language: Language = Language.ITA,
        sources: list[SourceType] | None = None,
        top_k: int = 5,
    ) -> RAGResult:
        """Full RAG pipeline: retrieve relevant chunks and generate an answer.

        Args:
            question: The user's question.
            language: Response language.
            sources: Source namespaces to search. Defaults to all.
            top_k: Number of chunks to retrieve.

        Returns:
            RAGResult with generated answer and source citations.
        """
        if sources is None:
            sources = list(SourceType)

        chunks = self._retriever.search(
            query=question,
            sources=sources,
            language=language,
            top_k=top_k,
        )

        return self._generator.generate(
            query=question,
            chunks=chunks,
            language=language,
        )

    def search(
        self,
        query: str,
        language: Language = Language.ITA,
        sources: list[SourceType] | None = None,
        top_k: int = 5,
    ) -> SearchResult:
        """Semantic search only (no LLM generation).

        Args:
            query: The search query.
            language: Filter by language.
            sources: Source namespaces to search. Defaults to all.
            top_k: Number of results.

        Returns:
            SearchResult with matching chunks.
        """
        if sources is None:
            sources = list(SourceType)

        chunks = self._retriever.search(
            query=query,
            sources=sources,
            language=language,
            top_k=top_k,
        )

        return SearchResult(
            query=query,
            chunks=chunks,
            language=language,
        )

    def ask_from_query(self, query: RAGQuery) -> RAGResult:
        """Run the pipeline from a RAGQuery model."""
        return self.ask(
            question=query.question,
            language=query.language,
            sources=query.sources,
            top_k=query.top_k,
        )
