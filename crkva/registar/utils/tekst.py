"""Помоћне функције за нормализацију текста (lookup називи)."""

from __future__ import annotations

import re

_WS_RE = re.compile(r"\s+")


def normalize_naziv(value: str | None) -> str:
    """Скрати водеће/пратеће размаке и сведи унутрашње на један размак.

    Користи се да lookup називи (Занимање/Вероисповест/Народност) буду
    конзистентни, па case-insensitive ограничење јединствености не пропусти
    дупликате типа „лекар“ / „Лекар “ (#252).
    """
    return _WS_RE.sub(" ", (value or "").strip())
