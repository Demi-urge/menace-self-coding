"""Lightweight knowledge graph shims for the open source snapshot.

The production Menace stack ships with a fairly involved knowledge graph that
persists relationships between bots, modules, telemetry and GPT derived
insights.  The original implementation depends on a number of internal
services and storage layers that are unavailable in this repository.  To keep
imports working we provide a minimal, threadsafe in-memory stand-in that models
only the behaviours exercised by the rest of the open source code.

The goal of this shim is not to be feature complete; it merely keeps track of
relationships between identifiers so helpers such as the quick fix engine can
obtain "related" entities.  The implementation intentionally favours
simplicity over fidelity – the graph resets with every process and silently
ignores persistence failures – but the public surface mirrors the subset of
the real API that the snapshot interacts with.
"""

from __future__ import annotations

import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Iterator, Mapping, MutableMapping, Sequence

try:  # pragma: no cover - optional dependency
    import networkx as _nx  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _nx = None  # type: ignore

__all__ = ["KnowledgeGraph"]


class _SimpleDiGraph:
    """Tiny directed graph used when :mod:`networkx` is unavailable.

    Only the methods touched by the surrounding code are implemented.  The
    object mimics the small slice of the ``networkx.DiGraph`` API that the
    snapshot relies upon (``add_node``/``add_edge``/``nodes``/``edges``).
    """

    def __init__(self) -> None:
        self.nodes: MutableMapping[str, dict[str, Any]] = {}
        self._edges: MutableMapping[str, MutableMapping[str, dict[str, Any]]] = (
            defaultdict(dict)
        )

    # ``networkx`` exposes ``nodes`` as a set-like view.  Returning the mapping
    # directly is sufficient for our needs and keeps the API largely familiar.
    def add_node(self, node: str, **attrs: Any) -> None:
        self.nodes.setdefault(node, {}).update(attrs)

    def add_edge(self, u: str, v: str, **attrs: Any) -> None:
        self.add_node(u)
        self.add_node(v)
        self._edges.setdefault(u, {})[v] = attrs

    def edges(self, data: bool = False) -> Iterator[tuple[str, str] | tuple[str, str, dict[str, Any]]]:
        for u, mapping in self._edges.items():
            for v, attrs in mapping.items():
                if data:
                    yield u, v, attrs
                else:
                    yield u, v


@dataclass
class _TelemetryEvent:
    bot: str
    event_type: str
    module: str | None
    patch_id: str | None
    resolved: bool | None
    timestamp: datetime
    meta: dict[str, Any]


