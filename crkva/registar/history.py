"""Helpers for surfacing django-simple-history rows on detail pages.

Each model with a `history` manager (HistoricalRecords) gets ordered
revisions. For each revision we compute the per-field diff against the
previous revision, so the template can show 'who changed what, when'.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldChange:
    """One field change inside a single revision."""

    field: str
    old: object
    new: object


@dataclass(frozen=True)
class HistoryEntry:
    """One revision with its field changes vs. the previous revision."""

    record: object
    changes: list[FieldChange]


CREATE = "+"
UPDATE = "~"
DELETE = "-"

ACTION_LABEL = {
    CREATE: "Креирано",
    UPDATE: "Измењено",
    DELETE: "Обрисано",
}


def history_for(instance, limit: int = 20) -> list[HistoryEntry]:
    """Return up to `limit` revisions of `instance`, newest first."""
    if not hasattr(instance, "history"):
        return []
    records = list(
        instance.history.select_related("history_user").order_by("-history_date")[
            :limit
        ]
    )
    entries: list[HistoryEntry] = []
    for i, rec in enumerate(records):
        # diff_against(prev) gives ModelChange objects; oldest revision has no diff.
        prev = records[i + 1] if i + 1 < len(records) else None
        changes: list[FieldChange] = []
        if prev is not None:
            try:
                delta = rec.diff_against(prev)
                for c in delta.changes:
                    changes.append(FieldChange(field=c.field, old=c.old, new=c.new))
            except Exception:  # pylint: disable=broad-except
                # If models differ between revisions diff_against can raise; ignore.
                changes = []
        entries.append(HistoryEntry(record=rec, changes=changes))
    return entries
