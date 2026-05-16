"""Memoised get-or-create for small lookup tables.

Each migration was building ad-hoc caches with slightly different lookup
keys for Veroispovest, Narodnost, Zanimanje, Hram, etc. This wraps the
pattern in one class so the cache hit/miss behaviour is consistent.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from __future__ import annotations

import re
from typing import Callable

from django.db.models import Model


class LookupCache:
    """Memoise get_or_create for a (model, key_field) pair.

    Usage:
        veroispovest = LookupCache(Veroispovest, key_field="naziv")
        v = veroispovest.get("православна")
    """

    def __init__(
        self,
        model: type[Model],
        key_field: str = "naziv",
        key_normaliser: Callable[[str], str] | None = None,
        extra_defaults: dict | None = None,
    ):
        self.model = model
        self.key_field = key_field
        self._normalise = key_normaliser or (lambda x: x)
        self._extra_defaults = extra_defaults or {}
        self._cache: dict[str, Model] = {}

    def warm(self):
        """Prefill the cache with every existing row. Use once at start."""
        for obj in self.model.objects.all():
            key = self._normalise(getattr(obj, self.key_field))
            self._cache[key] = obj

    def get(self, raw_key: str | None) -> Model | None:
        if not raw_key or not str(raw_key).strip():
            return None
        key = self._normalise(str(raw_key).strip())
        if key not in self._cache:
            obj, _ = self.model.objects.get_or_create(
                **{f"{self.key_field}__iexact": key},
                defaults={self.key_field: key, **self._extra_defaults},
            )
            self._cache[key] = obj
        return self._cache[key]


# --- Hram has its own quirks: strip the literal "храм"/"hram" from the naziv ---

_HRAM_LITERAL = re.compile(r"(?i)\bhram\b|\bхрам\b")


def normalise_hram_naziv(naziv: str | None) -> str:
    if not naziv:
        return "Непознат храм"
    stripped = _HRAM_LITERAL.sub("", naziv).strip()
    return stripped or "Непознат храм"


# --- Zanimanje normaliser: lowercase ---


def normalise_zanimanje(naziv: str) -> str:
    return naziv.lower()
