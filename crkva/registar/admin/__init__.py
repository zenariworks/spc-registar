"""Модул за администрацију Django модела у апликацији регистар."""

from .adresa_admin import AdresaAdmin
from .crkvena_opstina_admin import CrkvenaOpstinaAdmin
from .domacinstvo_admin import DomacinstvоAdmin
from .eparhija_admin import EparhijaAdmin
from .hram_admin import HramAdmin
from .krstenje_admin import KrstenjeAdmin
from .narodnost_admin import NarodnostAdmin
from .parohija_admin import ParohijaAdmin
from .parohijan_admin import ParohijanAdmin
from .svestenik_admin import SvestenikAdmin
from .ukucanin_admin import UkucaninAdmin
from .vencanje_admin import VencanjeAdmin
from .veroispovest_admin import VeroispovestAdmin
from .zanimanje_admin import ZanimanjeAdmin

__all__ = [
    "AdresaAdmin",
    "CrkvenaOpstinaAdmin",
    "DomacinstvоAdmin",
    "EparhijaAdmin",
    "HramAdmin",
    "KrstenjeAdmin",
    "NarodnostAdmin",
    "ParohijaAdmin",
    "ParohijanAdmin",
    "SvestenikAdmin",
    "UkucaninAdmin",
    "VencanjeAdmin",
    "VeroispovestAdmin",
    "ZanimanjeAdmin",
]
