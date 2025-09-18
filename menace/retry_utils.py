"""Minimal retry helpers used when the full infrastructure is unavailable."""

from __future__ import annotations

from typing import Any, Callable, TypeVar
import functools
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that executes ``func`` and logs failures without retrying."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except Exception:  # pragma: no cover - best effort
            logger.exception("operation failed without retry: %s", func.__name__)
            raise

    return wrapper


def publish_with_retry(bus: Any, topic: str, payload: Any) -> bool:
    """Attempt to publish ``payload`` to ``topic`` on ``bus`` once."""

    try:
        publish = getattr(bus, "publish", None)
        if callable(publish):
            publish(topic, payload)
            return True
    except Exception:  # pragma: no cover - best effort
        logger.debug("publish_with_retry failed for %s", topic, exc_info=True)
    return False


__all__ = ["publish_with_retry", "with_retry"]

