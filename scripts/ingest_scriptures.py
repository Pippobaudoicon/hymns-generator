#!/usr/bin/env python3
"""Ingest scriptures into the RAG vector store.

Produces clean, structured JSON files (bcbooks-compatible format) per volume,
then chunks and embeds them for Pinecone.

English JSON is downloaded from bcbooks/scriptures-json.
Italian JSON is scraped from churchofjesuschrist.org and saved locally so
you only need to scrape once — reusable as a standalone dataset.

Saved to: data/scriptures-json/<lang>/<volume>.json

Usage:
    python scripts/ingest_scriptures.py --lang ita                        # all volumes
    python scripts/ingest_scriptures.py --lang ita --volumes ot nt        # only OT + NT
    python scripts/ingest_scriptures.py --lang ita --volumes bofm         # only Book of Mormon
    python scripts/ingest_scriptures.py --lang spa --scrape-only          # scrape Spanish, JSON only
    python scripts/ingest_scriptures.py --lang ita --dry-run              # report stats
    python scripts/ingest_scriptures.py --lang ita --force-scrape         # re-scrape even if cached
    python scripts/ingest_scriptures.py --lang eng                        # download from bcbooks

Volume keys: bofm, dc-testament, pgp, ot, nt
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
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import chunk_verses
from rag.embedder import Embedder
from rag.schemas import SourceType
from rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
JSON_DIR = PROJECT_ROOT / "data" / "scriptures-json"

# ──────────────────────────────────────────────────────────────────────────────
# English: download from bcbooks
# ──────────────────────────────────────────────────────────────────────────────

# Maps short key → (json filename, bcbooks download URL)
ENG_VOLUMES = {
    "bofm": ("book-of-mormon.json", "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/book-of-mormon.json"),
    "dc-testament": ("doctrine-and-covenants.json", "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/doctrine-and-covenants.json"),
    "pgp": ("pearl-of-great-price.json", "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/pearl-of-great-price.json"),
    "ot": ("old-testament.json", "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/old-testament.json"),
    "nt": ("new-testament.json", "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/new-testament.json"),
}

ALL_VOLUME_KEYS = list(ENG_VOLUMES.keys())  # bofm, dc-testament, pgp, ot, nt


def download_english(volumes: list[str], force: bool = False) -> list[Path]:
    """Download English JSON from bcbooks if not already cached."""
    out_dir = JSON_DIR / "eng"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for key in volumes:
        filename, url = ENG_VOLUMES[key]
        out_path = out_dir / filename
        if out_path.exists() and not force:
            logger.info(f"  {filename} already exists, skipping (use --force-scrape to re-download)")
            paths.append(out_path)
            continue

        logger.info(f"Downloading {filename}...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        out_path.write_text(json.dumps(resp.json(), ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"  Saved {out_path}")
        paths.append(out_path)

    return paths


# ──────────────────────────────────────────────────────────────────────────────
# Italian: scrape from churchofjesuschrist.org → save as bcbooks-format JSON
# ──────────────────────────────────────────────────────────────────────────────

CHURCH_BASE = "https://www.churchofjesuschrist.org"
HEADERS = {"User-Agent": "LDS-RAG-Ingestion/1.0"}


def _build_session() -> requests.Session:
    """Build a requests Session with transport-level retry + backoff.

    urllib3 retries handle DNS failures, connection resets, and timeouts
    at the socket layer — creating fresh connections on each retry instead
    of reusing a broken connection pool.
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=4,
        backoff_factor=3,          # 0s, 3s, 6s, 12s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _build_session()

