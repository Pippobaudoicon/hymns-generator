# LDS RAG Tool — Architecture & Stack

## Design principle

The VPS hosting this app is small. The RAG module must not add meaningful disk, RAM, or CPU
pressure to it. Solution: outsource all heavy components to free hosted services.
The VPS stays a thin HTTP routing layer — it only runs FastAPI and makes API calls.

## High-level flow

```
User (rag.html)
    ↓ HTTP
FastAPI /rag/* routes   ← runs on VPS (lightweight, no model, no vector DB)
    ↓
RAG Pipeline (rag/pipeline.py)
    ├── 1. Embed query    → Voyage AI API      (external, free tier)
    ├── 2. Semantic search → Pinecone API      (external, free tier)
    └── 3. Generate answer → Anthropic API     (external, pay-per-token)
    ↓
Response with answer + cited sources
```

## Component choices

### Embeddings: Voyage AI (`voyage-multilingual-2`)
- **Free tier**: 200M tokens/month — far more than needed
- Natively multilingual (Italian + English and many more)
- State-of-the-art retrieval quality, better than MiniLM
- Pure API call — **zero RAM, zero disk on VPS**
- Dimension: 1024
- **Why not local sentence-transformers**: ~420 MB model in RAM, unacceptable on small VPS
- **Why not OpenAI/Cohere embeddings**: Voyage free tier is more generous and quality is better
- Requires `VOYAGE_API_KEY` in `.env` (free at `voyageai.com`)

### Vector DB: Pinecone (serverless free tier)
- **Free tier**: 2 GB storage, 1 index — enough for full Italian corpus
- Serverless: no always-on pod, billed per query (well within free tier)
- Pure API — **zero disk on VPS**
- One namespace per source: `scriptures`, `conference`, `handbook`, `liahona`
- Index name: `lds-rag`, similarity metric: `cosine` (set at creation time, cannot be changed without recreating the index)
- **Why not ChromaDB on disk**: adds 100–500 MB to VPS disk, loads into RAM at startup
- **Why not Supabase pgvector**: requires schema changes to existing DB; Pinecone is purpose-built
- Requires `PINECONE_API_KEY` in `.env` (free at `pinecone.io`)

### LLM: Claude claude-haiku-4-5 (Anthropic API)
- Used only for answer generation — only external cost in the stack
- Haiku is fast and cheap; upgrade to Sonnet for better quality if needed
- System prompt instructs to cite sources and stay grounded in retrieved context
- Requires `ANTHROPIC_API_KEY` in `.env`

## Module structure

```
rag/
├── __init__.py
├── schemas.py          # Pydantic models: RAGQuery, RAGResult, SearchResult, SourceChunk
├── embedder.py         # Voyage AI API wrapper — embed(texts) → list[vector]
├── vector_store.py     # Pinecone wrapper — upsert_chunks(), query()
├── retriever.py        # search(query, namespace, lang, top_k) → list[SourceChunk]
├── generator.py        # Claude API call: context + query → RAGResult
└── pipeline.py         # ask(query, lang, sources) orchestrating all above

api/routes/
└── rag.py              # FastAPI router, registered in app.py

scripts/
├── ingest_scriptures.py
├── ingest_conference.py
├── ingest_handbook.py
└── ingest_liahona.py   # optional, low priority

static/
└── rag.html            # Chat/search UI (vanilla JS, matches existing style)
```

No `data/` folder needed — nothing stored on disk.

## Chunking strategy

- Chunk size: ~400 tokens with 50-token overlap
- Metadata stored per chunk (in Pinecone): `source`, `book`, `chapter`, `verse` (scriptures),
  `speaker`, `title`, `date`, `url` (talks), `section` (handbook), `language`
- Namespace per source allows filtered retrieval without metadata overhead

## RAG answer format

Every answer includes:
- Answer text (in the user's query language)
- List of source citations: title, author/book, URL if available

## Environment variables needed

```
VOYAGE_API_KEY=...           # voyageai.com — free
PINECONE_API_KEY=...         # pinecone.io — free
ANTHROPIC_API_KEY=sk-ant-... # anthropic.com — pay per token
```

No model files, no large data directories. The VPS footprint of this module is just Python code.

## Latency profile

Each query makes 3 serial API calls:
1. Voyage embed: ~100–200ms
2. Pinecone query: ~50–150ms
3. Claude generate: ~500ms–2s (depends on answer length)

Total: ~1–2.5s per query. Acceptable for a Q&A tool.
Ingestion (one-time, run locally): batched Voyage embeds + Pinecone upserts, no VPS involvement.

## Ingestion: run locally, not on VPS

Ingestion scripts embed thousands of chunks and upsert to Pinecone.
This is CPU-heavy and should **not run on the VPS**.
Run on a dev machine, then it's done — Pinecone stores the results permanently.

```bash
# Run on dev machine, not on server
python scripts/ingest_scriptures.py --lang ita
python scripts/ingest_conference.py --lang ita --from-year 2015
python scripts/ingest_handbook.py --lang ita
```

Ingestion scripts should support a `--dry-run` flag that scrapes, chunks, and reports stats (chunk counts, estimated token usage) without calling the embedding API or upserting to Pinecone. This is useful for cost control during development.

## Auth & rate limiting

All `/rag/*` routes require JWT authentication, reusing the existing auth middleware. This protects Anthropic API costs from unauthorized use. Rate limiting on `/rag/query` and `/rag/generate` should be added in Phase 3 before endpoints go live.

## Cost optimizations

- **Response caching**: Repeated identical queries can be cached using an LRU cache keyed on query hash. This cuts both latency and Anthropic API cost for common questions.
- **Anthropic prompt caching**: The system prompt (which includes RAG instructions and formatting rules) can use Anthropic's prompt caching feature for up to 90% cost reduction on the cached prefix, since it stays constant across requests.

## Dependency risks

- **Pinecone and Voyage AI free tiers could change.** Keep ingestion scripts idempotent so you can re-ingest to a different provider if needed.
- **Voyage fallback**: OpenAI `text-embedding-3-small` at $0.02/1M tokens. Swap in `embedder.py` — same interface, different API call.
- **Pinecone fallback**: Upgrade to a paid plan, or migrate to an alternative provider. Export vectors first (Pinecone supports fetch-by-ID in bulk).
