"""Модул модела у апликацији регистар."""

from .adresa import Adresa
from .crkvena_opstina import CrkvenaOpstina
from .domacinstvo import Domacinstvo
from .eparhija import Eparhija
from .hram import Hram
from .krstenje import Krstenje
from .narodnost import Narodnost
from .parohija import Parohija
from .parohijan import Osoba, Parohijan
from .slava import Slava
from .svestenik import Svestenik
from .ukucanin import Ukucanin
from .vencanje import Vencanje
from .veroispovest import Veroispovest
from .zanimanje import Zanimanje

__all__ = [
    "Adresa",
    "CrkvenaOpstina",
    "Domacinstvo",
    "Eparhija",
    "Hram",
    "Krstenje",
    "Narodnost",
    "Parohija",
    "Osoba",
    "Parohijan",
    "Slava",
    "Svestenik",
    "Ukucanin",
    "Vencanje",
    "Veroispovest",
    "Zanimanje",
]
