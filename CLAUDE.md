# Project: Hymns Generator + LDS RAG Tool

## What this repo is

A FastAPI app serving two purposes:

1. **Italian Hymns API** — smart hymn selection for LDS wards in Italy. Existing, production. See `README.md`.
2. **LDS RAG Tool** — a new module being built. Q&A, search, and content generation grounded in LDS sources (scriptures, conference talks, Liahona, General Handbook). See `docs/lds-rag/` for full context.

## Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLAlchemy (SQLite dev / Postgres prod)
- **Auth**: JWT-based, role hierarchy (superadmin → area → stake → ward)
- **Process manager**: PM2 (`ecosystem.config.js`)
- **Deployment**: `lds.tommasolopiparo.com`

## Key commands

```bash
make install       # install deps
make run           # dev server
make test          # run tests
make lint          # lint + format check
python cli.py db init   # init DB
```

## Working on the LDS RAG module?

Read `docs/lds-rag/` in this order:
1. `overview.md` — goals and what it does
2. `architecture.md` — stack choices and design decisions
3. `data-sources.md` — sources, scraping strategy
4. `build-plan.md` — phased plan with status

## Conventions

- Routes go in `api/routes/`, registered in `app.py`
- Business logic goes in a dedicated module folder (e.g. `rag/`)
- Scripts go in `scripts/`
- Static pages go in `static/` (HTML + CSS + vanilla JS, matching existing style)
- Tests go in `tests/`
- Commit style: `feat:`, `fix:`, `chore:`, `docs:`
