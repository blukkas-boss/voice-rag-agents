"""Chunker — split documents into overlapping token-estimated chunks.

Uses a simple character-based token proxy (len // 4) so chunking works
without a real tokenizer. Configurable chunk_size and overlap from
voice_rag_agents.config.settings.
"""

from __future__ import annotations

from voice_rag_agents.config.settings import get_settings


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English prose."""
    return max(1, len(text) // 4)


def chunk_documents(
    documents: list[dict],
    chunk_size_tokens: int | None = None,
    chunk_overlap_tokens: int | None = None,
) -> list[dict]:
    """Split *documents* into overlapping chunks.

    Each input dict must have ``page_content`` and ``metadata``.
    Each returned dict has: ``text``, ``source``, ``chunk_index``,
    ``token_count``, ``metadata``.
    """
    settings = get_settings()
    size = chunk_size_tokens or settings.chunk_size_tokens
    overlap = chunk_overlap_tokens or settings.chunk_overlap_tokens
    # Convert token budget to character budget (~4 chars/token)
    char_size = size * 4
    char_overlap = overlap * 4
    step = max(1, char_size - char_overlap)

    chunks: list[dict] = []
    for doc in documents:
        text = doc.get("page_content", "")
        if not text:
            continue
        source = doc.get("metadata", {}).get("source_file", "unknown")
        base_meta = {k: v for k, v in doc.get("metadata", {}).items()}

        idx = 0
        pos = 0
        while pos < len(text):
            end = min(pos + char_size, len(text))
            chunk_text = text[pos:end]
            chunks.append(
                {
                    "text": chunk_text,
                    "source": source,
                    "chunk_index": idx,
                    "token_count": _estimate_tokens(chunk_text),
                    "metadata": {
                        **base_meta,
                        "char_start": pos,
                        "char_end": end,
                    },
                }
            )
            idx += 1
            pos += step
            if end == len(text):
                break

    return chunks
