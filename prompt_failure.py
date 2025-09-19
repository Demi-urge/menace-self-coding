"""Utilities for consistent handling of prompt construction failures.

The real project exposes helpers that normalise how prompt construction errors
are surfaced to callers.  Portions of this repository import the helpers
whether the code is executed as a package (``menace.prompt_failure``) or from
source (``prompt_failure``).  The original module was omitted from this kata,
so we provide a lightweight, fully documented implementation that captures the
behaviour relied on by the surrounding code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Any

__all__ = ["PromptBuildError", "handle_failure"]


@dataclass(slots=True)
class PromptBuildError(RuntimeError):
    """Exception raised when constructing an LLM prompt fails.

    Parameters
    ----------
    message:
        Human readable message describing the failure.  This mirrors the base
        :class:`RuntimeError` constructor to preserve backwards compatibility.
    metadata:
        Optional mapping with additional structured information about the
        failure.  Callers can use this to propagate context to higher layers.
    original_exception:
        The underlying exception that triggered the prompt build failure.  This
        is stored for diagnostic purposes and is also used as the exception
        ``__cause__`` when raised via :func:`handle_failure`.
    """

    message: str
    metadata: MutableMapping[str, Any]
    original_exception: Exception | None = None

    def __init__(
        self,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "metadata", dict(metadata or {}))
        object.__setattr__(self, "original_exception", original_exception)


# Default logger used when callers do not provide one.
_LOGGER = logging.getLogger("menace.prompt_failure")


def handle_failure(
    message: str,
    exc: Exception,
    *,
    logger: logging.Logger | None = None,
    raise_error: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    """Log a prompt build failure and optionally raise a wrapped exception.

    The helper centralises error reporting so modules constructing prompts do
    not have to duplicate logging or wrapping logic.  Errors are logged using
    :meth:`logging.Logger.exception` to capture the stack trace.  When
    ``raise_error`` is ``True`` (the default) a :class:`PromptBuildError` is
    raised so callers can handle prompt specific failures distinctly from other
    exceptions.
    """

    log = logger if logger is not None else _LOGGER
    details: MutableMapping[str, Any] = dict(metadata or {})
    details.setdefault("message", message)
    details.setdefault("exception_type", exc.__class__.__name__)

    try:
        log.exception(message, exc_info=exc, extra={"metadata": details})
    except Exception:  # pragma: no cover - logging should never crash callers
        try:
            log.exception(message, exc_info=exc)
        except Exception:  # pragma: no cover - ultimate fallback for logging
            print(f"[prompt_failure] {message}: {exc}")

    if not raise_error:
        return

    if isinstance(exc, PromptBuildError):
        raise exc

    error = PromptBuildError(
        message,
        metadata=details,
        original_exception=exc,
    )
    raise error from exc
