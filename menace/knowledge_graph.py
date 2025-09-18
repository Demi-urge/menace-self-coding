"""Simple placeholder knowledge graph implementation."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple


class KnowledgeGraph:
    """Very small in-memory directed graph."""

    def __init__(self) -> None:
        self._edges: Dict[str, Set[str]] = defaultdict(set)

    def add_edge(self, source: str, target: str) -> None:
        self._edges[source].add(target)

    def neighbours(self, node: str) -> List[str]:
        return sorted(self._edges.get(node, ()))


__all__ = ["KnowledgeGraph"]

