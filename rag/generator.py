"""LLM answer generation — supports Anthropic (Claude) and OpenAI (GPT)."""

import os

import anthropic
import openai

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


def _build_user_message(query: str, chunks: list[SourceChunk], language: Language) -> str:
    """Build the user message with context and language instruction."""
    context = _format_context(chunks)
    lang_instruction = (
        "Rispondi in italiano." if language == Language.ITA else "Answer in English."
    )
    return f"{lang_instruction}\n\nContext:\n{context}\n\nQuestion: {query}"


class AnthropicGenerator:
    """Generates answers using Claude (Anthropic API)."""

    DEFAULT_MODEL = "claude-haiku-4-5-20241022"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._model = model or self.DEFAULT_MODEL
        self._client = anthropic.Anthropic(api_key=self._api_key)

    def generate(
        self,
        query: str,
        chunks: list[SourceChunk],
        language: Language = Language.ITA,
    ) -> RAGResult:
        user_message = _build_user_message(query, chunks, language)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_message}],
        )

        return RAGResult(
            query=query,
            answer=response.content[0].text,
            sources=chunks,
            language=language,
            model=self._model,
        )


class OpenAIGenerator:
    """Generates answers using GPT (OpenAI API)."""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._model = model or self.DEFAULT_MODEL
        self._client = openai.OpenAI(api_key=self._api_key)

    def generate(
        self,
        query: str,
        chunks: list[SourceChunk],
        language: Language = Language.ITA,
    ) -> RAGResult:
        user_message = _build_user_message(query, chunks, language)

        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )

        return RAGResult(
            query=query,
            answer=response.choices[0].message.content,
            sources=chunks,
            language=language,
            model=self._model,
        )


# Factory — keeps backward compatibility
def Generator(
    api_key: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> AnthropicGenerator | OpenAIGenerator:
    """Create a generator for the configured LLM provider.

    Args:
        api_key: API key override. If None, reads from env.
        provider: "anthropic" or "openai". If None, reads LLM_PROVIDER env var.
        model: Model name override. If None, uses provider default.

    Returns:
        AnthropicGenerator or OpenAIGenerator instance.
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower()

    if provider == "openai":
        return OpenAIGenerator(api_key=api_key, model=model)

    return AnthropicGenerator(api_key=api_key, model=model)
