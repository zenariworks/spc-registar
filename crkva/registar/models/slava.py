"""Модул модела славе у бази података."""

from datetime import date, timedelta
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Slava(models.Model):
    """Класа која представља слава."""

    uid = models.AutoField(primary_key=True, unique=True, editable=False)

    naziv = models.CharField(verbose_name="назив")
    opsti_naziv = models.CharField(verbose_name="општи назив")

    # Фиксни датуми
    dan = models.IntegerField(
        verbose_name="дан",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        null=True,
        blank=True,
    )
    mesec = models.IntegerField(
        verbose_name="месец",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        null=True,
        blank=True,
    )

    # Покретни празници
    pokretni = models.BooleanField(
        verbose_name="покретни празник",
        default=False,
        help_text="Празник који се рачуна у односу на Васкрс"
    )

    offset_dani = models.IntegerField(
        verbose_name="помак у данима",
        null=True,
        blank=True,
        help_text="Број дана у односу на Васкрс"
    )

    offset_nedelje = models.IntegerField(
        verbose_name="помак у недељама",
        null=True,
        blank=True,
        help_text="Број недеља у односу на Васкрс"
    )

    # Постови
    post = models.BooleanField(
        verbose_name="пост",
        default=False
    )

    post_od = models.IntegerField(
        verbose_name="почетак поста (дани)",
        null=True,
        blank=True,
        help_text="Почетак поста у данима од Васкрса"
    )

    post_do = models.IntegerField(
        verbose_name="крај поста (дани)",
        null=True,
        blank=True,
        help_text="Крај поста у данима од Васкрса"
    )

    @staticmethod
    def calc_vaskrs(year):
        """Рачуна православни Васкрс за дату годину."""
        # Meeus/Jones/Butcher алгоритам за Јулијански календар
        a = year % 4
        b = year % 7
        c = year % 19
        d = (19 * c + 15) % 30
        e = (2 * a + 4 * b - d + 34) % 7
        month = (d + e + 114) // 31
        day = ((d + e + 114) % 31) + 1

        # Јулијански датум
        julian_date = date(year, month, day)

        # Конверзија у Грегоријански календар
        if year >= 1900 and year < 2100:
            offset = 13
        elif year >= 2100 and year < 2200:
            offset = 14
        elif year >= 1800 and year < 1900:
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
        else:
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
        from registar.utils import MESECI
        return MESECI.get(self.mesec, "") if self.mesec else ""

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "slave"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
