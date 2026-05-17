"""Helpers for surfacing django-simple-history rows on detail pages.

Each model with a ``history`` manager (HistoricalRecords) gets ordered
revisions. For each revision we compute the per-field diff against the
previous revision, so the template can show 'who changed what, when'.

ForeignKey-valued changes coming out of ``diff_against`` carry raw PK
values (UUIDs, ints). To render them sensibly we resolve those PKs to
the related model's ``__str__`` here, so templates can render the
:class:`FieldChange` directly without knowing about FK plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fallback string when a related row referenced by an old/new value can no
# longer be loaded (e.g. it has been deleted since the revision was made).
DELETED_LABEL = "(обрисано)"


@dataclass(frozen=True)
class FieldChange:
    """One field change inside a single revision.

    ``old`` / ``new`` are the values as they will be rendered. For
    ForeignKey fields they are already resolved to the related row's
    ``__str__``; for everything else they are the raw scalar value.
    """

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


def _resolve_fk_value(model, field_name: str, value):
    """Return a display label for a FK ``value`` (PK), or ``value`` unchanged.

    - ``None`` is passed through so the template's ``|default:"—"`` works.
    - If the related instance can't be loaded (deleted row, wrong PK type,
      schema mismatch) we fall back to :data:`DELETED_LABEL`.
    - If ``field_name`` is not a relation on ``model`` we return ``value``
      untouched (numbers, dates, booleans, strings stay as they are).
    """
    if value in (None, ""):
        return value
    try:
        field = model._meta.get_field(field_name)
    except Exception:  # pylint: disable=broad-except
        return value
    if not getattr(field, "is_relation", False):
        return value
    related = getattr(field, "related_model", None)
    if related is None:
        return value
    try:
        return str(related._default_manager.get(pk=value))
    except related.DoesNotExist:  # pylint: disable=no-member
        return DELETED_LABEL
    except Exception:  # pylint: disable=broad-except
        # Wrong PK type, multi-tenant routing surprises, etc. – degrade
        # gracefully to the deleted label rather than raise on a panel.
        return DELETED_LABEL


def _resolve_change(model, field_name: str, old, new) -> tuple[object, object]:
    """Resolve both ends of a diff entry. Returns ``(old, new)``."""
    return (
        _resolve_fk_value(model, field_name, old),
        _resolve_fk_value(model, field_name, new),
    )


def history_for(instance, limit: int = 20) -> list[HistoryEntry]:
    """Return up to ``limit`` revisions of ``instance``, newest first.

    FK changes are resolved to the related row's ``__str__`` so templates
    don't have to deal with raw PKs.
    """
    if not hasattr(instance, "history"):
        return []
    model = type(instance)
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
                    old, new = _resolve_change(model, c.field, c.old, c.new)
                    changes.append(FieldChange(field=c.field, old=old, new=new))
            except Exception:  # pylint: disable=broad-except
                # If models differ between revisions diff_against can raise; ignore.
                changes = []
        entries.append(HistoryEntry(record=rec, changes=changes))
    return entries
