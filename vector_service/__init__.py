"""Expose :mod:`menace.vector_service` as a top-level package."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_BASE_MODULE = importlib.import_module("menace.vector_service")

# Export the public API from the packaged module.
for name in getattr(_BASE_MODULE, "__all__", []):
    globals()[name] = getattr(_BASE_MODULE, name)

# Make sure submodules are discoverable via ``vector_service.<module>`` imports.
_BASE_PATH = Path(_BASE_MODULE.__file__ or "").resolve().parent
__path__ = [str(Path(__file__).resolve().parent), str(_BASE_PATH)]


def __getattr__(name: str) -> Any:  # pragma: no cover - dynamic proxy
    try:
        module = importlib.import_module(f"menace.vector_service.{name}")
    except ModuleNotFoundError as exc:
        try:
            return getattr(_BASE_MODULE, name)
        except AttributeError:
            raise exc from None
    sys.modules[f"vector_service.{name}"] = module
    return module


def __dir__() -> list[str]:  # pragma: no cover - convenience
    return sorted(set(globals()) | set(dir(_BASE_MODULE)))


__all__ = list(getattr(_BASE_MODULE, "__all__", []))

