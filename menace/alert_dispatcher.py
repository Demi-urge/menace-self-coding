"""Placeholder alert dispatcher used in the self-coding sandbox."""

from __future__ import annotations

from typing import Any, Dict

CONFIG: Dict[str, Any] = {}


def send_discord_alert(*_args: Any, **_kwargs: Any) -> bool:
    """Stub implementation that pretends to send an alert."""

    return False


__all__ = ["CONFIG", "send_discord_alert"]

