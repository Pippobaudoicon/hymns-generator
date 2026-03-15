#!/usr/bin/env python3
"""Ingest scriptures into the RAG vector store.

Downloads structured JSON from a public source, chunks by verse groups,
embeds via Voyage AI, and upserts into Pinecone.

Usage:
    python scripts/ingest_scriptures.py --lang ita
    python scripts/ingest_scriptures.py --lang ita --dry-run
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import chunk_verses
from rag.embedder import Embedder
from rag.schemas import SourceType
from rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Public scripture JSON sources
SCRIPTURE_URLS = {
    "ita": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/ita-scriptures.json",
    "eng": "https://raw.githubusercontent.com/bcbooks/scriptures-json/master/eng-scriptures.json",
}

# Standard volume keys in the JSON
VOLUMES = [
    "old-testament",
    "new-testament",
    "book-of-mormon",
    "doctrine-and-covenants",
    "pearl-of-great-price",
]


def download_scriptures(lang: str) -> dict:
    """Download scripture JSON for the given language."""
    url = SCRIPTURE_URLS.get(lang)
    if not url:
        raise ValueError(f"Unsupported language: {lang}")

    logger.info(f"Downloading scriptures ({lang}) from {url}")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


def extract_chunks(data: dict, lang: str) -> list[dict]:
    """Extract and chunk all scripture verses from the JSON structure."""
    all_chunks = []

    # The JSON structure varies by source; handle common formats
    volumes = data if isinstance(data, list) else data.get("volumes", data.get("books", [data]))

    for volume in volumes:
        volume_name = volume.get("title", volume.get("name", "Unknown"))

        books = volume.get("books", volume.get("chapters", []))
        if not books and "book" in volume:
            books = [volume]

        for book in books:
            book_name = book.get("title", book.get("name", volume_name))
            chapters = book.get("chapters", [])

            for chapter in chapters:
                chapter_num = chapter.get("chapter", chapter.get("number", 0))
                verses = chapter.get("verses", [])

                if not verses:
                    continue

                verse_chunks = chunk_verses(verses, group_size=4, max_tokens=400)

                for vc in verse_chunks:
                    verse_range = f"{vc['verse_start']}-{vc['verse_end']}"
                    chunk_id = f"scriptures-{lang}-{book_name}-{chapter_num}-{verse_range}".replace(
                        " ", "_"
                    ).lower()

                    all_chunks.append(
                        {
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
                        }
                    )

    return all_chunks


def main():
    parser = argparse.ArgumentParser(description="Ingest scriptures into RAG vector store")
    parser.add_argument("--lang", choices=["ita", "eng"], default="ita", help="Language")
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    args = parser.parse_args()

    # Download
    data = download_scriptures(args.lang)

    # Chunk
    chunks = extract_chunks(data, args.lang)
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
