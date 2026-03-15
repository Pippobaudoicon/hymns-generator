# LDS RAG Tool — Build Plan

## Status legend
- [ ] Not started
- [~] In progress
- [x] Done

---

## Phase 1: RAG core infrastructure

Goal: working RAG pipeline with no data yet (unit-testable).

- [ ] Add dependencies to `requirements.txt`: `chromadb`, `sentence-transformers`, `anthropic`
- [ ] `rag/__init__.py`
- [ ] `rag/schemas.py` — Pydantic models: `RAGQuery`, `RAGResult`, `SearchResult`, `SourceChunk`
- [ ] `rag/embedder.py` — load `paraphrase-multilingual-MiniLM-L12-v2`, expose `embed(texts)`
- [ ] `rag/vector_store.py` — ChromaDB wrapper: init collections, `add_chunks()`, `query()`
- [ ] `rag/retriever.py` — `search(query, collection, lang, top_k)` → list of `SourceChunk`
- [ ] `rag/generator.py` — Claude API call with retrieved context → `RAGResult`
- [ ] `rag/pipeline.py` — `ask(query, lang, sources)` orchestrating all above
- [ ] Add `ANTHROPIC_API_KEY` and `CHROMA_DB_PATH` to `.env.example`
- [ ] `tests/test_rag_pipeline.py` — unit tests with mock data

## Phase 2: Ingestion scripts

Goal: populate ChromaDB with real LDS content.

- [ ] `scripts/ingest_scriptures.py`
- [ ] `scripts/ingest_conference.py`
- [ ] `scripts/ingest_liahona.py`
- [ ] `scripts/ingest_handbook.py`
- [ ] Add `make rag-ingest` target to Makefile
- [ ] Add `python cli.py rag stats` CLI command
- [ ] Add `data/chromadb/` to `.gitignore`

## Phase 3: API routes

Goal: exposed HTTP endpoints.

- [ ] `api/routes/rag.py`:
  - `POST /rag/query` — full RAG Q&A
  - `GET /rag/search` — semantic search (params: `q`, `source`, `lang`, `top_k`)
  - `POST /rag/generate` — generate content (talk, lesson outline, etc.)
  - `GET /rag/sources` — list collections + chunk counts
- [ ] Register router in `app.py`
- [ ] `tests/test_rag_api.py`

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

- [ ] PM2 config update if needed (model loading at startup)
- [ ] Rate limiting on `/rag/*` routes (avoid API cost abuse)
- [ ] Auth: decide if RAG endpoints require login or are public
- [ ] Makefile targets: `make rag-ingest`, `make rag-stats`
- [ ] Update `README.md` with RAG section

---

## Decisions log

| Decision | Choice | Rationale |
|---|---|---|
| Vector DB | ChromaDB embedded | Zero infra, persists to disk, free |
| Embeddings | sentence-transformers multilingual | Local, free, Italian+English support |
| LLM | Claude claude-sonnet-4-6 | Best reasoning, citation quality |
| Project location | Module inside hymns-generator repo | Reuse auth, infra, deployment |
| Scraping scope | Italian + English, 2000+ for conference | Multilingual audience |

## Open questions (resolve before/during implementation)

1. **Anthropic API key** — does the user have one? Needed for Phase 1.
2. **Languages to ingest** — Italian + English both, or start with one?
3. **Disk budget** — server storage available? Affects scope of ingestion (see `data-sources.md`).
4. **Auth on RAG routes** — public access or require login?
5. **Conference year range** — 2000+ or more/less?
