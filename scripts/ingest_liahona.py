#!/usr/bin/env python3
"""Ingest Liahona magazine articles into the RAG vector store.

Scrapes articles from churchofjesuschrist.org, chunks them, embeds via
Voyage AI, and upserts into Pinecone.

Note: This source is low priority and optional per the build plan.

Usage:
    python scripts/ingest_liahona.py --lang ita --from-year 2010
    python scripts/ingest_liahona.py --lang ita --from-year 2010 --dry-run
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
MONTHS = [f"{m:02d}" for m in range(1, 13)]


def get_issue_articles(year: int, month: str, lang: str) -> list[dict]:
    """Fetch article links from a Liahona issue."""
    url = f"{BASE_URL}/study/liahona/{year}/{month}?lang={lang}"
    logger.info(f"Fetching issue index: {url}")

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "LDS-RAG-Ingestion/1.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []

    for link in soup.select("a[href*='/study/liahona/']"):
        href = link.get("href", "")
        title = link.get_text(strip=True)

        if re.search(rf"/study/liahona/{year}/{month}/\w", href) and title:
            article_url = href.split("?")[0]
            if not article_url.startswith("http"):
                article_url = BASE_URL + article_url

            articles.append({
                "title": title,
                "url": article_url,
                "year": year,
                "month": month,
            })

    # Deduplicate
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    return unique


def scrape_article(article: dict, lang: str) -> dict | None:
    """Scrape the full text of a single article."""
    url = f"{article['url']}?lang={lang}"

    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "LDS-RAG-Ingestion/1.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch article {url}: {e}")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    body = soup.select_one("article") or soup.select_one(".body-block") or soup.select_one("main")
    if not body:
        return None

    for el in body.select("footer, nav, .footnote"):
        el.decompose()

    text = body.get_text(separator=" ", strip=True)
    if len(text) < 100:
        return None

    author_el = soup.select_one(".author-name") or soup.select_one(".byline")
    author = author_el.get_text(strip=True) if author_el else ""

    return {
        "title": article["title"],
        "author": author,
        "text": text,
        "url": article["url"],
        "year": article["year"],
        "month": article["month"],
    }


def main():
    parser = argparse.ArgumentParser(description="Ingest Liahona articles into RAG vector store")
    parser.add_argument("--lang", choices=["ita", "eng"], default="ita")
    parser.add_argument("--from-year", type=int, default=2010)
    parser.add_argument("--to-year", type=int, default=2025)
    parser.add_argument("--dry-run", action="store_true", help="Report stats without embedding/upserting")
    args = parser.parse_args()

    all_chunks = []

    for year in range(args.from_year, args.to_year + 1):
        for month in MONTHS:
            articles = get_issue_articles(year, month, args.lang)
            if not articles:
                continue

            logger.info(f"  Found {len(articles)} articles for {year}/{month}")

            for article in articles:
                time.sleep(1)  # Rate limiting
                article_data = scrape_article(article, args.lang)
                if not article_data:
                    continue

                text_chunks = chunk_text(article_data["text"], max_tokens=400, overlap_tokens=50)

                for i, chunk_text_str in enumerate(text_chunks):
                    chunk_id = (
                        f"liahona-{args.lang}-{year}-{month}-"
                        f"{article_data['title'][:30]}-{i}".replace(" ", "_").lower()
                    )
                    chunk_id = re.sub(r"[^a-z0-9_-]", "", chunk_id)

                    all_chunks.append(
                        {
                            "id": chunk_id,
                            "text": chunk_text_str,
                            "metadata": {
                                "text": chunk_text_str,
                                "source": SourceType.LIAHONA.value,
                                "title": article_data["title"],
                                "speaker": article_data["author"],
                                "date": f"{year}-{month}",
                                "url": article_data["url"],
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
        print(f"Years: {args.from_year}-{args.to_year}")
        print(f"Total chunks: {len(all_chunks)}")
        print(f"Total characters: {total_chars:,}")
        print(f"Estimated tokens: {est_tokens:,.0f}")
        if all_chunks:
            print(f"\nSample chunk:")
            print(f"  ID: {all_chunks[0]['id']}")
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
        namespace=SourceType.LIAHONA.value,
    )
    logger.info(f"Done! Upserted {total} vectors to namespace '{SourceType.LIAHONA.value}'")


if __name__ == "__main__":
    main()
