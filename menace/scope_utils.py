"""Utility helpers for applying scope filters to SQL queries."""

from __future__ import annotations

from enum import Enum


class Scope(str, Enum):
    """Enumeration representing database visibility scopes."""

    GLOBAL = "global"
    SHARED = "shared"
    LOCAL = "local"

    @classmethod
    def _missing_(cls, value: object) -> "Scope":  # pragma: no cover - simple
        if isinstance(value, Scope):
            return value
        if value is None:
            return cls.GLOBAL
        value_str = str(value).lower()
        for member in cls:
            if member.value == value_str:
                return member
        return cls.GLOBAL


def build_scope_clause(
    table: str,
    scope: Scope | str | None,
    menace_id: str | None,
) -> tuple[str, list[str]]:
    """Return a SQL clause enforcing the requested *scope*.

    The simplified implementation only distinguishes between ``LOCAL`` and all
    other scopes.  Local scope filters rows to the provided ``menace_id`` when
    available, while global/shared scopes return a no-op clause.
    """

    resolved_scope = Scope(scope) if scope is not None else Scope.GLOBAL
    if resolved_scope is Scope.LOCAL and menace_id:
        prefix = f"{table}." if table else ""
        return f"{prefix}source_menace_id=?", [menace_id]
    return "1=1", []


def apply_scope(query: str, clause: str) -> str:
    """Inject *clause* into ``query`` when necessary."""

    clause = clause.strip()
    if not clause or clause == "1=1":
        return query

    if "{scope_clause}" in query:
        return query.replace("{scope_clause}", clause)

    upper_query = query.upper()
    if " WHERE " in upper_query:
        return f"{query} AND {clause}"
    return f"{query} WHERE {clause}"


__all__ = ["Scope", "build_scope_clause", "apply_scope"]

