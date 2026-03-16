#!/usr/bin/env python3
"""Ingest General Conference talks into the RAG vector store.

Scrapes talks from churchofjesuschrist.org, saves them as JSON files
(one per session), then chunks, embeds, and upserts into Pinecone.

Conference talks don't change after publication, so JSON is saved locally
and reused on subsequent runs — just like scriptures.

Saved to: data/conference-json/<lang>/<year>-<month>.json

Usage:
    python scripts/ingest_conference.py --lang ita --from-year 2015
    python scripts/ingest_conference.py --lang ita --from-year 2015 --dry-run
    python scripts/ingest_conference.py --lang ita --scrape-only
    python scripts/ingest_conference.py --lang ita --force-scrape
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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import chunk_text
from rag.embedder import Embedder
from rag.schemas import SourceType
from rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths & constants
# ──────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
JSON_DIR = PROJECT_ROOT / "data" / "conference-json"
BASE_URL = "https://www.churchofjesuschrist.org"
SESSIONS = ["04", "10"]  # April and October


# ──────────────────────────────────────────────────────────────────────────────
# HTTP session with retry
# ──────────────────────────────────────────────────────────────────────────────

def _build_session() -> requests.Session:
    """Build a requests Session with transport-level retry + backoff."""
    session = requests.Session()
    session.headers.update({"User-Agent": "LDS-RAG-Ingestion/1.0"})
    retry = Retry(
        total=4,
        backoff_factor=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _build_session()


# ──────────────────────────────────────────────────────────────────────────────
# Scraping
# ──────────────────────────────────────────────────────────────────────────────


def get_session_talks(year: int, month: str, lang: str) -> list[dict]:
    """Fetch the list of talks for a conference session."""
    url = f"{BASE_URL}/study/general-conference/{year}/{month}?lang={lang}"
    logger.info(f"Fetching session index: {url}")

    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(resp.content, "html.parser")
    talks = []

    for link in soup.select("a[href*='/study/general-conference/']"):
        href = link.get("href", "")
        title = link.get_text(separator=", ", strip=True)

        if re.search(rf"/study/general-conference/{year}/{month}/\w", href) and title:
            talk_url = href.split("?")[0]
            if not talk_url.startswith("http"):
                talk_url = BASE_URL + talk_url

            talks.append({"title": title, "url": talk_url, "year": year, "month": month})

    # Deduplicate by URL
    seen = set()
    unique = []
    for t in talks:
        if t["url"] not in seen:
            seen.add(t["url"])
            unique.append(t)

    return unique


def scrape_talk(talk: dict, lang: str) -> dict | None:
    """Scrape the full text of a single talk."""
    url = f"{talk['url']}?lang={lang}"

    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch talk {url}: {e}")
        return None

    soup = BeautifulSoup(resp.content, "html.parser")

    body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
    if not body:
        logger.warning(f"No body found for {url}")
        return None

    for el in body.select("footer, nav, .footnote, .kicker"):
        el.decompose()

    text = body.get_text(separator=" ", strip=True)
    if len(text) < 100:
        logger.warning(f"Talk text too short ({len(text)} chars): {url}")
        return None

    speaker_el = soup.select_one(".author-name") or soup.select_one(".byline")
    speaker = speaker_el.get_text(strip=True) if speaker_el else ""

    return {
        "title": talk["title"],
        "speaker": speaker,
        "text": text,
        "url": talk["url"],
        "year": talk["year"],
        "month": talk["month"],
    }


def scrape_and_save_session(year: int, month: str, lang: str, out_dir: Path) -> Path | None:
    """Scrape all talks for one conference session and save as JSON."""
    out_path = out_dir / f"{year}-{month}.json"

    talks = get_session_talks(year, month, lang)
    logger.info(f"  Found {len(talks)} talks for {year}/{month}")

    if not talks:
        return None

    session_data = {
        "year": year,
        "month": month,
        "language": lang,
        "talks": [],
    }

    for talk in talks:
        time.sleep(1)  # Rate limiting: 1 req/sec
        talk_data = scrape_talk(talk, lang)
        if talk_data:
            session_data["talks"].append(talk_data)

    if not session_data["talks"]:
        logger.warning(f"  No talks scraped for {year}/{month}")
        return None

    out_path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"  Saved → {out_path} ({len(session_data['talks'])} talks)")
    return out_path


def scrape_sessions(lang: str, from_year: int, to_year: int, force: bool = False) -> list[Path]:
    """Scrape all conference sessions in the year range, saving each as JSON."""
    out_dir = JSON_DIR / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for year in range(from_year, to_year + 1):
        for month in SESSIONS:
            out_path = out_dir / f"{year}-{month}.json"
            if out_path.exists() and not force:
                logger.info(f"  {out_path.name} already exists, skipping (use --force-scrape to re-scrape)")
                paths.append(out_path)
                continue

            result = scrape_and_save_session(year, month, lang, out_dir)
            if result:
                paths.append(result)

    return paths


# ──────────────────────────────────────────────────────────────────────────────
# JSON → RAG chunks
# ──────────────────────────────────────────────────────────────────────────────


def json_to_chunks(json_paths: list[Path], lang: str) -> list[dict]:
    """Read conference JSON files and produce RAG chunks."""
    all_chunks = []

    for path in json_paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        year = data["year"]
        month = data["month"]

        for talk_data in data.get("talks", []):
            text_chunks = chunk_text(talk_data["text"], max_tokens=400, overlap_tokens=50)

            for i, chunk_text_str in enumerate(text_chunks):
                chunk_id = (
                    f"conference-{lang}-{year}-{month}-"
                    f"{talk_data['title'][:40]}-{i}".replace(" ", "_").lower()
                )
                chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id)

                all_chunks.append(
                    {
                        "id": chunk_id,
                        "text": chunk_text_str,
                        "metadata": {
                            "text": chunk_text_str,
                            "source": SourceType.CONFERENCE.value,
                            "speaker": talk_data["speaker"],
                            "title": talk_data["title"],
                            "date": f"{year}-{month}",
                            "url": talk_data["url"],
                            "language": lang,
                        },
                    }
                )

    return all_chunks


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Ingest conference talks into RAG vector store")
    parser.add_argument("--lang", choices=["ita", "eng"], default="ita")
    parser.add_argument("--from-year", type=int, default=2015)
    parser.add_argument("--to-year", type=int, default=2026)
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    parser.add_argument("--scrape-only", action="store_true", help="Only scrape and save JSON, no embedding")
    parser.add_argument("--force-scrape", action="store_true", help="Re-scrape even if JSON exists")
    args = parser.parse_args()

    # Step 1: Get JSON files (scrape or use cached)
    logger.info(f"Getting {args.lang} conference talks ({args.from_year}-{args.to_year})...")
    json_paths = scrape_sessions(args.lang, args.from_year, args.to_year, force=args.force_scrape)

    if args.scrape_only:
        print(f"\nJSON files saved to: {JSON_DIR / args.lang}/")
        for p in json_paths:
            size_kb = p.stat().st_size / 1024
            data = json.loads(p.read_text(encoding="utf-8"))
            num_talks = len(data.get("talks", []))
            print(f"  {p.name} ({size_kb:.0f} KB, {num_talks} talks)")
        return

    # Step 2: Convert JSON → chunks
    all_chunks = json_to_chunks(json_paths, args.lang)
    logger.info(f"Total chunks: {len(all_chunks)}")

    if args.dry_run:
        total_chars = sum(len(c["text"]) for c in all_chunks)
        est_tokens = total_chars / 4
        print(f"\n--- Dry Run Report ---")
        print(f"Language: {args.lang}")
        print(f"JSON dir: {JSON_DIR / args.lang}")
        print(f"Years: {args.from_year}-{args.to_year}")
        print(f"Total chunks: {len(all_chunks)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Estimated tokens: {est_tokens:,.0f}")
        if all_chunks:
            print(f"\nSample chunk:")
            print(f"  ID: {all_chunks[0]['id']}")
            print(f"  Speaker: {all_chunks[0]['metadata']['speaker']}")
            print(f"  Title: {all_chunks[0]['metadata']['title']}")
            print(f"  Text: {all_chunks[0]['text'][:200]}...")
        return

    # Step 3: Embed
    embedder = Embedder()
    logger.info("Embedding chunks...")

    batch_size = 128
    all_embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch_texts = [c["text"] for c in all_chunks[i : i + batch_size]]
        batch_embs = embedder.embed_documents(batch_texts)
        all_embeddings.extend(batch_embs)
        logger.info(f"  Embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

    # Step 4: Upsert to Pinecone
    store = VectorStore()
    ids = [c["id"] for c in all_chunks]
    metadata = [c["metadata"] for c in all_chunks]

    logger.info("Upserting to Pinecone...")
    total = store.upsert_chunks(
        ids=ids,
        embeddings=all_embeddings,
        metadata=metadata,
        namespace=SourceType.CONFERENCE.value,
    )
    logger.info(f"Done! Upserted {total} vectors to namespace '{SourceType.CONFERENCE.value}'")


if __name__ == "__main__":
    main()
