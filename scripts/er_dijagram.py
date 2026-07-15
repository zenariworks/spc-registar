#!/usr/bin/env python
"""Генерише mermaid `erDiagram` из Django модела.

Дијаграм у `docs/architecture.md` је раније писан руком, па је ћутке одлазио
из корака са моделима. Овде се гради интроспекцијом: колоне, PK/FK ознаке,
кардиналност и `verbose_name` као ознака везе — приказ близак dbdiagram.io.

Блок се уписује између маркера `<!-- er:start -->` и `<!-- er:end -->`.

Покретање (из корена репозиторијума):

    python scripts/er_dijagram.py            # штампа блок на stdout
    python scripts/er_dijagram.py --upisi    # уписује у architecture.md
    python scripts/er_dijagram.py --check    # пада ако је док застарео (pre-commit)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

KOREN = Path(__file__).resolve().parent.parent

# Django пројекат живи у `crkva/`; скрипта се покреће из корена, па га
# стављамо на пут пре увоза Django-а. Отуда увоз испод дефиниције.
sys.path.insert(0, str(KOREN / "crkva"))

# pylint: disable=wrong-import-position
import django  # noqa: E402
from django.apps import apps  # noqa: E402

# pylint: enable=wrong-import-position

APPS = ("registar", "tenants", "kalendar")

START = "<!-- er:start -->"
END = "<!-- er:end -->"

# Django internal type -> кратак тип колоне (mermaid не трпи размаке у типу).
TIPOVI = {
    "AutoField": "int",
    "BigAutoField": "int",
    "UUIDField": "uuid",
    "CharField": "string",
    "TextField": "text",
    "EmailField": "string",
    "IntegerField": "int",
    "PositiveSmallIntegerField": "int",
    "SmallIntegerField": "int",
    "BooleanField": "bool",
    "DateField": "date",
    "DateTimeField": "datetime",
    "TimeField": "time",
    "PhoneNumberField": "phone",
}


def tip(field) -> str:
    """Тип колоне.

    За FK/O2O враћа тип PK-а на који поље показује, а не генеричко „fk“ —
    дијаграм приказује стварне колоне (`adresa_id uuid`), као dbdiagram.io.
    """
    if field.is_relation and field.related_model is not None:
        field = field.target_field
    interni = field.get_internal_type()
    return TIPOVI.get(interni, interni.lower())


def je_istorijski(model) -> bool:
    """Тачно за `simple_history` ревизионе моделе — они се не цртају."""
    return model.__name__.startswith("Historical")


def modeli() -> list:
    """Сви модели из `APPS`, без ревизионих, сортирани по имену."""
    nadjeni = []
    for app in APPS:
        for model in apps.get_app_config(app).get_models():
            if not je_istorijski(model):
                nadjeni.append(model)
    return sorted(nadjeni, key=lambda m: m.__name__)


def entitet(model) -> list[str]:
    """Mermaid блок једног ентитета — све колоне са PK/FK ознакама."""
    linije = [f"    {model.__name__} {{"]
    for field in model._meta.fields:  # pylint: disable=protected-access
        if field.primary_key:
            kljuc = " PK"
        elif field.is_relation:
            kljuc = " FK"
        else:
            kljuc = ""
        ime = field.column if field.is_relation else field.name
        linije.append(f"        {tip(field)} {ime}{kljuc}")
    linije.append("    }")
    return linije


def veze(svi) -> list[str]:
    """Mermaid линије веза, изведене из FK/O2O поља.

    Везе ка моделима ван обухвата (нпр. `auth.User`) се прескачу — цртао би
    се ентитет без колона.
    """
    imena = {m.__name__ for m in svi}
    nadjene = set()
    for model in svi:
        for field in model._meta.fields:  # pylint: disable=protected-access
            if not field.is_relation or field.related_model is None:
                continue
            roditelj = field.related_model.__name__
            if roditelj not in imena:
                continue
            kard = "||--o|" if field.one_to_one else "||--o{"
            opis = str(field.verbose_name or field.name)
            if getattr(field, "db_constraint", True) is False:
                opis = f"{opis} (cross-schema)"
            nadjene.add(f'    {roditelj} {kard} {model.__name__} : "{opis}"')
    return sorted(nadjene)


def generisi() -> str:
    """Цео mermaid блок, спреман за уметање у Markdown."""
    svi = modeli()
    linije = ["```mermaid", "erDiagram"]
    for model in svi:
        linije += entitet(model)
    linije += veze(svi)
    linije.append("```")
    return "\n".join(linije)


def main() -> int:
    """Улазна тачка; враћа излазни код процеса."""
    raspoznavac = argparse.ArgumentParser(description=__doc__)
    raspoznavac.add_argument(
        "--upisi", action="store_true", help="упиши блок у docs/architecture.md"
    )
    raspoznavac.add_argument(
        "--check", action="store_true", help="пади ако је док застарео"
    )
    args = raspoznavac.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crkva.settings")
    django.setup()

    blok = generisi()

    if not (args.upisi or args.check):
        print(blok)
        return 0

    dok = KOREN / "docs" / "architecture.md"
    txt = dok.read_text(encoding="utf-8")
    obrazac = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not obrazac.search(txt):
        print(f"маркери {START} / {END} нису нађени у {dok}", file=sys.stderr)
        return 2
    novi = obrazac.sub(f"{START}\n\n{blok}\n\n{END}", txt)

    if args.check:
        if novi != txt:
            print(
                "ER дијаграм у docs/architecture.md је застарео.\n"
                "Покрени из корена репозиторијума: "
                "python scripts/er_dijagram.py --upisi",
                file=sys.stderr,
            )
            return 1
        print("ER дијаграм је у кораку са моделима.")
        return 0

    dok.write_text(novi, encoding="utf-8")
    print(f"уписано у {dok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
