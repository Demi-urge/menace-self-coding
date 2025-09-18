"""Simplified publish/subscribe event bus for standalone environments."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, DefaultDict, Dict, List
import logging

logger = logging.getLogger(__name__)


class UnifiedEventBus:
    """Very small in-memory pub/sub bus."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[[str, object], None]]] = (
            defaultdict(list)
        )

    def publish(self, topic: str, payload: object) -> bool:
        callbacks = list(self._subscribers.get(topic, ()))
        for callback in callbacks:
            try:
                callback(topic, payload)
            except Exception:
                logger.debug("event subscriber failed for %s", topic, exc_info=True)
        return True

    def subscribe(self, topic: str, callback: Callable[[str, object], None]) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._subscribers[topic].append(callback)


__all__ = ["UnifiedEventBus"]

