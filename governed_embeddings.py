"""Minimal stubs for governed embedding helpers."""

from __future__ import annotations

from typing import Iterable, List


def governed_embed(texts: Iterable[str]) -> List[List[float]]:
    return [[float(len(t))] for t in texts]


def get_embedder():  # pragma: no cover - simple stub
    class _Embedder:
        def encode(self, texts: Iterable[str]) -> List[List[float]]:
            return governed_embed(texts)

    return _Embedder()


__all__ = ["governed_embed", "get_embedder"]