# Volume slug on church site → (json filename, title, list of books)
# Each book: (url_slug, display_name, num_chapters)
VOLUME_DEFS = {
    "bofm": {
        "file": "book-of-mormon.json",
        "title": "Il Libro di Mormon",
        "books": [
            ("1-ne", "1 Nefi", 22), ("2-ne", "2 Nefi", 33), ("jacob", "Giacobbe", 7),
            ("enos", "Enos", 1), ("jarom", "Jarom", 1), ("omni", "Omni", 1),
            ("w-of-m", "Parole di Mormon", 1), ("mosiah", "Mosia", 29),
            ("alma", "Alma", 63), ("hel", "Helaman", 16), ("3-ne", "3 Nefi", 30),
            ("4-ne", "4 Nefi", 1), ("morm", "Mormon", 9), ("ether", "Ether", 15),
            ("moro", "Moroni", 10),
        ],
    },
    "dc-testament": {
        "file": "doctrine-and-covenants.json",
        "title": "Dottrina e Alleanze",
        "books": [
            ("dc", "Dottrina e Alleanze", 138),
        ],
    },
    "pgp": {
        "file": "pearl-of-great-price.json",
        "title": "Perla di Gran Prezzo",
        "books": [
            ("moses", "Mosè", 8), ("abr", "Abrahamo", 5),
            ("js-m", "Joseph Smith—Matteo", 1), ("js-h", "Joseph Smith—Storia", 1),
            ("a-of-f", "Articoli di Fede", 1),
        ],
    },
    "ot": {
        "file": "old-testament.json",
        "title": "Vecchio Testamento",
        "books": [
            ("gen", "Genesi", 50), ("ex", "Esodo", 40), ("lev", "Levitico", 27),
            ("num", "Numeri", 36), ("deut", "Deuteronomio", 34),
            ("josh", "Giosuè", 24), ("judg", "Giudici", 21),
            ("ruth", "Rut", 4), ("1-sam", "1 Samuele", 31), ("2-sam", "2 Samuele", 24),
            ("1-kgs", "1 Re", 22), ("2-kgs", "2 Re", 25),
            ("1-chr", "1 Cronache", 29), ("2-chr", "2 Cronache", 36),
            ("ezra", "Esdra", 10), ("neh", "Neemia", 13),
            ("esth", "Ester", 10), ("job", "Giobbe", 42),
            ("ps", "Salmi", 150), ("prov", "Proverbi", 31),
            ("eccl", "Ecclesiaste", 12), ("song", "Cantico dei Cantici", 8),
            ("isa", "Isaia", 66), ("jer", "Geremia", 52),
            ("lam", "Lamentazioni", 5), ("ezek", "Ezechiele", 48),
            ("dan", "Daniele", 12), ("hosea", "Osea", 14),
            ("joel", "Gioele", 3), ("amos", "Amos", 9),
            ("obad", "Abdia", 1), ("jonah", "Giona", 4),
            ("micah", "Michea", 7), ("nahum", "Naum", 3),
            ("hab", "Abacuc", 3), ("zeph", "Sofonia", 3),
            ("hag", "Aggeo", 2), ("zech", "Zaccaria", 14),
            ("mal", "Malachia", 4),
        ],
    },
    "nt": {
        "file": "new-testament.json",
        "title": "Nuovo Testamento",
        "books": [
            ("matt", "Matteo", 28), ("mark", "Marco", 16), ("luke", "Luca", 24),
            ("john", "Giovanni", 21), ("acts", "Atti", 28), ("rom", "Romani", 16),
            ("1-cor", "1 Corinzi", 16), ("2-cor", "2 Corinzi", 13),
            ("gal", "Galati", 6), ("eph", "Efesini", 6), ("philip", "Filippesi", 4),
            ("col", "Colossesi", 4), ("1-thes", "1 Tessalonicesi", 5),
            ("2-thes", "2 Tessalonicesi", 3), ("1-tim", "1 Timoteo", 6),
            ("2-tim", "2 Timoteo", 4), ("titus", "Tito", 3),
            ("philem", "Filemone", 1), ("heb", "Ebrei", 13),
            ("james", "Giacomo", 5), ("1-pet", "1 Pietro", 5),
            ("2-pet", "2 Pietro", 3), ("1-jn", "1 Giovanni", 5),
            ("2-jn", "2 Giovanni", 1), ("3-jn", "3 Giovanni", 1),
            ("jude", "Giuda", 1), ("rev", "Apocalisse", 22),
        ],
    },
}


