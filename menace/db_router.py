"""Lightweight database router used for local development and tests.

This module provides a greatly simplified stand-in for the production
``db_router`` implementation that ships with the original Menace project.
The goal is not to be feature complete, but to offer enough functionality so
that high level orchestration code can be imported and exercised in isolated
environments where the real infrastructure (multiple SQLite databases,
embedding services, background workers, etc.) is unavailable.

The :class:`DBRouter` class manages a small collection of SQLite connections
backed by on-disk databases when paths are supplied, or in-memory databases
otherwise.  Connections are cached per logical database name.  A minimal
"memory manager" is also included so callers that expect a publish/subscribe
style interface can continue to operate without raising ``AttributeError``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, List, MutableMapping
import logging
import sqlite3
import threading

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Globals mirroring the public API of the original module
LOCAL_TABLES: set[str] = set()
GLOBAL_ROUTER: "DBRouter | None" = None


@dataclass
class _Subscription:
    topic: str
    callback: Callable[[str, object], None]


class _MemoryManager:
    """Very small publish/subscribe hub used by a number of modules."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscriptions: List[_Subscription] = []

    def subscribe(self, topic: str, callback: Callable[[str, object], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._lock:
            self._subscriptions.append(_Subscription(topic, callback))

    def publish(self, topic: str, payload: object) -> None:
        with self._lock:
            callbacks = [s.callback for s in self._subscriptions if s.topic == topic]
        for cb in callbacks:
            try:
                cb(topic, payload)
            except Exception:
                logger.debug("memory manager callback failed for %s", topic, exc_info=True)

    # The real implementation exposes richer query capabilities.  Returning an
    # empty iterator keeps callers functional while making the limitation clear.
    def search_by_tag(self, _tag: str) -> Iterator[object]:  # pragma: no cover - simple
        return iter(())


class DBRouter:
    """Route logical database names to SQLite connections."""

    def __init__(
        self,
        menace_id: str,
        local_path: str | Path | None = None,
        shared_path: str | Path | None = None,
        *,
        read_only: bool = False,
        memory_mgr: _MemoryManager | None = None,
    ) -> None:
        if not menace_id:
            raise ValueError("menace_id is required")
        self.menace_id = menace_id
        self._lock = threading.RLock()
        self._connections: MutableMapping[str, sqlite3.Connection] = {}
        self._local_base = self._prepare_path(local_path)
        self._shared_base = self._prepare_path(shared_path)
        self._read_only = read_only
        self.memory_mgr = memory_mgr or _MemoryManager()

    # ------------------------------------------------------------------
    @staticmethod
    def _prepare_path(path: str | Path | None) -> Path | None:
        if path is None:
            return None
        p = Path(path).expanduser().resolve()
        if p.suffix:
            # Parent directories may not exist yet when files are provided.
            p.parent.mkdir(parents=True, exist_ok=True)
        else:
            p.mkdir(parents=True, exist_ok=True)
        return p

    def _db_path(self, name: str) -> str:
        base: Path | None
        if name in LOCAL_TABLES and self._local_base is not None:
            base = self._local_base
        elif self._shared_base is not None:
            base = self._shared_base
        else:
            base = self._local_base

        if base is None:
            return ":memory:"

        if base.suffix:
            # Treat the base as a file path; reuse it for all logical databases.
            return str(base)

        return str(base / f"{name}.db")

    def _create_connection(self, name: str) -> sqlite3.Connection:
        path = self._db_path(name)
        uri = path
        if self._read_only and path != ":memory:":
            uri = f"file:{Path(path).as_uri().replace('file:', '')}?mode=ro"
        conn = sqlite3.connect(uri, check_same_thread=False, uri=self._read_only)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    def get_connection(self, name: str) -> sqlite3.Connection:
        """Return a cached SQLite connection for *name*."""

        with self._lock:
            conn = self._connections.get(name)
            if conn is None:
                conn = self._create_connection(name)
                self._connections[name] = conn
        return conn

    # The production router exposes FTS search helpers. Returning an empty list
    # keeps consumers functional while signalling that no results are available.
    def search_fts(
        self, query: str, *, dbs: Iterable[str] | None = None, limit: int = 10
    ) -> list[tuple[str, float]]:  # pragma: no cover - simple behaviour
        logger.debug(
            "FTS search requested for %s on %s with limit %s", query, dbs, limit
        )
        return []

    def close(self, name: str | None = None) -> None:
        with self._lock:
            if name is not None:
                conn = self._connections.pop(name, None)
                if conn is not None:
                    conn.close()
            else:
                for conn in self._connections.values():
                    conn.close()
                self._connections.clear()


def init_db_router(
    menace_id: str,
    local_path: str | Path | None = None,
    shared_path: str | Path | None = None,
    *,
    read_only: bool = False,
) -> DBRouter:
    """Create and cache a :class:`DBRouter` instance."""

    global GLOBAL_ROUTER
    router = DBRouter(
        menace_id,
        local_path=local_path,
        shared_path=shared_path,
        read_only=read_only,
    )
    GLOBAL_ROUTER = router
    logger.debug("Initialised DBRouter for %s", menace_id)
    return router


__all__ = [
    "DBRouter",
    "GLOBAL_ROUTER",
    "LOCAL_TABLES",
    "init_db_router",
]

