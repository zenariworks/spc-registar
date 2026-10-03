"""Својства уписа која читају поље везане особе (дете, отац, кум …).

Модели уписа (крштење, венчање) приказују податке особа преко много кратких
својстава. Ове фабрике праве таква својства из назива везе и поља, уместо да
свако буде посебна метода са истим обрасцем.

`opis_osobe` и `opis_veze` састављају опис особе у једном реду (име, занимање,
место, …) за приказ уписа.
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


def spoji(*delovi) -> str:
    """Спаја непразне делове зарезом (без празнина и двоструких зареза)."""
    return ", ".join(str(d).strip() for d in delovi if d is not None and str(d).strip())


def mala(vrednost) -> str:
    """Мала слова за заједничке именице (занимање, вера, народност)."""
    return str(vrednost).lower() if vrednost else ""


def opis_osobe(ime, prezime, zanimanje, adresa, *dodatno) -> str:
    """Особа у реду: име презиме, занимање, место становања, па `dodatno`.

    Занимање и додатни делови (вера, народност) су малим словима.
    """
    ime_prezime = " ".join(p for p in (ime, prezime) if p)
    mesto = adresa.mesto if adresa else ""
    return spoji(ime_prezime, mala(zanimanje), mesto, *(mala(d) for d in dodatno))


def opis_veze(uloga: str, opis: str = "") -> property:
    """Опис везане особе (`opis_osobe`), или празан стринг кад није везана."""

    def citaj(self):
        osoba = getattr(self, uloga)
        if not osoba:
            return ""
        return opis_osobe(osoba.ime, osoba.prezime, osoba.zanimanje, osoba.adresa)

    return property(citaj, doc=opis)
