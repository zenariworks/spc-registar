"""Заједнички помоћници за приказе спискова домаћинстава (#340).

Раздвајање укућана на живе/преминуле и груписање домаћинстава по улици
понављало се у `slava_view` и `domacinstvo_view` (списак, детаљ, штампа).
Издвојено овде поред `territory.py` да сви прикази деле исту логику.
"""

from __future__ import annotations

from itertools import groupby


def razdvoji_zive_i_preminule(ukucani):
    """Раздваја укућане на (живи, преминули), чувајући редослед."""
    clanovi = list(ukucani)
    zivi = [u for u in clanovi if not u.preminuo]
    preminuli = [u for u in clanovi if u.preminuo]
    return zivi, preminuli


def grupisi_po_ulici(domacinstva):
    """Групише домаћинства по називу улице за штампане извештаје.

    Улаз мора већ бити сортиран по `adresa__ulica` (`groupby` групише само
    узастопне елементе); домаћинства без адресе иду у групу „Без улице".
    """

    def _ulica(d):
        if d.adresa and (d.adresa.ulica or "").strip():
            return d.adresa.ulica.strip()
        return ""

    return [
        {"ulica": ulica or "Без улице", "domacinstva": list(items)}
        for ulica, items in groupby(domacinstva, key=_ulica)
    ]
