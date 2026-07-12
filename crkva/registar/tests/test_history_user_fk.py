"""Регресија за #331: history_user FK свих Historical* модела мора имати
``db_constraint=False``.

Historical табеле живе у tenant шемама, а ``history_user`` показује на
``public.auth_user``. Са правим Postgres FK-ом, брисање корисника који је
уређивао запис у *неактивној* шеми обара интегритет (FK violation коју Django
collector не види) и квари pg_dump/restore и клонирање шема. ``db_constraint=False``
задржава Django-везу али уклања FK ограничење на нивоу базе.
"""

from django.test import SimpleTestCase
from registar.models import (
    Adresa,
    Domacinstvo,
    Krstenje,
    Osoba,
    Svestenik,
    Ukucanin,
    Vencanje,
)

MODELI_SA_ISTORIJOM = [
    Adresa,
    Domacinstvo,
    Krstenje,
    Osoba,
    Svestenik,
    Ukucanin,
    Vencanje,
]


class HistoryUserFKConstraintTest(SimpleTestCase):
    def test_history_user_bez_db_constrainta(self):
        for model in MODELI_SA_ISTORIJOM:
            istorijski = model.history.model
            polje = istorijski._meta.get_field("history_user")
            with self.subTest(model=istorijski.__name__):
                self.assertFalse(
                    polje.db_constraint,
                    f"{istorijski.__name__}.history_user мора имати "
                    "db_constraint=False (укрштени FK ка public.auth_user)",
                )
