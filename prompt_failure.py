"""Utilities for reporting prompt construction failures consistently."""

from __future__ import annotations

import logging


class PromptBuildError(RuntimeError):
    """Exception raised when a prompt cannot be constructed reliably."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


def handle_failure(
    message: str,
    exc: Exception,
    *,
    logger: logging.Logger | None = None,
    raise_error: bool = True,
) -> None:
    """Log ``exc`` against ``message`` and optionally raise a wrapped error.

    Parameters
    ----------
    message:
        Human readable context describing the failure.
    exc:
        The original exception that triggered the failure handling.
    logger:
        Optional logger used for reporting.  When ``None`` a module level logger
        is used instead.  Any logging errors are swallowed so that failure
        handling never introduces additional crashes.
    raise_error:
        When ``True`` (the default) the function re-raises ``exc`` wrapped in a
        :class:`PromptBuildError`.  Callers can disable re-raising when they only
        need to record the failure but intend to handle the error themselves.
    """

    log = logger or logging.getLogger(__name__)
    try:
        log.exception(message, exc_info=exc)
    except Exception:
        # ``logger`` might be a mock or custom object.  Avoid bubbling up logging
        # issues when handling the original failure.
        logging.getLogger(__name__).error("%s: %s", message, exc)

    if not raise_error:
        return

    if isinstance(exc, PromptBuildError):
        raise exc

    raise PromptBuildError(message, cause=exc) from exc
