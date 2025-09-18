"""Provide a no-op :func:`auto_link` decorator used in tests."""

from __future__ import annotations

from typing import Any, Callable, Mapping


def auto_link(mapping: Mapping[str, str] | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a decorator that forwards the wrapped function unchanged."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


__all__ = ["auto_link"]

