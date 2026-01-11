"""Модул за администрацију Django модела у апликацији регистар."""

from .adresa_admin import AdresaAdmin
from .crkvena_opstina_admin import CrkvenaOpstinaAdmin
from .domacinstvo_admin import DomacinstvоAdmin
from .drzava_admin import DrzavaAdmin
from .eparhija_admin import EparhijaAdmin
from .hram_admin import HramAdmin
from .krstenje_admin import KrstenjeAdmin
from .mesto_admin import MestoAdmin
from .narodnost_admin import NarodnostAdmin
from .opstina_admin import OpstinaAdmin
from .parohija_admin import ParohijaAdmin
from .parohijan_admin import ParohijanAdmin
from .slava_admin import SlavaAdmin
from .svestenik_admin import SvestenikAdmin
from .ukucanin_admin import UkucaninAdmin
from .ulica_admin import UlicaAdmin
from .vencanje_admin import VencanjeAdmin
from .veroispovest_admin import VeroispovestAdmin
from .zanimanje_admin import ZanimanjeAdmin

__all__ = [
    "AdresaAdmin",
    "CrkvenaOpstinaAdmin",
    "DomacinstvоAdmin",
    "DrzavaAdmin",
    "EparhijaAdmin",
    "HramAdmin",
    "KrstenjeAdmin",
    "MestoAdmin",
    "NarodnostAdmin",
    "OpstinaAdmin",
    "ParohijaAdmin",
    "ParohijanAdmin",
    "SlavaAdmin",
    "SvestenikAdmin",
    "UkucaninAdmin",
    "UlicaAdmin",
    "VencanjeAdmin",
    "VeroispovestAdmin",
    "ZanimanjeAdmin",
]
