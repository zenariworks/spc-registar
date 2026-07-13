"""
Utility modules for the registar app.

Пресловљавање и DBF конвертори живе у :mod:`registar.utils.preslovljavanje`;
овде их само ре-експортујемо ради компатибилности старих import путања.
"""

from kalendar.models.slava import MESECI  # noqa: F401
from registar.utils.preslovljavanje import get_query_variants, preslovi  # noqa: F401

__all__ = [
    "MESECI",
    "get_query_variants",
    "preslovi",
]
