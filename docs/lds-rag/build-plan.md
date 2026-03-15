# LDS RAG Tool — Build Plan

## Status legend
- [ ] Not started
- [~] In progress
- [x] Done

---

## Phase 1: RAG core infrastructure

Goal: working RAG pipeline with no data yet (unit-testable).

- [x] Add dependencies to `requirements.txt`: `pinecone`, `voyageai`, `anthropic`
- [x] `rag/__init__.py`
- [x] `rag/schemas.py` — Pydantic models: `RAGQuery`, `RAGResult`, `SearchResult`, `SourceChunk`
- [x] `rag/embedder.py` — Voyage AI API wrapper, expose `embed(texts)`
- [x] `rag/vector_store.py` — Pinecone wrapper: init index/namespaces, `upsert_chunks()`, `query()`
- [x] `rag/retriever.py` — `search(query, collection, lang, top_k)` → list of `SourceChunk`
- [x] `rag/generator.py` — Claude API call with retrieved context → `RAGResult`
- [x] `rag/pipeline.py` — `ask(query, lang, sources)` orchestrating all above
- [x] Add `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `PINECONE_API_KEY` to `.env.example`
- [x] `tests/test_rag_pipeline.py` — unit tests with mock data

## Phase 2: Ingestion scripts

Goal: populate Pinecone with real LDS content.

- [ ] `scripts/ingest_scriptures.py`
- [ ] `scripts/ingest_conference.py`
- [ ] `scripts/ingest_liahona.py`
- [ ] `scripts/ingest_handbook.py`
- [ ] Add `make rag-ingest` target to Makefile
- [ ] Add `python cli.py rag stats` CLI command
- [ ] Nothing to gitignore — no local data files

## Phase 3: API routes

Goal: exposed HTTP endpoints.

- [ ] `api/routes/rag.py`:
  - `POST /rag/query` — full RAG Q&A
  - `GET /rag/search` — semantic search (params: `q`, `source`, `lang`, `top_k`)
  - `POST /rag/generate` — generate content (talk, lesson outline, etc.)
  - `GET /rag/sources` — list collections + chunk counts
- [ ] Register router in `app.py`
- [ ] `tests/test_rag_api.py`
- [ ] Auth: require JWT login on all /rag/* routes (reuse existing auth middleware)
- [ ] Rate limiting on /rag/query and /rag/generate to protect Anthropic API costs

## Phase 4: Frontend

Goal: usable web interface.

- [ ] `static/rag.html` — chat/search UI
  - Chat mode: Q&A with source citations shown below answer
  - Search mode: list of matching passages with source metadata
  - Language toggle: ITA / ENG
  - Source filter: checkboxes for scriptures / conference / liahona / handbook
- [ ] Wire to API endpoints with fetch
- [ ] Link from existing `index.html` nav

## Phase 5: Integration & polish

- [ ] PM2 config update if needed (env vars, restart policy)
- [ ] Makefile target: `make rag-stats`
- [ ] Update `README.md` with RAG section

---

## Decisions log

| Decision | Choice | Rationale |
|---|---|---|
| Vector DB | Pinecone serverless free tier | 2 GB free, zero VPS disk usage |
| Embeddings | Voyage AI API (`voyage-multilingual-2`) | Free 200M tokens/month, zero VPS RAM |
| LLM | Claude claude-haiku-4-5 | Fast and cheap; upgrade to Sonnet for better quality if needed |
| Project location | Module inside hymns-generator repo | Reuse auth, infra, deployment |
| Scraping scope | Italian only, 2015+ for conference | VPS disk/RAM constraint |
| Liahona | Skip initially | Lowest priority; saves ~12–100 MB |
| Ingestion location | Run on dev machine, push to Pinecone | VPS never involved in ingestion |

## Constraints & approach

**The server is a small VPS.** All heavy work is outsourced to free external APIs:

- **Embeddings** → Voyage AI free tier (no model on VPS)
- **Vector storage** → Pinecone free tier (no disk usage on VPS)
- **LLM** → Anthropic API (already external)
- **Ingestion** → run on dev machine, push to Pinecone (VPS never involved)

The VPS runs only FastAPI + API calls. Its footprint for this module is ~0 MB disk, ~0 MB extra RAM.

## Open questions (resolve before/during implementation)

1. **API keys** — need three: `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `PINECONE_API_KEY`. All have free tiers.
2. **Auth on RAG routes** — **resolved: login required** (JWT, reuse existing auth middleware)
