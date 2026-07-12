"""Групне подкоманде за DBF миграцију: ``manage.py migracija <под-команда>``.

Логика живи у ``registar/uvoz/`` (није више top-level команда после #353).
``--schema`` бира парохијску шему (кораци одбијају public).
"""

from __future__ import annotations

import typer
from django.core.management import call_command
from django_tenants.utils import schema_context
from django_typer.management import TyperCommand, command
from registar.uvoz import (
    krstenja,
    svestenici,
    ukucani_parohijani,
    veliki_postovi,
    vencanja,
)

# pylint: disable=missing-class-docstring,missing-function-docstring,too-many-arguments,too-many-positional-arguments,bad-staticmethod-argument,unused-argument


Schema = typer.Option(..., help="Schema name парохије (не public).")


class Command(TyperCommand):
    help = "DBF миграциони кораци — групне подкоманде."

    def _migriraj(self, modul, schema, dry_run, limit):
        with schema_context(schema):
            call_command(modul.Command(), dry_run=dry_run, limit=limit)

    @command(help="Свештеници.")
    def svestenici(self, schema: str = Schema, dry_run: bool = False, limit: int = 0):
        self._migriraj(svestenici, schema, dry_run, limit)

    @command(help="Домаћинства + парохијани.")
    def ukucani(self, schema: str = Schema, dry_run: bool = False, limit: int = 0):
        self._migriraj(ukucani_parohijani, schema, dry_run, limit)

    @command(help="Крштења.")
    def krstenja(self, schema: str = Schema, dry_run: bool = False, limit: int = 0):
        self._migriraj(krstenja, schema, dry_run, limit)

    @command(help="Венчања.")
    def vencanja(self, schema: str = Schema, dry_run: bool = False, limit: int = 0):
        self._migriraj(vencanja, schema, dry_run, limit)

    @command(help="Обележавање црвених слова (велики празници).")
    def praznici(self, schema: str = Schema):
        with schema_context(schema):
            call_command(veliki_postovi.Command())
