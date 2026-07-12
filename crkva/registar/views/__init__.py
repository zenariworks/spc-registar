"""Модул за приказе у апликацији регистар.

Овај фајл служи само као агрегатор увоза/реекспорта. Стварна логика
живи у одвојеним модулима по ентитету (parohijan_view, krstenje_view,
vencanje_view, ...) и по намени (home_view, search_view, brzi_view).
"""

from .adresa import duplikati_adresa, spoji_adresu
from .brzi_prikaz import (
    brzi_izmena_adrese,
    brzi_unos_adrese,
    brzi_unos_hrama,
    brzi_unos_osobe,
    brzi_unos_parohije,
    brzi_unos_svestenika,
)
from .domacinstvo import (
    PrikazDomacinstva,
    SpisakDomacinsta,
    domacinstva_print,
    izmena_domacinstva,
    unos_domacinstva,
)
from .home import index
from .kalendar import kalendar
from .krstenje import (
    KrstenjePDF,
    PrikazKrstenja,
    SpisakKrstenja,
    calibrate_krstenje,
    izmena_krstenja,
    unos_krstenja,
)
from .parohijan import (
    ParohijanPDF,
    PrikazParohijana,
    SpisakParohijana,
    izmena_parohijana,
    unos_parohijana,
)
from .search import SEARCH_PREVIEW_LIMIT, search_autocomplete, search_view
from .slava import slava_domacinstva
from .svestenik import (
    PrikazSvestenika,
    SpisakSvestenika,
    SvestenikPDF,
    izmena_svestenika,
    unos_svestenika,
)
from .vencanje import (
    PrikazVencanja,
    SpisakVencanja,
    VencanjePDF,
    calibrate_vencanje,
    izmena_vencanja,
    unos_vencanja,
)
from .view_404 import custom_404
from .vodica import vaskrsnja_vodica

__all__ = [
    # Re-exports for url config and other modules
    "PrikazDomacinstva",
    "SpisakDomacinsta",
    "unos_domacinstva",
    "kalendar",
    "KrstenjePDF",
    "PrikazKrstenja",
    "SpisakKrstenja",
    "calibrate_krstenje",
    "unos_krstenja",
    "ParohijanPDF",
    "PrikazParohijana",
    "SpisakParohijana",
    "unos_parohijana",
    "slava_domacinstva",
    "PrikazSvestenika",
    "SpisakSvestenika",
    "unos_svestenika",
    "SvestenikPDF",
    "PrikazVencanja",
    "SpisakVencanja",
    "VencanjePDF",
    "calibrate_vencanje",
    "unos_vencanja",
    "izmena_domacinstva",
    "izmena_svestenika",
    "izmena_vencanja",
    "izmena_krstenja",
    "izmena_parohijana",
    "custom_404",
    "vaskrsnja_vodica",
    "domacinstva_print",
    # Functions defined in this module
    "index",
    "search_view",
    "search_autocomplete",
]
