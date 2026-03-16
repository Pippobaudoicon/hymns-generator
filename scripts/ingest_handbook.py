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
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.chunker import chunk_text
from rag.embedder import Embedder
from rag.schemas import SourceType
from rag.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.churchofjesuschrist.org"
HANDBOOK_PATH = "/study/manual/general-handbook"
HEADERS = {"User-Agent": "LDS-RAG-Ingestion/1.0"}


def _build_session() -> requests.Session:
    """Build a requests Session with transport-level retry + backoff."""
    session = requests.Session()
    session.headers.update(HEADERS)
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


def discover_sections(session: requests.Session, lang: str) -> list[dict]:
    """Scrape the handbook TOC page to discover section slugs and titles."""
    url = f"{BASE_URL}{HANDBOOK_PATH}?lang={lang}"
    logger.info(f"Fetching handbook TOC: {url}")

    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")

    sections = []
    seen = set()
    prefix = f"{HANDBOOK_PATH}/"

    for link in soup.select(f"a[href*='{HANDBOOK_PATH}/']"):
        href = link.get("href", "")
        title = link.get_text(strip=True)
        # Strip query params and fragment
        path = href.split("?")[0].split("#")[0]

        if not path.startswith(prefix) or not title:
            continue

        slug = path[len(prefix):]
        # Skip empty slugs or nested paths (sub-sections within a page)
        if not slug or "/" in slug:
            continue

        if slug not in seen:
            seen.add(slug)
            sections.append({"slug": slug, "title": title})

    logger.info(f"Discovered {len(sections)} handbook sections")
    return sections


def scrape_section(session: requests.Session, slug: str, lang: str) -> dict | None:
    """Scrape a single handbook section."""
    url = f"{BASE_URL}{HANDBOOK_PATH}/{slug}?lang={lang}"
    logger.info(f"Fetching section {slug}: {url}")

    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch section {slug}: {e}")
        return None

    soup = BeautifulSoup(resp.content, "html.parser")

    # Extract title
    title_el = soup.select_one("h1") or soup.select_one("title")
    title = title_el.get_text(strip=True) if title_el else slug

    # Extract body text
    body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
    if not body:
        logger.warning(f"No body found for section {slug}")
        return None

    # Remove nav, footnotes
    for el in body.select("footer, nav, .footnote, header"):
        el.decompose()

    text = body.get_text(separator=" ", strip=True)
    if len(text) < 50:
        logger.warning(f"Section {slug} text too short ({len(text)} chars)")
        return None

    return {
        "slug": slug,
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
    session = _build_session()
    sections = discover_sections(session, args.lang)

    if not sections:
        logger.error("No sections discovered from TOC page — aborting")
        sys.exit(1)

    for section in sections:
        time.sleep(1)  # Rate limiting
        section_data = scrape_section(session, section["slug"], args.lang)
        if not section_data:
            continue

        text_chunks = chunk_text(section_data["text"], max_tokens=400, overlap_tokens=50)

        for i, chunk_text_str in enumerate(text_chunks):
            chunk_id = (
                f"handbook-{args.lang}-{section['slug']}-{i}"
            )
            chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id)

            all_chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text_str,
                    "metadata": {
                        "text": chunk_text_str,
                        "source": SourceType.HANDBOOK.value,
                        "section": section["slug"],
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
        print(f"Sections discovered: {len(sections)}")
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
