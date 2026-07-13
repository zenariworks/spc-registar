"""
Utility modules for the registar app.

Транслитерација и DBF конвертори живе у :mod:`registar.utils.preslovljavanje`;
овде их само ре-експортујемо ради компатибилности старих import путања.
"""

from kalendar.models.slava import MESECI  # noqa: F401
from registar.utils.preslovljavanje import (  # noqa: F401
    preslovljavanje,
    get_query_variants,
    latin_to_cyrillic,
)

__all__ = [
    "MESECI",
    "preslovljavanje",
    "get_query_variants",
    "latin_to_cyrillic",
]
