"""Својства уписа која читају поље везане особе (дете, отац, кум …).

Модели уписа (крштење, венчање) приказују податке особа преко много кратких
својстава. Ове фабрике праве таква својства из назива везе и поља, уместо да
свако буде посебна метода са истим обрасцем.
"""

from __future__ import annotations


def polje_osobe(uloga: str, polje: str, prazno="", opis: str = "") -> property:
    """`uloga.polje`, или `prazno` кад особа није везана."""

    def citaj(self):
        osoba = getattr(self, uloga)
        return getattr(osoba, polje) if osoba else prazno

    return property(citaj, doc=opis)


def popunjeno_polje_osobe(uloga: str, polje: str, opis: str = "") -> property:
    """`uloga.polje` ако је особа везана и поље попуњено, иначе празан стринг."""

    def citaj(self):
        osoba = getattr(self, uloga)
        vrednost = getattr(osoba, polje) if osoba else None
        return vrednost if vrednost else ""

    return property(citaj, doc=opis)


def naziv_polja_osobe(uloga: str, polje: str, opis: str = "") -> property:
    """`str(uloga.polje)` ако је особа везана и поље попуњено, иначе празан стринг."""

    def citaj(self):
        osoba = getattr(self, uloga)
        vrednost = getattr(osoba, polje) if osoba else None
        return str(vrednost) if vrednost else ""

    return property(citaj, doc=opis)
