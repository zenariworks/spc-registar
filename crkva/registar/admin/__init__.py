"""Модул за администрацију Django модела у апликацији регистар."""

from .adresa import AdresaAdmin
from .crkvena_opstina import CrkvenaOpstinaAdmin
from .domacinstvo import DomacinstvоAdmin
from .eparhija import EparhijaAdmin
from .hram import HramAdmin
from .krstenje import KrstenjeAdmin
from .narodnost import NarodnostAdmin
from .parohija import ParohijaAdmin
from .parohijan import ParohijanAdmin
from .svestenik import SvestenikAdmin
from .ukucanin import UkucaninAdmin
from .vencanje import VencanjeAdmin
from .veroispovest import VeroispovestAdmin
from .zanimanje import ZanimanjeAdmin

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
