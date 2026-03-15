"""Text chunking utilities for the RAG ingestion pipeline."""

import re


def chunk_text(
    text: str,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
    chars_per_token: float = 4.0,
) -> list[str]:
    """Split text into overlapping chunks of roughly max_tokens size.

    Uses a simple character-based estimate (chars_per_token) since we don't
    need exact tokenization for chunking — the embedding model handles that.

    Args:
        text: The text to chunk.
        max_tokens: Target maximum tokens per chunk.
        overlap_tokens: Token overlap between consecutive chunks.
        chars_per_token: Approximate characters per token.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    max_chars = int(max_tokens * chars_per_token)
    overlap_chars = int(overlap_tokens * chars_per_token)

    # Split into sentences for cleaner chunk boundaries
    sentences = _split_sentences(text)

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_len + sentence_len > max_chars and current_chunk:
            # Emit current chunk
            chunks.append(" ".join(current_chunk))

            # Keep overlap: walk backwards until we have ~overlap_chars
            overlap_chunk: list[str] = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) > overlap_chars:
                    break
                overlap_chunk.insert(0, s)
                overlap_len += len(s)

            current_chunk = overlap_chunk
            current_len = overlap_len

        current_chunk.append(sentence)
        current_len += sentence_len

    # Emit final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping them non-empty."""
    # Split on sentence-ending punctuation followed by whitespace
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_verses(
    verses: list[dict],
    group_size: int = 4,
    max_tokens: int = 400,
    chars_per_token: float = 4.0,
) -> list[dict]:
    """Group scripture verses into chunks suitable for embedding.

    Each verse dict should have at least: {"verse": int, "text": str}.
    Returns list of dicts with combined text and verse range.

    Args:
        verses: List of verse dicts with "verse" and "text" keys.
        group_size: Target number of verses per group.
        max_tokens: Maximum tokens per chunk.
        chars_per_token: Approximate characters per token.

    Returns:
        List of dicts with "text", "verse_start", "verse_end" keys.
    """
    if not verses:
        return []

    max_chars = int(max_tokens * chars_per_token)
    chunks: list[dict] = []
    current_texts: list[str] = []
    start_verse = verses[0].get("verse", 1)
    current_len = 0

    for v in verses:
        verse_text = v.get("text", "").strip()
        verse_num = v.get("verse", 0)
        verse_len = len(verse_text)

        if (
            len(current_texts) >= group_size or current_len + verse_len > max_chars
        ) and current_texts:
            chunks.append(
                {
                    "text": " ".join(current_texts),
                    "verse_start": start_verse,
                    "verse_end": prev_verse,
                }
            )
            current_texts = []
            current_len = 0
            start_verse = verse_num

        current_texts.append(verse_text)
        current_len += verse_len
        prev_verse = verse_num

    if current_texts:
        chunks.append(
            {
                "text": " ".join(current_texts),
                "verse_start": start_verse,
                "verse_end": prev_verse,
            }
        )

    return chunks
