"""Simplified GPT memory interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class MemoryEntry:
    key: str
    text: str
    tags: str = ""


class GPTMemoryInterface:
    """In-memory implementation for storing snippets."""

    def __init__(self) -> None:
        self._entries: Dict[str, MemoryEntry] = {}

    def store(self, key: str, text: str, *, tags: str = "") -> None:
        self._entries[key] = MemoryEntry(key, text, tags)

    def get(self, key: str) -> Optional[str]:
        entry = self._entries.get(key)
        return entry.text if entry else None

    def search_by_tag(self, tag: str) -> List[MemoryEntry]:
        return [entry for entry in self._entries.values() if tag in entry.tags]


__all__ = ["GPTMemoryInterface", "MemoryEntry"]

