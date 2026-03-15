# LDS RAG Tool — Data Sources & Ingestion

## Source 1: Scriptures

**Strategy**: Download structured JSON — no scraping needed.

- Source: `https://github.com/bcbooks/scriptures-json` or `scriptures.byu.edu`
- Format: Clean JSON with book/chapter/verse structure
- Volumes: Old Testament, New Testament, Book of Mormon, D&C, Pearl of Great Price
- Languages: English and Italian JSON available separately
- Script: `scripts/ingest_scriptures.py`

**Chunking**: By verse or small verse groups (3-5 verses), keeping book+chapter+verse as metadata.

---

## Source 2: General Conference

**Strategy**: Scrape `churchofjesuschrist.org/study/general-conference`

- URL pattern: `https://www.churchofjesuschrist.org/study/general-conference/{year}/{month}?lang=ita`
- Languages: `lang=ita` for Italian, `lang=eng` for English
- Years: Start from 2000 onward (earlier years have less digital content)
- Rate limiting: 1 request/second, respect `robots.txt`
- Script: `scripts/ingest_conference.py`

**Metadata per chunk**: speaker, talk title, session, year, month, URL, language

---

## Source 3: Liahona Magazine

**Strategy**: Scrape `churchofjesuschrist.org/study/liahona`

- URL pattern: `https://www.churchofjesuschrist.org/study/liahona/{year}/{month}?lang=ita`
- Languages: `lang=ita`, `lang=eng`
- Scope: Recent years (e.g. 2010+) — prioritize quality over volume
- Rate limiting: 1 request/second
- Script: `scripts/ingest_liahona.py`

**Metadata per chunk**: author, article title, issue (year/month), URL, language

---

## Source 4: General Handbook

**Strategy**: Scrape section by section from `churchofjesuschrist.org/study/manual/general-handbook`

- URL pattern: `https://www.churchofjesuschrist.org/study/manual/general-handbook/{section}?lang=ita`
- Sections: numbered 0 through ~38 (Introduction through appendices)
- Languages: `lang=ita`, `lang=eng`
- Rate limiting: 1 request/second
- Script: `scripts/ingest_handbook.py`

**Metadata per chunk**: section number, section title, subsection, URL, language

---

## Ingestion pipeline (all sources)

```
Download/Scrape raw text
    ↓
Clean & normalize (strip HTML, fix encoding)
    ↓
Split into chunks (~400 tokens, 50-token overlap)
    ↓
Add metadata to each chunk
    ↓
Embed chunks (Voyage AI API, batched)
    ↓
Upsert into Pinecone (namespace per source)
```

**Note on chunking**: The ~400-token target is the actual constraint. For scriptures, verse grouping (3-5 verses) is flexible — some verse groups may be shorter or longer depending on content. The overlap and token budget take priority over strict verse counts.

## Running ingestion

```bash
# Individual sources
python scripts/ingest_scriptures.py --lang ita
python scripts/ingest_scriptures.py --lang eng
python scripts/ingest_conference.py --lang ita --from-year 2000
python scripts/ingest_liahona.py --lang ita --from-year 2010
python scripts/ingest_handbook.py --lang ita

# Check what's been ingested
python cli.py rag stats
```

## Storage: not a VPS concern

Vector storage lives in **Pinecone** (free tier, 2 GB), not on the VPS.
Ingestion scripts run on a dev machine and push directly to Pinecone.
The VPS stores nothing related to RAG.

### Scope with Pinecone free tier (2 GB)

With Pinecone's free 2 GB, the full Italian + English corpus fits comfortably.
Start with Italian only for speed, add English later.

| Source | Scope | Chunks (est.) | Pinecone size (est.) |
|---|---|---|---|
| Scriptures | Italian only | ~30,000 | ~120 MB |
| Conference talks | Italian only, 2015+ | ~15,000 | ~60 MB |
| General Handbook | Italian only | ~5,000 | ~20 MB |
| Liahona | Skip initially | — | — |
| **Phase 1 total** | | **~50,000** | **~200 MB** |
| + English (Phase 2) | all above, English | ~50,000 | +~200 MB |

Plenty of headroom within the 2 GB free tier.

### Per-ingestion script default flags

```bash
# Run on dev machine
python scripts/ingest_scriptures.py --lang ita
python scripts/ingest_conference.py --lang ita --from-year 2015
python scripts/ingest_handbook.py --lang ita
# Liahona: skip initially
```
