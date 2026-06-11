"""Канонска дефиниција покретних празника Васкршњег циклуса (issue #259).

Једини извор истине за покретне празнике. Користе га:

* сејачи ``unos_slava`` и ``migracija_slava`` — да их **не** уписују као
  фиксне (са лажним датумом из извора), већ као покретне;
* команда ``fix_moveable_feasts`` — за помирење већ постојеће базе.

Сваки празник има ``offset_dani`` (помак у данима у односу на Васкрсну
недељу); види :meth:`kalendar.models.Slava.get_datum`.

ВАЖНО: имена морају тачно одговарати називима у извору (``fixtures/slave.sql``
и DBF ``hsp_slave`` након ``Konvertor.string``), јер се поклапање ради по
називу. Међу покретним празницима свако име је јединствено (легитимни
истоимени фиксни празници на различите дане — нпр. Св. Атанасије 31.1 и 15.5 —
НИСУ покретни и овде се не наводе).
"""

# naziv, opsti_naziv, offset_dani (помак од Васкрса у данима)
MOVEABLE_FEASTS = [
    {"naziv": "Лазарева субота", "opsti_naziv": "Врбица", "offset_dani": -8},
    {"naziv": "Улазак Господа Исуса Христа у Јерусалим", "opsti_naziv": "Цвети", "offset_dani": -7},
    {"naziv": "Велики четвртак (Велико бденије)", "opsti_naziv": "", "offset_dani": -3},
    {"naziv": "Велики петак", "opsti_naziv": "", "offset_dani": -2},
    {"naziv": "Велика субота", "opsti_naziv": "", "offset_dani": -1},
    {"naziv": "Васкрсење Господа исуса Христа", "opsti_naziv": "ВАСКРС", "offset_dani": 0},
    {"naziv": "Васкрски понедељак", "opsti_naziv": "", "offset_dani": 1},
    {"naziv": "Васкрсни уторак", "opsti_naziv": "", "offset_dani": 2},
    {"naziv": "Вазнесење Господње", "opsti_naziv": "Спасовдан", "offset_dani": 39},
    {"naziv": "Силазак Светог Духа на апостоле-Педесетница-Тројице", "opsti_naziv": "", "offset_dani": 49},
    {"naziv": "Духовски понедељак", "opsti_naziv": "", "offset_dani": 50},
    {"naziv": "Духовски уторак", "opsti_naziv": "", "offset_dani": 51},
]

MOVEABLE_FEAST_NAMES = frozenset(f["naziv"] for f in MOVEABLE_FEASTS)


def is_moveable_feast(naziv):
    """Да ли се празник датог назива сматра покретним (Васкршњи циклус)."""
    return naziv in MOVEABLE_FEAST_NAMES


def upsert_moveable_feasts(stdout=None):
    """Осигурава да сваки покретни празник постоји као тачно један покретни ред.

    Идемпотентно. За сваки канонски празник: ако ред(ови) са тим називом већ
    постоје, узима канонски (већ покретни ако постоји, иначе најмањи uid) и
    претвара га у покретни; ако не постоји ниједан, креира га. **Не** брише
    евентуалне вишак фиксне копије — то ради ``fix_moveable_feasts`` (због
    премештања ``Domacinstvo`` веза кроз tenant шеме). Враћа број
    креираних/претворених празника.

    Намењено да га зову сејачи (``unos_slava``, ``migracija_slava``) као
    замену за упис фиксних редова покретних празника.
    """
    from kalendar.models import Slava

    touched = 0
    for feast in MOVEABLE_FEASTS:
        rows = list(Slava.objects.filter(naziv=feast["naziv"]).order_by("uid"))
        canonical = next((r for r in rows if r.pokretni), rows[0] if rows else None)
        if canonical is None:
            canonical = Slava(naziv=feast["naziv"])
        if not canonical.opsti_naziv:
            canonical.opsti_naziv = feast["opsti_naziv"]
        canonical.pokretni = True
        canonical.offset_dani = feast["offset_dani"]
        canonical.offset_nedelje = 0
        canonical.dan = None
        canonical.mesec = None
        canonical.save()
        touched += 1
        if stdout is not None:
            stdout.write(f"  ↻ покретни осигуран: „{feast['naziv']}“ (uid={canonical.uid})")
    return touched
