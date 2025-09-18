"""Simplified text chunking utilities used by the Menace sandbox."""

from __future__ import annotations

from typing import Iterable, Iterator, List, Sequence


def split_into_chunks(text: str, max_chars: int = 500) -> List[str]:
    """Split ``text`` into chunks of at most ``max_chars`` characters."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)] or [""]


def get_chunk_summaries(chunks: Sequence[str]) -> List[str]:
    """Return lightweight summaries for ``chunks``."""

    return [chunk[:80] for chunk in chunks]


__all__ = ["split_into_chunks", "get_chunk_summaries"]

