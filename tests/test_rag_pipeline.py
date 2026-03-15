"""Unit tests for the RAG pipeline with mocked external APIs."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.schemas import Language, RAGQuery, RAGResult, SearchResult, SourceChunk, SourceType


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestSchemas:
    """Test Pydantic models for the RAG module."""

    def test_source_chunk_minimal(self):
        chunk = SourceChunk(
            id="chunk-1",
            text="Sample text",
            source=SourceType.SCRIPTURES,
            score=0.95,
        )
        assert chunk.id == "chunk-1"
        assert chunk.source == SourceType.SCRIPTURES
        assert chunk.language == Language.ITA

    def test_source_chunk_full_metadata(self):
        chunk = SourceChunk(
            id="chunk-2",
            text="And it came to pass...",
            source=SourceType.SCRIPTURES,
            score=0.88,
            language=Language.ENG,
            book="1 Nephi",
            chapter=1,
            verse="1-3",
        )
        assert chunk.book == "1 Nephi"
        assert chunk.chapter == 1
        assert chunk.verse == "1-3"
        assert chunk.language == Language.ENG

    def test_source_chunk_conference_metadata(self):
        chunk = SourceChunk(
            id="conf-1",
            text="Talk text...",
            source=SourceType.CONFERENCE,
            score=0.92,
            speaker="President Nelson",
            title="The Power of Faith",
            date="2023-10",
            url="https://example.com/talk",
        )
        assert chunk.speaker == "President Nelson"
        assert chunk.url == "https://example.com/talk"

    def test_rag_query_defaults(self):
        query = RAGQuery(question="What is faith?")
        assert query.language == Language.ITA
        assert query.top_k == 5
        assert len(query.sources) == len(SourceType)

    def test_rag_query_custom(self):
        query = RAGQuery(
            question="Cos'è la fede?",
            language=Language.ITA,
            sources=[SourceType.SCRIPTURES, SourceType.CONFERENCE],
            top_k=10,
        )
        assert len(query.sources) == 2
        assert query.top_k == 10

    def test_rag_query_validation(self):
        with pytest.raises(Exception):
            RAGQuery(question="ab")  # too short

    def test_rag_result(self):
        result = RAGResult(
            query="What is faith?",
            answer="Faith is...",
            sources=[],
            language=Language.ENG,
            model="claude-haiku-4-5-20241022",
        )
        assert result.answer == "Faith is..."

    def test_search_result(self):
        result = SearchResult(
            query="fede",
            chunks=[
                SourceChunk(
                    id="c1", text="text", source=SourceType.SCRIPTURES, score=0.9
                )
            ],
            language=Language.ITA,
        )
        assert len(result.chunks) == 1


# ---------------------------------------------------------------------------
# Embedder tests
# ---------------------------------------------------------------------------


class TestEmbedder:
    """Test the Voyage AI embedder wrapper."""

    @patch("rag.embedder.voyageai")
    def test_embed_documents(self, mock_voyageai):
        mock_client = MagicMock()
        mock_voyageai.Client.return_value = mock_client
        mock_client.embed.return_value = MagicMock(
            embeddings=[[0.1] * 1024, [0.2] * 1024]
        )

        from rag.embedder import Embedder

        embedder = Embedder(api_key="test-key")
        result = embedder.embed_documents(["text 1", "text 2"])

        assert len(result) == 2
        assert len(result[0]) == 1024
        mock_client.embed.assert_called_once_with(
            ["text 1", "text 2"],
            model="voyage-multilingual-2",
            input_type="document",
        )

    @patch("rag.embedder.voyageai")
    def test_embed_query(self, mock_voyageai):
        mock_client = MagicMock()
        mock_voyageai.Client.return_value = mock_client
        mock_client.embed.return_value = MagicMock(embeddings=[[0.5] * 1024])

        from rag.embedder import Embedder

        embedder = Embedder(api_key="test-key")
        result = embedder.embed_query("What is faith?")

        assert len(result) == 1024
        mock_client.embed.assert_called_once_with(
            ["What is faith?"],
            model="voyage-multilingual-2",
            input_type="query",
        )

    @patch("rag.embedder.voyageai")
    def test_embed_empty_list(self, mock_voyageai):
        from rag.embedder import Embedder

        embedder = Embedder(api_key="test-key")
        result = embedder.embed([])
        assert result == []


# ---------------------------------------------------------------------------
# VectorStore tests
# ---------------------------------------------------------------------------


class TestVectorStore:
    """Test the Pinecone vector store wrapper."""

    @patch("rag.vector_store.Pinecone")
    def test_upsert_chunks(self, mock_pinecone_cls):
        mock_index = MagicMock()
        mock_pinecone_cls.return_value.Index.return_value = mock_index

        from rag.vector_store import VectorStore

        store = VectorStore(api_key="test-key")
        count = store.upsert_chunks(
            ids=["id1", "id2"],
            embeddings=[[0.1] * 1024, [0.2] * 1024],
            metadata=[{"text": "a"}, {"text": "b"}],
            namespace="scriptures",
        )

        assert count == 2
        mock_index.upsert.assert_called_once()

    @patch("rag.vector_store.Pinecone")
    def test_upsert_batching(self, mock_pinecone_cls):
        mock_index = MagicMock()
        mock_pinecone_cls.return_value.Index.return_value = mock_index

        from rag.vector_store import VectorStore

        store = VectorStore(api_key="test-key")
        # 3 items with batch_size=2 → 2 upsert calls
        count = store.upsert_chunks(
            ids=["a", "b", "c"],
            embeddings=[[0.1] * 1024] * 3,
            metadata=[{"text": "x"}] * 3,
            namespace="conference",
            batch_size=2,
        )

        assert count == 3
        assert mock_index.upsert.call_count == 2

    @patch("rag.vector_store.Pinecone")
    def test_query(self, mock_pinecone_cls):
        mock_index = MagicMock()
        mock_pinecone_cls.return_value.Index.return_value = mock_index
        mock_index.query.return_value = {
            "matches": [
                {"id": "id1", "score": 0.95, "metadata": {"text": "hello"}},
                {"id": "id2", "score": 0.88, "metadata": {"text": "world"}},
            ]
        }

        from rag.vector_store import VectorStore

        store = VectorStore(api_key="test-key")
        results = store.query(
            vector=[0.1] * 1024,
            namespace="scriptures",
            top_k=2,
        )

        assert len(results) == 2
        assert results[0]["score"] == 0.95
        assert results[1]["metadata"]["text"] == "world"

    @patch("rag.vector_store.Pinecone")
    def test_query_with_filter(self, mock_pinecone_cls):
        mock_index = MagicMock()
        mock_pinecone_cls.return_value.Index.return_value = mock_index
        mock_index.query.return_value = {"matches": []}

        from rag.vector_store import VectorStore

        store = VectorStore(api_key="test-key")
        store.query(
            vector=[0.1] * 1024,
            namespace="conference",
            top_k=3,
            filter_dict={"language": "ita"},
        )

        call_kwargs = mock_index.query.call_args[1]
        assert call_kwargs["filter"] == {"language": "ita"}

    @patch("rag.vector_store.Pinecone")
    def test_list_namespaces(self, mock_pinecone_cls):
        mock_index = MagicMock()
        mock_pinecone_cls.return_value.Index.return_value = mock_index
        mock_index.describe_index_stats.return_value = {
            "namespaces": {
                "scriptures": {"vector_count": 1000},
                "conference": {"vector_count": 500},
            }
        }

        from rag.vector_store import VectorStore

        store = VectorStore(api_key="test-key")
        ns = store.list_namespaces()

        assert ns == {"scriptures": 1000, "conference": 500}


# ---------------------------------------------------------------------------
# Retriever tests
# ---------------------------------------------------------------------------


class TestRetriever:
    """Test the retriever combining embedder + vector store."""

    def _make_retriever(self):
        from rag.retriever import Retriever

        embedder = MagicMock()
        embedder.embed_query.return_value = [0.1] * 1024

        vector_store = MagicMock()
        vector_store.query.return_value = [
            {
                "id": "chunk-1",
                "score": 0.95,
                "metadata": {
                    "text": "La fede è...",
                    "book": "Alma",
                    "chapter": 32,
                    "verse": "21",
                },
            },
            {
                "id": "chunk-2",
                "score": 0.87,
                "metadata": {
                    "text": "Senza fede...",
                    "book": "Ebrei",
                    "chapter": 11,
                    "verse": "1",
                },
            },
        ]

        return Retriever(embedder, vector_store), embedder, vector_store

    def test_search_single_source(self):
        retriever, embedder, vs = self._make_retriever()
        results = retriever.search(
            query="Cos'è la fede?",
            sources=[SourceType.SCRIPTURES],
            language=Language.ITA,
            top_k=5,
        )

        assert len(results) == 2
        assert results[0].score >= results[1].score
        assert results[0].book == "Alma"
        embedder.embed_query.assert_called_once_with("Cos'è la fede?")

    def test_search_multiple_sources(self):
        retriever, _, vs = self._make_retriever()
        results = retriever.search(
            query="faith",
            sources=[SourceType.SCRIPTURES, SourceType.CONFERENCE],
            top_k=5,
        )

        # Called once per source
        assert vs.query.call_count == 2

    def test_search_results_sorted_by_score(self):
        retriever, _, _ = self._make_retriever()
        results = retriever.search(
            query="test", sources=[SourceType.SCRIPTURES], top_k=10
        )
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------


class TestGenerator:
    """Test the Claude answer generator."""

    @patch("rag.generator.anthropic")
    def test_generate_answer(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="La fede è la certezza...")]
        mock_client.messages.create.return_value = mock_response

        from rag.generator import Generator

        generator = Generator(api_key="test-key")
        chunks = [
            SourceChunk(
                id="c1",
                text="La fede è...",
                source=SourceType.SCRIPTURES,
                score=0.95,
                book="Alma",
                chapter=32,
                verse="21",
            )
        ]

        result = generator.generate(
            query="Cos'è la fede?",
            chunks=chunks,
            language=Language.ITA,
        )

        assert isinstance(result, RAGResult)
        assert result.answer == "La fede è la certezza..."
        assert result.query == "Cos'è la fede?"
        assert len(result.sources) == 1
        assert result.language == Language.ITA

        # Verify Claude was called correctly
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-haiku-4-5-20241022"
        assert "Rispondi in italiano" in call_kwargs["messages"][0]["content"]

    @patch("rag.generator.anthropic")
    def test_generate_english(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Faith is...")]
        mock_client.messages.create.return_value = mock_response

        from rag.generator import Generator

        generator = Generator(api_key="test-key")
        result = generator.generate(
            query="What is faith?",
            chunks=[],
            language=Language.ENG,
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "Answer in English" in call_kwargs["messages"][0]["content"]
        assert result.language == Language.ENG


# ---------------------------------------------------------------------------
# Pipeline integration tests (all external calls mocked)
# ---------------------------------------------------------------------------


class TestPipeline:
    """Test the full RAG pipeline with mocked components."""

    def _make_pipeline(self):
        from rag.pipeline import RAGPipeline

        embedder = MagicMock()
        vector_store = MagicMock()
        generator = MagicMock()

        embedder.embed_query.return_value = [0.1] * 1024
        vector_store.query.return_value = [
            {
                "id": "c1",
                "score": 0.95,
                "metadata": {
                    "text": "La fede è la speranza...",
                    "book": "Alma",
                    "chapter": 32,
                    "verse": "21",
                },
            }
        ]
        generator.generate.return_value = RAGResult(
            query="Cos'è la fede?",
            answer="La fede è la certezza delle cose sperate...",
            sources=[
                SourceChunk(
                    id="c1",
                    text="La fede è la speranza...",
                    source=SourceType.SCRIPTURES,
                    score=0.95,
                )
            ],
            language=Language.ITA,
            model="claude-haiku-4-5-20241022",
        )

        pipeline = RAGPipeline(
            embedder=embedder,
            vector_store=vector_store,
            generator=generator,
        )
        return pipeline, embedder, vector_store, generator

    def test_ask(self):
        pipeline, embedder, vs, gen = self._make_pipeline()
        result = pipeline.ask("Cos'è la fede?")

        assert isinstance(result, RAGResult)
        assert result.answer == "La fede è la certezza delle cose sperate..."
        gen.generate.assert_called_once()

    def test_ask_with_specific_sources(self):
        pipeline, _, vs, _ = self._make_pipeline()
        pipeline.ask(
            "test",
            sources=[SourceType.SCRIPTURES],
        )

        # Should only query one namespace
        assert vs.query.call_count == 1

    def test_search_no_generation(self):
        pipeline, _, vs, gen = self._make_pipeline()
        result = pipeline.search("fede")

        assert isinstance(result, SearchResult)
        assert len(result.chunks) > 0
        gen.generate.assert_not_called()

    def test_ask_from_query(self):
        pipeline, _, _, gen = self._make_pipeline()
        query = RAGQuery(
            question="Cos'è la fede?",
            language=Language.ITA,
            sources=[SourceType.SCRIPTURES],
            top_k=3,
        )
        result = pipeline.ask_from_query(query)

        assert isinstance(result, RAGResult)

    def test_ask_defaults_to_all_sources(self):
        pipeline, _, vs, _ = self._make_pipeline()
        pipeline.ask("test question")

        # Should query all 4 source namespaces
        assert vs.query.call_count == len(SourceType)
