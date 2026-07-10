"""Разрешавање циљних шема за per-tenant cleanup команде (#330).

Команде ``popravi_*`` су раније подразумевано петљале кроз СВЕ закупце када
``--schema`` није дат, па је увоз једне парохије брисао/преписивао податке
других. Овде је безбедан подразумевани избор: ради се само над АКТИВНОМ
шемом; масовни рад захтева изричито ``--all-tenants``.
"""

from __future__ import annotations

from django.core.management.base import CommandError
from django.db import connection
from django_tenants.utils import get_tenant_model


def razresi_ciljne_sheme(opcije: dict) -> list[str]:
    """Врати листу schema имена над којима команда сме да ради.

    - ``--all-tenants`` → сви закупци осим ``public``.
    - ``--schema=X``    → само ``X`` (мора постојати).
    - иначе             → само тренутно активна шема; одбија ``public``
      (fail-fast, да се спречи ненамеран cross-tenant или public упис).
    """
    samo_shema: str | None = opcije.get("schema")
    svi_zakupci: bool = opcije.get("all_tenants", False)
    model_zakupca = get_tenant_model()

    if svi_zakupci and samo_shema:
        raise CommandError("--all-tenants и --schema се међусобно искључују.")

    if svi_zakupci:
        return list(
            model_zakupca.objects.exclude(schema_name="public").values_list(
                "schema_name", flat=True
            )
        )

    if samo_shema:
        if not model_zakupca.objects.filter(schema_name=samo_shema).exists():
            raise CommandError(f"Шема не постоји: {samo_shema}")
        return [samo_shema]

    aktivna_shema = connection.schema_name
    if aktivna_shema == "public":
        raise CommandError(
            "Одбијено над public шемом. Покрени преко tenant_command "
            "(--schema бира парохију), или изричито дај --schema=<шема> "
            "или --all-tenants."
        )
    return [aktivna_shema]
