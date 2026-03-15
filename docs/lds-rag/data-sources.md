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
Embed chunks (sentence-transformers, batched)
    ↓
Upsert into ChromaDB collection
```

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

## Storage estimates (rough)

| Source | Chunks (est.) | ChromaDB size (est.) |
|---|---|---|
| Scriptures (both langs) | ~60,000 | ~150 MB |
| Conference talks 2000+ (both langs) | ~100,000 | ~250 MB |
| Liahona 2010+ (both langs) | ~40,000 | ~100 MB |
| General Handbook (both langs) | ~10,000 | ~25 MB |
| **Total** | **~210,000** | **~525 MB** |

## Open question: disk budget

If server disk is limited, reduce scope:
- Conference talks from 2010+ instead of 2000+
- Liahona from 2015+ only
- English only as a first pass, add Italian later
