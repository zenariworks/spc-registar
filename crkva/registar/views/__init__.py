"""Модул за приказе у апликацији регистар.

Овај фајл служи само као агрегатор увоза/реекспорта. Стварна логика
живи у одвојеним модулима по ентитету (parohijan_view, krstenje_view,
vencanje_view, ...) и по намени (home_view, search_view, brzi_view).
"""

from .adresa_view import duplikati_adresa, spoji_adresu
from .brzi_view import (
    brzi_izmena_adrese,
    brzi_unos_adrese,
    brzi_unos_hrama,
    brzi_unos_osobe,
    brzi_unos_parohije,
    brzi_unos_svestenika,
)
from .domacinstvo_view import (
    PrikazDomacinstva,
    SpisakDomacinsta,
    domacinstva_print,
    izmena_domacinstva,
    unos_domacinstva,
)
from .home_view import index
from .kalendar_view import kalendar
from .krstenje_view import (
    KrstenjePDF,
    PrikazKrstenja,
    SpisakKrstenja,
    calibrate_krstenje,
    izmena_krstenja,
    unos_krstenja,
)
from .parohijan_view import (
    ParohijanPDF,
    PrikazParohijana,
    SpisakParohijana,
    izmena_parohijana,
    unos_parohijana,
)
from .search_view import SEARCH_PREVIEW_LIMIT, search_autocomplete, search_view
from .slava_view import slava_domacinstva
from .vodica_view import vaskrsnja_vodica
from .svestenik_view import (
    PrikazSvestenika,
    SpisakSvestenika,
    SvestenikPDF,
    izmena_svestenika,
    unos_svestenika,
)
from .vencanje_view import (
    PrikazVencanja,
    SpisakVencanja,
    VencanjePDF,
    calibrate_vencanje,
    izmena_vencanja,
    unos_vencanja,
)
from .view_404 import custom_404

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