class KnowledgeGraph:
    """Threadsafe, in-memory knowledge graph replacement."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        if _nx is not None:  # pragma: no cover - best effort
            try:
                self.graph = _nx.DiGraph()
            except Exception:  # pragma: no cover - best effort
                self.graph = _SimpleDiGraph()
        else:
            self.graph = _SimpleDiGraph()
        self._relations: MutableMapping[str, Counter[str]] = defaultdict(Counter)
        self._memory_tags: MutableMapping[str, set[str]] = defaultdict(set)
        self._events: list[_TelemetryEvent] = []
        self._error_stats: Counter[str] = Counter()

    # ------------------------------------------------------------------
    # internal helpers
    def _ensure_node(self, node: str, **attrs: Any) -> None:
        try:
            self.graph.add_node(node, **attrs)
        except Exception:  # pragma: no cover - defensive
            if hasattr(self.graph, "add_node"):
                self.graph.add_node(node)

    def _link(self, *nodes: str, weight: float = 1.0) -> None:
        uniq = [n for n in dict.fromkeys(nodes) if n]
        for idx, src in enumerate(uniq):
            self._ensure_node(src)
            for dst in uniq[idx + 1 :]:
                if src == dst:
                    continue
                self._relations[src][dst] += weight
                self._relations[dst][src] += weight
                try:  # pragma: no cover - optional networkx features
                    self.graph.add_edge(src, dst, weight=float(weight))
                    self.graph.add_edge(dst, src, weight=float(weight))
                except Exception:
                    try:
                        self.graph.add_edge(src, dst)
                        self.graph.add_edge(dst, src)
                    except Exception:
                        pass

    def _normalise_tag(self, tag: str) -> str:
        return tag.strip()

    # ------------------------------------------------------------------
    # public API mirroring the proprietary implementation
    def add_memory_entry(self, key: str, tags: Sequence[str] | None = None) -> None:
        """Record a memory ``key`` linked to the provided ``tags``.

        Tags are connected both to the ``memory`` node and to each other so the
        :meth:`related` lookup has useful adjacency information.
        """

        node_id = f"memory:{key}"
        with self._lock:
            self._ensure_node(node_id, kind="memory", key=key)
            if not tags:
                return
            normalised = sorted({self._normalise_tag(tag) for tag in tags if tag})
            self._memory_tags[key].update(normalised)
            for tag in normalised:
                self._ensure_node(tag, kind="tag")
                self._link(node_id, tag, weight=1.0)
            for idx, tag in enumerate(normalised):
                for other in normalised[idx + 1 :]:
                    self._link(tag, other, weight=0.5)

    def add_gpt_insight(
        self,
        key: str,
        *,
        bots: Sequence[str] | None = None,
        code_paths: Sequence[str] | None = None,
        error_categories: Sequence[str] | None = None,
    ) -> None:
        """Attach GPT derived metadata to an existing memory entry."""

        node_id = f"memory:{key}"
        with self._lock:
            self._ensure_node(node_id, kind="memory", key=key)
            nodes = [node_id]
            for prefix, values in (
                ("bot", bots),
                ("code", code_paths),
                ("error", error_categories),
            ):
                if not values:
                    continue
                for value in values:
                    if not value:
                        continue
                    node = f"{prefix}:{value}"
                    self._ensure_node(node, kind=prefix)
                    nodes.append(node)
            self._link(*nodes, weight=1.0)

    def add_telemetry_event(
        self,
        bot: str,
        event_type: str,
        module: str | None,
        mods: Mapping[str, int] | None = None,
        *,
        patch_id: str | int | None = None,
        resolved: bool | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        """Record a telemetry event and connect related nodes."""

        patch = None if patch_id is None else str(patch_id)
        record = _TelemetryEvent(
            bot=str(bot),
            event_type=str(event_type),
            module=str(module) if module else None,
            patch_id=patch,
            resolved=None if resolved is None else bool(resolved),
            timestamp=datetime.utcnow(),
            meta=dict(metadata or {}),
        )
        module_node = None
        if module:
            module_node = module if module.startswith("code:") else f"code:{module}"
        with self._lock:
            self._events.append(record)
            nodes = [f"bot:{record.bot}", f"event:{record.event_type}"]
            if module_node:
                nodes.append(module_node)
            if mods:
                for name in mods:
                    if not name:
                        continue
                    node = name if name.startswith("code:") else f"code:{name}"
                    nodes.append(node)
            self._link(*nodes, weight=1.0)
            if record.resolved:
                if module_node:
                    self._error_stats[module_node] = max(
                        0, self._error_stats.get(module_node, 0) - 1
                    )
            else:
                if module_node:
                    self._error_stats[module_node] += 1

    def related(self, node: str, limit: int = 10) -> list[str]:
        """Return nodes related to ``node`` ordered by frequency."""

        key = self._normalise_tag(node)
        with self._lock:
            neighbours = self._relations.get(key)
            if not neighbours:
                return []
            return [name for name, _ in neighbours.most_common(limit)]

    def update_error_stats(self, error_db: Any | None = None) -> None:
        """Best-effort synchronisation with an external error database.

        The open source snapshot only needs this to avoid crashes when the
        proprietary implementation refreshes cached statistics.  We attempt to
        pull mapping-like data from a handful of well named attributes or
        callables and fall back to leaving the in-memory counters untouched.
        """

        if error_db is None:
            return
        candidates = [
            getattr(error_db, "error_counts", None),
            getattr(error_db, "error_stats", None),
            getattr(error_db, "counts", None),
        ]
        for candidate in candidates:
            data: Mapping[str, Any] | None
            try:
                if callable(candidate):
                    data = candidate()
                else:
                    data = candidate  # type: ignore[assignment]
            except Exception:  # pragma: no cover - defensive
                continue
            if isinstance(data, Mapping):
                with self._lock:
                    self._error_stats = Counter({str(k): int(v) for k, v in data.items()})
                return

    # ------------------------------------------------------------------
    # diagnostic helpers ------------------------------------------------
    @property
    def telemetry_events(self) -> Sequence[_TelemetryEvent]:
        """Expose recorded telemetry for debugging and tests."""

        return list(self._events)

    @property
    def error_stats(self) -> Mapping[str, int]:
        """Return the most recent error statistics snapshot."""

        with self._lock:
            return dict(self._error_stats)
