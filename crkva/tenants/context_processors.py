"""Expose `tenant` to every template."""

from __future__ import annotations


def current_tenant(request):
    return {"tenant": getattr(request, "tenant", None)}
