"""LLM answer generation using Claude API."""

import os

import anthropic

from .schemas import Language, RAGResult, SourceChunk

SYSTEM_PROMPT = """\
You are an assistant specializing in LDS (Latter-day Saint) content. \
You answer questions grounded in the provided source passages. \
Always cite your sources. If the provided context doesn't contain \
enough information to answer, say so honestly.

Rules:
- Answer in the same language as the user's question.
- Cite sources by title, author/book, and reference when available.
- Do not invent information beyond what is in the provided context.
- Be concise but thorough.
"""


def _format_context(chunks: list[SourceChunk]) -> str:
    """Format retrieved chunks as context for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header_parts = [f"[Source {i}]"]
        if chunk.title:
            header_parts.append(f"Title: {chunk.title}")
        if chunk.speaker:
            header_parts.append(f"Speaker: {chunk.speaker}")
        if chunk.book:
            ref = chunk.book
            if chunk.chapter:
                ref += f" {chunk.chapter}"
            if chunk.verse:
                ref += f":{chunk.verse}"
            header_parts.append(f"Reference: {ref}")
        if chunk.section:
            header_parts.append(f"Section: {chunk.section}")
        if chunk.date:
            header_parts.append(f"Date: {chunk.date}")

        header = " | ".join(header_parts)
        parts.append(f"{header}\n{chunk.text}")

    return "\n\n---\n\n".join(parts)


class Generator:
    """Generates answers using Claude with retrieved context."""

    MODEL = "claude-haiku-4-5-20241022"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._client = anthropic.Anthropic(api_key=self._api_key)

    def generate(
        self,
        query: str,
        chunks: list[SourceChunk],
        language: Language = Language.ITA,
    ) -> RAGResult:
        """Generate an answer using Claude with retrieved context.

        Args:
            query: The user's question.
            chunks: Retrieved source chunks for context.
            language: Response language.

        Returns:
            RAGResult with the generated answer and source citations.
        """
        context = _format_context(chunks)

        lang_instruction = (
            "Rispondi in italiano." if language == Language.ITA else "Answer in English."
        )

        user_message = (
            f"{lang_instruction}\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}"
        )

        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_message}],
        )

        answer = response.content[0].text

        return RAGResult(
            query=query,
            answer=answer,
            sources=chunks,
            language=language,
            model=self.MODEL,
        )
