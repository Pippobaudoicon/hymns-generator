#!/usr/bin/env python3
"""Ingest General Handbook into the RAG vector store.

Scrapes sections from churchofjesuschrist.org, chunks them, embeds via
Voyage AI, and upserts into Pinecone.

Usage:
    python scripts/ingest_handbook.py --lang ita
    python scripts/ingest_handbook.py --lang ita --dry-run
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

# Handbook section slugs (0 = introduction, 1-38 = numbered sections)
SECTION_SLUGS = [f"{i}" for i in range(0, 39)]


def scrape_section(section: str, lang: str) -> dict | None:
    """Scrape a single handbook section."""
    url = f"{BASE_URL}/study/manual/general-handbook/{section}?lang={lang}"
    logger.info(f"Fetching section {section}: {url}")

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "LDS-RAG-Ingestion/1.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch section {section}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract title
    title_el = soup.select_one("h1") or soup.select_one("title")
    title = title_el.get_text(strip=True) if title_el else f"Section {section}"

    # Extract body text
    body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
    if not body:
        logger.warning(f"No body found for section {section}")
        return None

    # Remove nav, footnotes
    for el in body.select("footer, nav, .footnote, header"):
        el.decompose()

    text = body.get_text(separator=" ", strip=True)
    if len(text) < 50:
        logger.warning(f"Section {section} text too short ({len(text)} chars)")
        return None

    return {
        "section": section,
        "title": title,
        "text": text,
        "url": url.split("?")[0],
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest General Handbook into RAG vector store")
    parser.add_argument("--lang", choices=["ita", "eng"], default="ita")
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    args = parser.parse_args()

    all_chunks = []

    for section_slug in SECTION_SLUGS:
        time.sleep(1)  # Rate limiting
        section_data = scrape_section(section_slug, args.lang)
        if not section_data:
            continue

        text_chunks = chunk_text(section_data["text"], max_tokens=400, overlap_tokens=50)

        for i, chunk_text_str in enumerate(text_chunks):
            chunk_id = (
                f"handbook-{args.lang}-s{section_slug}-{i}"
            )
            chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id)

            all_chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text_str,
                    "metadata": {
                        "text": chunk_text_str,
                        "source": SourceType.HANDBOOK.value,
                        "section": section_slug,
                        "title": section_data["title"],
                        "url": section_data["url"],
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
        print(f"Sections: {len(SECTION_SLUGS)}")
        print(f"Total chunks: {len(all_chunks)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Estimated tokens: {est_tokens:,.0f}")
        if all_chunks:
            print(f"\nSample chunk:")
            print(f"  ID: {all_chunks[0]['id']}")
            print(f"  Section: {all_chunks[0]['metadata']['section']}")
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
        namespace=SourceType.HANDBOOK.value,
    )
    logger.info(f"Done! Upserted {total} vectors to namespace '{SourceType.HANDBOOK.value}'")


if __name__ == "__main__":
    main()