def scrape_chapter_verses(volume_slug: str, book_slug: str, chapter: int, lang: str) -> list[dict]:
    """Scrape a single chapter and return a list of {verse, text, reference} dicts."""
    url = f"{CHURCH_BASE}/study/scriptures/{volume_slug}/{book_slug}/{chapter}?lang={lang}"

    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"  Failed {url} after retries: {e}")
        return []

    soup = BeautifulSoup(resp.content, "html.parser")
    verses = []

    # Try verse-marked elements first
    verse_elements = soup.select("[class*='verse']")
    if verse_elements:
        for el in verse_elements:
            num_el = el.select_one("[class*='verse-number']")
            if num_el:
                try:
                    verse_num = int(re.search(r"\d+", num_el.get_text()).group())
                except (AttributeError, ValueError):
                    verse_num = len(verses) + 1
                text = el.get_text(separator=" ", strip=True)
                text = re.sub(r"^\d+\s*", "", text)
            else:
                verse_num = len(verses) + 1
                text = el.get_text(separator=" ", strip=True)

            if text and len(text) > 5:
                verses.append({"verse": verse_num, "text": text})
    else:
        # Fallback: extract body paragraphs
        body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
        if body:
            for el in body.select("footer, nav, .footnote, header"):
                el.decompose()
            paragraphs = body.find_all("p")
            for i, p in enumerate(paragraphs, 1):
                text = p.get_text(separator=" ", strip=True)
                if text and len(text) > 10:
                    verses.append({"verse": i, "text": text})

    return verses


