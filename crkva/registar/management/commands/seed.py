"""Групне подкоманде за сидере: ``manage.py seed <под-команда>``.

Логика живи у ``registar/seed/`` (није више top-level команда после #353);
ова typer група враћа груписан CLI приступ за ручно покретање/дебаговање.
"""

from __future__ import annotations

import typer
from django.core.management import call_command
from django_typer.management import TyperCommand, command
from registar.seed import (
    unos_adresa,
    unos_domacinstava,
    unos_krstenja,
    unos_parohijana,
    unos_sifarnika,
    unos_slava,
    unos_svestenika,
    unos_vencanja,
)

# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-arguments,too-many-positional-arguments,bad-staticmethod-argument,unused-argument


Tenant = typer.Option(..., help="Schema name тенанта.")


class Command(TyperCommand):
    help = "Сидери (mock/референтни подаци) — групне подкоманде."

    def _mock(self, modul, tenant, count, source, seed, reset):
        kwargs = {"tenant": tenant, "source": source, "reset": reset}
        if count is not None:
            kwargs["count"] = count
        if seed is not None:
            kwargs["seed"] = seed
        call_command(modul.Command(), **kwargs)

    @command(help="Шифрарници (народности, вероисповести, занимања, епархије, славе).")
    def sifarnika(self, tenant: str = Tenant):
        call_command(unos_sifarnika.Command(), tenant=tenant)

    @command(help="Календар слава из fixtures/slave.jsonl.")
    def slava(self):
        call_command(unos_slava.Command())

    @command(help="Свештеници (mock или dummy).")
    def svestenici(
        self,
        tenant: str = Tenant,
        count: int | None = None,
        source: str = "mock",
        seed: int | None = None,
        reset: bool = False,
    ):
        self._mock(unos_svestenika, tenant, count, source, seed, reset)

    @command(help="Адресе.")
    def adrese(
        self,
        tenant: str = Tenant,
        count: int | None = None,
        source: str = "mock",
        seed: int | None = None,
        reset: bool = False,
    ):
        self._mock(unos_adresa, tenant, count, source, seed, reset)

    @command(help="Парохијани (особе).")
    def parohijani(
        self,
        tenant: str = Tenant,
        count: int | None = None,
        source: str = "mock",
        seed: int | None = None,
        reset: bool = False,
    ):
        self._mock(unos_parohijana, tenant, count, source, seed, reset)

    @command(help="Домаћинства.")
    def domacinstva(
        self,
        tenant: str = Tenant,
        count: int | None = None,
        source: str = "mock",
        seed: int | None = None,
        reset: bool = False,
    ):
        self._mock(unos_domacinstava, tenant, count, source, seed, reset)

    @command(help="Крштења.")
    def krstenja(
        self,
        tenant: str = Tenant,
        count: int | None = None,
        source: str = "mock",
        seed: int | None = None,
        reset: bool = False,
    ):
        self._mock(unos_krstenja, tenant, count, source, seed, reset)

    @command(help="Венчања.")
    def vencanja(
        self,
        tenant: str = Tenant,
        count: int | None = None,
        source: str = "mock",
        seed: int | None = None,
        reset: bool = False,
    ):
        self._mock(unos_vencanja, tenant, count, source, seed, reset)
