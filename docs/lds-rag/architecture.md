# LDS RAG Tool — Architecture & Stack

## High-level flow

```
User (rag.html)
    ↓ HTTP
FastAPI /rag/* routes
    ↓
RAG Pipeline (rag/pipeline.py)
    ├── 1. Embed query       → embedder.py (sentence-transformers, local)
    ├── 2. Semantic search   → retriever.py (ChromaDB)
    └── 3. Generate answer   → generator.py (Claude API)
    ↓
Response with answer + cited sources
```

## Component choices

### Vector DB: ChromaDB (embedded)
- Runs in-process, no extra service to manage
- Persists to disk (e.g. `data/chromadb/`)
- One collection per source: `scriptures`, `conference`, `liahona`, `handbook`
- **Why not Pinecone/Supabase pgvector**: overkill for a small tool; ChromaDB is simpler and free

### Embeddings: `paraphrase-multilingual-MiniLM-L12-v2`
- 118M params, 384 dimensions
- Supports Italian + English natively (trained on 50+ languages)
- Runs locally via `sentence-transformers` — no API cost per embedding
- **Why not OpenAI embeddings**: adds dependency + cost; local is fine at this scale

### LLM: Claude claude-sonnet-4-6 (Anthropic API)
- Used only for answer generation and content generation (not for embeddings)
- System prompt instructs to cite sources and stay grounded in retrieved context
- **Model ID**: `claude-sonnet-4-6`
- Requires `ANTHROPIC_API_KEY` in `.env`

## Module structure

```
rag/
├── __init__.py
├── vector_store.py     # ChromaDB wrapper — init, add, query collections
├── embedder.py         # Load sentence-transformers model, embed text
├── retriever.py        # Semantic search: query → top-K chunks with metadata
├── generator.py        # Claude API call: context + query → answer + sources
├── pipeline.py         # Orchestrates: embed → retrieve → generate
└── schemas.py          # Pydantic models: RAGQuery, RAGResult, SearchResult

api/routes/
└── rag.py              # FastAPI router, registered in app.py

scripts/
├── ingest_scriptures.py
├── ingest_conference.py
├── ingest_liahona.py
└── ingest_handbook.py

static/
└── rag.html            # Chat/search UI (vanilla JS, matches existing style)

data/
└── chromadb/           # ChromaDB persistent storage (gitignored)
```

## Chunking strategy

- Chunk size: ~400 tokens with 50-token overlap
- Metadata stored per chunk: `source`, `book/volume`, `chapter`, `verse` (scriptures),
  `speaker`, `title`, `date`, `url` (talks/articles), `section` (handbook), `language`
- Language stored as metadata to allow language-filtered search

## RAG answer format

Every answer from the generator includes:
- The answer text (in the user's query language)
- List of source citations: title, author/book, URL if available

## Environment variables needed

```
ANTHROPIC_API_KEY=sk-ant-...
CHROMA_DB_PATH=data/chromadb        # default
RAG_COLLECTION_LANGUAGES=ita,eng    # which language versions to ingest
```
