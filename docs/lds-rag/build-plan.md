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
| Scraping scope | Italian only, 2015+ for conference | VPS disk/RAM constraint |
| Liahona | Skip initially | Lowest priority; saves ~12–100 MB |
| Ingestion location | Run locally, upload ChromaDB to VPS | Avoid OOM during embedding on small VPS |

## Constraints

**The server is a small VPS with very limited disk and RAM.** This is not an open question —
it is a hard constraint that shapes all decisions:

- Ingest Italian only to start (cuts storage ~50%)
- Skip Liahona initially (lowest value/MB ratio)
- Conference talks from 2015+ only
- Target: ~135 MB total ChromaDB storage (see `data-sources.md`)
- Load sentence-transformers model lazily, not at app startup
- Do not load all ChromaDB collections at startup — open on demand

## Open questions (resolve before/during implementation)

1. **Anthropic API key** — does the user have one? Needed for Phase 1.
2. **Auth on RAG routes** — public access or require login?
3. **Ingestion machine** — run ingestion scripts locally then upload ChromaDB, or run on VPS?
   Running on VPS risks OOM during embedding; running locally is safer.
