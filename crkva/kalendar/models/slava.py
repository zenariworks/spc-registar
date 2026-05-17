"""Модул модела славе (shared model — public schema).

Slava (saint feast day) is shared across all tenants — every parish references
the same canonical list. Lives in the public schema via django-tenants
SHARED_APPS.

Cross-schema FK note: tenant tables like Domacinstvo.slava reference this
public table; those FKs use db_constraint=False because Postgres FKs cannot
cross schemas safely in a django-tenants setup.
"""

from datetime import date, timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel

MESECI = {
    1: "јануар",
    2: "фебруар",
    3: "март",
    4: "април",
    5: "мај",
    6: "јун",
    7: "јул",
    8: "август",
    9: "септембар",
    10: "октобар",
    11: "новембар",
    12: "децембар",
}


class Slava(TimeStampedModel):
    """Канонска класа Славе — shared across tenants."""

    uid = models.AutoField(primary_key=True, unique=True, editable=False)

    naziv = models.CharField(verbose_name="назив")
    opsti_naziv = models.CharField(verbose_name="општи назив")

    # Фиксни датуми
    dan = models.IntegerField(
        verbose_name="дан",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        null=True,
        blank=True,
        db_index=True,
    )
    mesec = models.IntegerField(
        verbose_name="месец",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        null=True,
        blank=True,
        db_index=True,
    )

    # Покретни празници
    pokretni = models.BooleanField(
        verbose_name="покретни празник",
        default=False,
        help_text="Празник који се рачуна у односу на Васкрс",
    )

    offset_dani = models.IntegerField(
        verbose_name="помак у данима",
        null=True,
        blank=True,
        help_text="Број дана у односу на Васкрс",
    )

    offset_nedelje = models.IntegerField(
        verbose_name="помак у недељама",
        null=True,
        blank=True,
        help_text="Број недеља у односу на Васкрс",
    )

    # Постови
    post = models.BooleanField(verbose_name="пост", default=False)

    post_od = models.IntegerField(
        verbose_name="почетак поста (дани)",
        null=True,
        blank=True,
        help_text="Почетак поста у данима од Васкрса",
    )

    post_do = models.IntegerField(
        verbose_name="крај поста (дани)",
        null=True,
        blank=True,
        help_text="Крај поста у данима од Васкрса",
    )

    # Црвено слово - велики празници
    crveno_slovo = models.BooleanField(
        verbose_name="црвено слово",
        default=False,
        help_text="Велики празник (црвено слово у календару)",
    )

    @staticmethod
    def calc_vaskrs(year):
        """Рачуна православни Васкрс за дату годину користећи Гаусов алгоритам."""
        a = year % 19
        b = year % 4
        c = year % 7

        M = 15  # За Јулијански календар
        N = 6  # За Јулијански календар

        d = (19 * a + M) % 30
        e = (2 * b + 4 * c + 6 * d + N) % 7

        if d + e < 10:
            month = 3
            day = d + e + 22
        else:
            month = 4
            day = d + e - 9

        if month == 4 and day == 26:
            day = 19

        if month == 4 and day == 25 and d == 28 and e == 6 and a > 10:
            day = 18

        julian_date = date(year, month, day)

        if 1900 <= year < 2100:
            offset = 13
        elif 2100 <= year < 2200:
            offset = 14
        elif 1800 <= year < 1900:
            offset = 12
        else:
            offset = year // 100 - year // 400 - 2

        return julian_date + timedelta(days=offset)

    def get_datum(self, year):
        """Враћа датум славе за дату годину."""
        if self.pokretni:
            vaskrs = self.calc_vaskrs(year)
            offset = 0
            if self.offset_dani:
                offset += self.offset_dani
            if self.offset_nedelje:
                offset += self.offset_nedelje * 7
            return vaskrs + timedelta(days=offset)

        if self.dan and self.mesec:
            return date(year, self.mesec, self.dan)
        return None

    def get_post(self, year):
        """Враћа период поста за дату годину (почетак, крај)."""
        if not self.post:
            return None

        vaskrs = self.calc_vaskrs(year)
        start = None
        end = None

        if self.post_od is not None:
            start = vaskrs + timedelta(days=self.post_od)
        if self.post_do is not None:
            end = vaskrs + timedelta(days=self.post_do)

        return (start, end)

    def get_mesec_naziv(self):
        """Враћа назив месеца."""
        return MESECI.get(self.mesec, "") if self.mesec else ""

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        app_label = "kalendar"
        managed = True
        db_table = "slave"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
