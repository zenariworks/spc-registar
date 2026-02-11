"""Модул модела славе у бази података."""

from datetime import date, timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel


class Slava(TimeStampedModel):
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
        # Гаусов алгоритам за Православни (Јулијански) календар
        # За Православни календар: M = 15, N = 6

        a = year % 19
        b = year % 4
        c = year % 7

        M = 15  # За Јулијански календар
        N = 6  # За Јулијански календар

        d = (19 * a + M) % 30
        e = (2 * b + 4 * c + 6 * d + N) % 7

        # Одређивање датума
        if d + e < 10:
            # Ускрс пада у марту
            month = 3
            day = d + e + 22
        else:
            # Ускрс пада у априлу
            month = 4
            day = d + e - 9

        # Изузеци:
        # 1. Ако је 26. април, помера се на 19. април
        if month == 4 and day == 26:
            day = 19

        # 2. Ако је 25. април при чему је d=28, e=6, и a>10, помера се на 18. април
        if month == 4 and day == 25 and d == 28 and e == 6 and a > 10:
            day = 18

        # Јулијански датум
        julian_date = date(year, month, day)

        # Конверзија у Грегоријански календар
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
        from registar.utils import MESECI

        return MESECI.get(self.mesec, "") if self.mesec else ""

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "slave"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
