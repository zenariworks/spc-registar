"""Django форме за унос и претрагу података."""

from .domacinstvo_form import DomacinstvoForm
from .forms import SearchForm
from .krstenje_form import KrstenjeForm
from .parohijan_form import ParohijanForm
from .svestenik_form import SvestenikForm
from .vencanje_form import VencanjeForm

__all__ = [
    "DomacinstvoForm",
    "SearchForm",
    "KrstenjeForm",
    "ParohijanForm",
    "SvestenikForm",
    "VencanjeForm",
]
