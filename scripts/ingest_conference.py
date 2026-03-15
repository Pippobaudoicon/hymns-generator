#!/usr/bin/env python3
"""Ingest General Conference talks into the RAG vector store.

Scrapes talks from churchofjesuschrist.org, chunks them, embeds via
Voyage AI, and upserts into Pinecone.

Usage:
    python scripts/ingest_conference.py --lang ita --from-year 2015
    python scripts/ingest_conference.py --lang ita --from-year 2015 --dry-run
"""

import argparse
import logging
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import chunk_text
from rag.embedder import Embedder
from rag.schemas import SourceType
from rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.churchofjesuschrist.org"
SESSIONS = ["04", "10"]  # April and October


def get_session_talks(year: int, month: str, lang: str) -> list[dict]:
    """Fetch the list of talks for a conference session."""
    url = f"{BASE_URL}/study/general-conference/{year}/{month}?lang={lang}"
    logger.info(f"Fetching session index: {url}")

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "LDS-RAG-Ingestion/1.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    talks = []

    # Find talk links in the session page
    for link in soup.select("a[href*='/study/general-conference/']"):
        href = link.get("href", "")
        title = link.get_text(strip=True)

        # Filter to actual talk URLs (not session index pages)
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
        resp = requests.get(url, timeout=30, headers={"User-Agent": "LDS-RAG-Ingestion/1.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch talk {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract talk body text
    body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
    if not body:
        logger.warning(f"No body found for {url}")
        return None

    # Remove footnotes, nav elements
    for el in body.select("footer, nav, .footnote, .kicker"):
        el.decompose()

    text = body.get_text(separator=" ", strip=True)
    if len(text) < 100:
        logger.warning(f"Talk text too short ({len(text)} chars): {url}")
        return None

    # Try to extract speaker from the page
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


def main():
    parser = argparse.ArgumentParser(description="Ingest conference talks into RAG vector store")
    parser.add_argument("--lang", choices=["ita", "eng"], default="ita")
    parser.add_argument("--from-year", type=int, default=2015)
    parser.add_argument("--to-year", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    args = parser.parse_args()

    all_chunks = []
    current_year = args.to_year

    for year in range(args.from_year, current_year + 1):
        for month in SESSIONS:
            talks = get_session_talks(year, month, args.lang)
            logger.info(f"  Found {len(talks)} talks for {year}/{month}")

            for talk in talks:
                time.sleep(1)  # Rate limiting: 1 req/sec
                talk_data = scrape_talk(talk, args.lang)
                if not talk_data:
                    continue

                text_chunks = chunk_text(talk_data["text"], max_tokens=400, overlap_tokens=50)

                for i, chunk_text_str in enumerate(text_chunks):
                    chunk_id = (
                        f"conference-{args.lang}-{year}-{month}-"
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
                                "language": args.lang,
                            },
                        }
                    )

    logger.info(f"Total chunks: {len(all_chunks)}")

    if args.dry_run:
        total_chars = sum(len(c["text"]) for c in all_chunks)
        est_tokens = total_chars / 4
        print(f"\n--- Dry Run Report ---")
        print(f"Language: {args.lang}")
        print(f"Years: {args.from_year}-{current_year}")
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

    # Embed
    embedder = Embedder()
    logger.info("Embedding chunks...")

    batch_size = 128
    all_embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch_texts = [c["text"] for c in all_chunks[i : i + batch_size]]
        batch_embs = embedder.embed_documents(batch_texts)
        all_embeddings.extend(batch_embs)
        logger.info(f"  Embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

    # Upsert
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