def scrape_and_save_volume(volume_slug: str, vol_def: dict, lang: str, out_dir: Path) -> Path:
    """Scrape one volume and save as a bcbooks-format JSON file."""
    out_path = out_dir / vol_def["file"]

    volume_data = {
        "title": vol_def["title"],
        "lds_slug": volume_slug,
        "language": lang,
        "books": [],
    }

    consecutive_failures = 0
    for book_slug, book_name, num_chapters in vol_def["books"]:
        logger.info(f"  {book_name} ({num_chapters} ch)...")
        book_data = {
            "book": book_name,
            "lds_slug": book_slug,
            "full_title": book_name,
            "chapters": [],
        }

        for ch in range(1, num_chapters + 1):
            # Back off harder when we see consecutive failures (likely network outage)
            if consecutive_failures >= 3:
                wait = min(consecutive_failures * 10, 120)
                logger.info(f"    {consecutive_failures} consecutive failures — waiting {wait}s for network recovery...")
                time.sleep(wait)
            else:
                time.sleep(0.5)  # Rate limiting: 2 req/sec

            verses = scrape_chapter_verses(volume_slug, book_slug, ch, lang)

            if not verses:
                consecutive_failures += 1
                logger.warning(f"    Chapter {ch}: no verses found")
                continue

            consecutive_failures = 0

            # Add reference field to each verse (bcbooks compat)
            for v in verses:
                v["reference"] = f"{book_name} {ch}:{v['verse']}"

            book_data["chapters"].append({
                "chapter": ch,
                "reference": f"{book_name} {ch}",
                "verses": verses,
            })

        volume_data["books"].append(book_data)

    out_path.write_text(json.dumps(volume_data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"  Saved → {out_path}")
    return out_path


def scrape_language(lang: str, volumes: list[str], force: bool = False) -> list[Path]:
    """Scrape selected volumes for *lang*, saving each as JSON. Skip if already exists."""
    out_dir = JSON_DIR / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for key in volumes:
        vol_def = VOLUME_DEFS[key]
        out_path = out_dir / vol_def["file"]
        if out_path.exists() and not force:
            logger.info(f"  {vol_def['file']} already exists, skipping (use --force-scrape to re-scrape)")
            paths.append(out_path)
            continue

        logger.info(f"Scraping {vol_def['title']} ({lang})...")
        paths.append(scrape_and_save_volume(key, vol_def, lang, out_dir))

    return paths


# ──────────────────────────────────────────────────────────────────────────────
# JSON → RAG chunks (shared for both languages)
# ──────────────────────────────────────────────────────────────────────────────


def json_to_chunks(json_paths: list[Path], lang: str) -> list[dict]:
    """Read bcbooks-format JSON files and produce RAG chunks."""
    all_chunks = []

    for path in json_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        books = data.get("books", [])

        for book in books:
            book_name = book.get("book", book.get("full_title", path.stem))

            for chapter in book.get("chapters", []):
                chapter_num = chapter.get("chapter", 0)
                verses = chapter.get("verses", [])
                if not verses:
                    continue

                verse_chunks = chunk_verses(verses, group_size=4, max_tokens=400)

                for vc in verse_chunks:
                    verse_range = f"{vc['verse_start']}-{vc['verse_end']}"
                    chunk_id = f"scriptures-{lang}-{book_name}-{chapter_num}-{verse_range}"
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
                            "language": lang,
                        },
                    })

    return all_chunks


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Ingest scriptures into RAG vector store")
    parser.add_argument("--lang", default="ita", help="Language code (e.g. ita, eng, spa, por, fra, deu)")
    parser.add_argument("--volumes", nargs="+", choices=ALL_VOLUME_KEYS, default=None,
                        help="Volumes to process (default: all). Choices: bofm, dc-testament, pgp, ot, nt")
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    parser.add_argument("--scrape-only", action="store_true", help="Only scrape and save JSON, no embedding")
    parser.add_argument("--force-scrape", action="store_true", help="Re-scrape/download even if JSON exists")
    args = parser.parse_args()

    volumes = args.volumes or ALL_VOLUME_KEYS

    # Step 1: Get JSON files (download or scrape)
    if args.lang == "eng":
        logger.info("Getting English JSON from bcbooks/scriptures-json...")
        json_paths = download_english(volumes, force=args.force_scrape)
    else:
        logger.info(f"Getting {args.lang} JSON (scraping from churchofjesuschrist.org)...")
        json_paths = scrape_language(args.lang, volumes, force=args.force_scrape)

    if args.scrape_only:
        print(f"\nJSON files saved to: {JSON_DIR / args.lang}/")
        for p in json_paths:
            size_kb = p.stat().st_size / 1024
            print(f"  {p.name} ({size_kb:.0f} KB)")
        print("\nThese files match the bcbooks/scriptures-json format.")
        print("You can publish them as a standalone scriptures dataset.")
        return

    # Step 2: Convert JSON → chunks
    chunks = json_to_chunks(json_paths, args.lang)
    logger.info(f"Extracted {len(chunks)} chunks from {len(json_paths)} volumes")

    if args.dry_run:
        total_chars = sum(len(c["text"]) for c in chunks)
        est_tokens = total_chars / 4
        print(f"\n--- Dry Run Report ---")
        print(f"Language: {args.lang}")
        print(f"JSON dir: {JSON_DIR / args.lang}")
        print(f"Total chunks: {len(chunks)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Estimated tokens: {est_tokens:,.0f}")
        print(f"Estimated Pinecone size: ~{len(chunks) * 4:.0f} KB")
        if chunks:
            print(f"\nSample chunk (first):")
            print(f"  ID: {chunks[0]['id']}")
            print(f"  Text: {chunks[0]['text'][:200]}...")
        return

    # Step 3: Embed
    embedder = Embedder()
    logger.info("Embedding chunks...")

    batch_size = 128
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch_texts = [c["text"] for c in chunks[i : i + batch_size]]
        batch_embs = embedder.embed_documents(batch_texts)
        all_embeddings.extend(batch_embs)
        logger.info(f"  Embedded {min(i + batch_size, len(chunks))}/{len(chunks)}")

    # Step 4: Upsert to Pinecone
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
