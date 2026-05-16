"""Structured skip/error logging for migration commands.

The old log_warning / log_error free-form strings made it hard to find
the source row when something went wrong. RecordContext attaches a
stable identifier (knjiga/strana/broj/redni_broj) to each log line so
debugging is a quick grep instead of a guess.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordContext:
    """Identifies a source row for error reporting."""

    table: str
    redni_broj: int | None = None
    godina: int | None = None
    knjiga: str | None = None
    strana: str | None = None
    broj: str | None = None

    def __str__(self) -> str:
        parts = [self.table]
        if self.redni_broj is not None:
            parts.append(f"#{self.redni_broj}")
        if self.godina:
            parts.append(f"{self.godina}.")
        if self.knjiga or self.strana or self.broj:
            parts.append(
                f"књ.{self.knjiga or '?'} стр.{self.strana or '?'} бр.{self.broj or '?'}"
            )
        return " ".join(parts)


class RecordSkipped(Exception):
    """Raise to signal a record was skipped (will be counted, not surfaced as error)."""

    def __init__(self, ctx: RecordContext, reason: str):
        super().__init__(f"{ctx}: {reason}")
        self.ctx = ctx
        self.reason = reason
