"""Django форме за унос и претрагу података."""

from .domacinstvo import DomacinstvoForm
from .forms import SearchForm
from .krstenje import KrstenjeForm
from .parohijan import ParohijanForm
from .svestenik import SvestenikForm
from .vencanje import VencanjeForm

__all__ = [
    "DomacinstvoForm",
    "SearchForm",
    "KrstenjeForm",
    "ParohijanForm",
    "SvestenikForm",
    "VencanjeForm",
]
