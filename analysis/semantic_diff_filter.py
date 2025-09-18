"""Placeholder semantic diff filter used in tests."""

from __future__ import annotations

from typing import Iterable, List


def find_semantic_risks(*_args, **_kwargs) -> List[str]:  # type: ignore[override]
    """Return an empty list to indicate no semantic risks were detected."""

    return []


__all__ = ["find_semantic_risks"]

