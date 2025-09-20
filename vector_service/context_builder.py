"""Compatibility layer exposing the canonical :mod:`ContextBuilder` API.

Historically the real implementation lived in :mod:`vector_service`.  The
project was later refactored so the heavy ``ContextBuilder`` implementation sits
at the repository root (and is also vendored under ``menace`` for package
installs), while this module only provided minimal error helpers.  Some callers
– like the sandbox bootstrap script in this kata – still import
``ContextBuilder`` from :mod:`vector_service.context_builder`.  Importing the
module therefore raised ``ImportError`` because the class was no longer exposed
here.

To retain backwards compatibility we now proxy the public surface of the real
builder and error helpers.  This keeps import paths stable without duplicating
logic.
"""

from __future__ import annotations

# ``PromptBuildError`` and ``handle_failure`` live in ``prompt_failure``.  We try
# the package-relative import first to support ``menace.*`` consumers and fall
# back to the repository root module for direct execution from source.
try:  # pragma: no cover - optional when package layout differs
    from menace.prompt_failure import (  # type: ignore
        PromptBuildError as _PromptBuildError,
        handle_failure as _handle_failure,
    )
except ImportError:  # pragma: no cover - fallback during local execution
    from prompt_failure import (  # type: ignore
        PromptBuildError as _PromptBuildError,
        handle_failure as _handle_failure,
    )

# Re-export ``ContextBuilder`` and related helpers from their canonical module.
# The implementation lives at the repository root but is also mirrored under the
# ``menace`` namespace when installed as a package.
try:  # pragma: no cover - optional when executed from installed package
    from menace.context_builder import (  # type: ignore
        ContextBuilder,
        build_prompt,
        load_failed_tags,
        record_failed_tags,
    )
except ImportError:  # pragma: no cover - fallback when running from source
    from context_builder import (  # type: ignore
        ContextBuilder,
        build_prompt,
        load_failed_tags,
        record_failed_tags,
    )


PromptBuildError = _PromptBuildError
handle_failure = _handle_failure

# ``__all__`` explicitly lists the symbols re-exported for consumers relying on
# ``from vector_service.context_builder import …`` semantics.
__all__ = [
    "ContextBuilder",
    "PromptBuildError",
    "handle_failure",
    "build_prompt",
    "load_failed_tags",
    "record_failed_tags",
]


