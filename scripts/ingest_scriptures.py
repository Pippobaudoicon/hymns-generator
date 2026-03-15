#!/usr/bin/env python3
"""Ingest scriptures into the RAG vector store.

For English: downloads structured JSON from bcbooks/scriptures-json (GitHub).
For Italian: scrapes from churchofjesuschrist.org/study/scriptures.

Usage:
    python scripts/ingest_scriptures.py --lang ita
    python scripts/ingest_scriptures.py --lang eng
    python scripts/ingest_scriptures.py --lang ita --dry-run
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import chunk_text, chunk_verses
from rag.embedder import Embedder
from rag.schemas import SourceType
from rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# bcbooks JSON (English only — has verse-level structure)
ENG_JSON_URLS = {
    "book-of-mormon": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/book-of-mormon.json",
    "doctrine-and-covenants": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/doctrine-and-covenants.json",
    "pearl-of-great-price": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/pearl-of-great-price.json",
    "old-testament": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/old-testament.json",
    "new-testament": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/new-testament.json",
}

# Church website scripture volumes and their book slugs
CHURCH_BASE = "https://www.churchofjesuschrist.org"
HEADERS = {"User-Agent": "LDS-RAG-Ingestion/1.0"}

# Volume → list of (book_slug, display_name, chapter_count)
VOLUMES = {
    "bofm": [
        ("1-ne", "1 Nefi", 22), ("2-ne", "2 Nefi", 33), ("jacob", "Giacobbe", 7),
        ("enos", "Enos", 1), ("jarom", "Jarom", 1), ("omni", "Omni", 1),
        ("w-of-m", "Parole di Mormon", 1), ("mosiah", "Mosia", 29),
        ("alma", "Alma", 63), ("hel", "Helaman", 16), ("3-ne", "3 Nefi", 30),
        ("4-ne", "4 Nefi", 1), ("morm", "Mormon", 9), ("ether", "Ether", 15),
        ("moro", "Moroni", 10),
    ],
    "dc-testament": [
        ("dc", "DeA", 138),
    ],
    "pgp": [
        ("moses", "Mosè", 8), ("abr", "Abrahamo", 5),
        ("js-m", "Joseph Smith—Matteo", 1), ("js-h", "Joseph Smith—Storia", 1),
        ("a-of-f", "Articoli di Fede", 1),
    ],
    # Old/New Testament are very large; include key books only for manageable size
    "ot": [
        ("gen", "Genesi", 50), ("ex", "Esodo", 40), ("deut", "Deuteronomio", 34),
        ("josh", "Giosuè", 24), ("judg", "Giudici", 21),
        ("1-sam", "1 Samuele", 31), ("2-sam", "2 Samuele", 24),
        ("1-kgs", "1 Re", 22), ("2-kgs", "2 Re", 25),
        ("ps", "Salmi", 150), ("prov", "Proverbi", 31),
        ("eccl", "Ecclesiaste", 12), ("isa", "Isaia", 66),
        ("jer", "Geremia", 52), ("ezek", "Ezechiele", 48),
        ("dan", "Daniele", 12), ("amos", "Amos", 9), ("micah", "Michea", 7),
        ("mal", "Malachia", 4),
    ],
    "nt": [
        ("matt", "Matteo", 28), ("mark", "Marco", 16), ("luke", "Luca", 24),
        ("john", "Giovanni", 21), ("acts", "Atti", 28), ("rom", "Romani", 16),
        ("1-cor", "1 Corinzi", 16), ("2-cor", "2 Corinzi", 13),
        ("gal", "Galati", 6), ("eph", "Efesini", 6), ("philip", "Filippesi", 4),
        ("col", "Colossesi", 4), ("1-thes", "1 Tessalonicesi", 5),
        ("2-thes", "2 Tessalonicesi", 3), ("1-tim", "1 Timoteo", 6),
        ("2-tim", "2 Timoteo", 4), ("titus", "Tito", 3),
        ("heb", "Ebrei", 13), ("james", "Giacomo", 5),
        ("1-pet", "1 Pietro", 5), ("2-pet", "2 Pietro", 3),
        ("1-jn", "1 Giovanni", 5), ("rev", "Apocalisse", 22),
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# English: download JSON from bcbooks
# ──────────────────────────────────────────────────────────────────────────────


def ingest_english_json() -> list[dict]:
    """Download English scriptures from bcbooks/scriptures-json and chunk."""
    all_chunks = []

    for volume_slug, url in ENG_JSON_URLS.items():
        logger.info(f"Downloading {volume_slug}...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        books = data.get("books", [])
        for book in books:
            book_name = book.get("book", book.get("full_title", volume_slug))
            chapters = book.get("chapters", [])

            for chapter in chapters:
                chapter_num = chapter.get("chapter", 0)
                verses = chapter.get("verses", [])
                if not verses:
                    continue

                verse_chunks = chunk_verses(verses, group_size=4, max_tokens=400)

                for vc in verse_chunks:
                    verse_range = f"{vc['verse_start']}-{vc['verse_end']}"
                    chunk_id = f"scriptures-eng-{book_name}-{chapter_num}-{verse_range}"
                    chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id.replace(" ", "_").lower())

                    all_chunks.append({
                        "id": chunk_id,
                        "text": vc["text"],
                        "metadata": {
                            "text": vc["text"],
                            "source": SourceType.SCRIPTURES.value,
                            "book": book_name,
                            "chapter": chapter_num,
                            "verse": verse_range,
                            "language": "eng",
                        },
                    })

    return all_chunks


# ──────────────────────────────────────────────────────────────────────────────
# Italian (and other languages): scrape from churchofjesuschrist.org
# ──────────────────────────────────────────────────────────────────────────────


def scrape_chapter(volume_slug: str, book_slug: str, chapter: int, lang: str) -> list[dict]:
    """Scrape a single chapter and extract verses."""
    url = f"{CHURCH_BASE}/study/scriptures/{volume_slug}/{book_slug}/{chapter}?lang={lang}"

    try:
        resp = requests.get(url, timeout=30, headers=HEADERS)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    verses = []
    # The Church site marks verses with <p class="verse" id="p...">
    # or <span class="verse-number"> followed by text
    verse_elements = soup.select("[class*='verse']")

    if verse_elements:
        for el in verse_elements:
            # Try to extract verse number
            num_el = el.select_one("[class*='verse-number']")
            if num_el:
                try:
                    verse_num = int(re.search(r"\d+", num_el.get_text()).group())
                except (AttributeError, ValueError):
                    verse_num = len(verses) + 1
                text = el.get_text(separator=" ", strip=True)
                # Remove the verse number from the beginning
                text = re.sub(r"^\d+\s*", "", text)
            else:
                verse_num = len(verses) + 1
                text = el.get_text(separator=" ", strip=True)

            if text and len(text) > 5:
                verses.append({"verse": verse_num, "text": text})
    else:
        # Fallback: get the whole body and chunk as plain text
        body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
        if body:
            for el in body.select("footer, nav, .footnote, header"):
                el.decompose()
            text = body.get_text(separator=" ", strip=True)
            if len(text) > 50:
                verses.append({"verse": 1, "text": text})

    return verses


def ingest_scraped(lang: str) -> list[dict]:
    """Scrape scriptures from churchofjesuschrist.org and chunk."""
    all_chunks = []

    for volume_slug, books in VOLUMES.items():
        for book_slug, book_name, num_chapters in books:
            logger.info(f"Scraping {book_name} ({num_chapters} chapters)...")

            for ch in range(1, num_chapters + 1):
                time.sleep(0.5)  # Rate limiting
                verses = scrape_chapter(volume_slug, book_slug, ch, lang)

                if not verses:
                    continue

                if len(verses) == 1 and verses[0]["verse"] == 1:
                    # Fallback: whole chapter as plain text, use text chunker
                    text_chunks = chunk_text(verses[0]["text"], max_tokens=400, overlap_tokens=50)
                    for i, ct in enumerate(text_chunks):
                        chunk_id = f"scriptures-{lang}-{book_name}-{ch}-chunk{i}"
                        chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id.replace(" ", "_").lower())
                        all_chunks.append({
                            "id": chunk_id,
                            "text": ct,
                            "metadata": {
                                "text": ct,
                                "source": SourceType.SCRIPTURES.value,
                                "book": book_name,
                                "chapter": ch,
                                "verse": f"chunk-{i}",
                                "language": lang,
                            },
                        })
                else:
                    # Verse-level: group verses
                    verse_chunks = chunk_verses(verses, group_size=4, max_tokens=400)
                    for vc in verse_chunks:
                        verse_range = f"{vc['verse_start']}-{vc['verse_end']}"
                        chunk_id = f"scriptures-{lang}-{book_name}-{ch}-{verse_range}"
                        chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id.replace(" ", "_").lower())
                        all_chunks.append({
                            "id": chunk_id,
                            "text": vc["text"],
                            "metadata": {
                                "text": vc["text"],
                                "source": SourceType.SCRIPTURES.value,
                                "book": book_name,
                                "chapter": ch,
                                "verse": verse_range,
                                "language": lang,
                            },
                        })

    return all_chunks


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Ingest scriptures into RAG vector store")
    parser.add_argument("--lang", choices=["ita", "eng"], default="ita", help="Language")
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    args = parser.parse_args()

    # Collect chunks
    if args.lang == "eng":
        logger.info("Using bcbooks/scriptures-json for English...")
        chunks = ingest_english_json()
    else:
        logger.info(f"Scraping scriptures from churchofjesuschrist.org ({args.lang})...")
        chunks = ingest_scraped(args.lang)

    logger.info(f"Extracted {len(chunks)} chunks")

    if args.dry_run:
        total_chars = sum(len(c["text"]) for c in chunks)
        est_tokens = total_chars / 4
        print(f"\n--- Dry Run Report ---")
        print(f"Language: {args.lang}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Estimated tokens: {est_tokens:,.0f}")
        print(f"Estimated Pinecone size: ~{len(chunks) * 4:.0f} KB")
        if chunks:
            print(f"\nSample chunk (first):")
            print(f"  ID: {chunks[0]['id']}")
            print(f"  Text: {chunks[0]['text'][:200]}...")
        return

    # Embed
    embedder = Embedder()
    logger.info("Embedding chunks...")

    batch_size = 128
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch_texts = [c["text"] for c in chunks[i : i + batch_size]]
        batch_embs = embedder.embed_documents(batch_texts)
        all_embeddings.extend(batch_embs)
        logger.info(f"  Embedded {min(i + batch_size, len(chunks))}/{len(chunks)}")

    # Upsert
    store = VectorStore()
    ids = [c["id"] for c in chunks]
    metadata = [c["metadata"] for c in chunks]

    logger.info("Upserting to Pinecone...")
    total = store.upsert_chunks(
        ids=ids,
        embeddings=all_embeddings,
        metadata=metadata,
        namespace=SourceType.SCRIPTURES.value,
    )
    logger.info(f"Done! Upserted {total} vectors to namespace '{SourceType.SCRIPTURES.value}'")


if __name__ == "__main__":
    main()
