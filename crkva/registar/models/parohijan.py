"""Модул модела особе у бази података."""

from django.db import models
from model_utils.models import TimeStampedModel
from registar.fields import TenantPhoneNumberField
from simple_history.models import HistoricalRecords

from .adresa import Adresa
from .narodnost import Narodnost
from .veroispovest import Veroispovest
from .zanimanje import Zanimanje


class Osoba(TimeStampedModel):
    """Класа која представља особу (парохијанин или друга особа из црквених записа)."""

    uid = models.AutoField(primary_key=True, unique=True, editable=False)

    ime = models.CharField(max_length=100, verbose_name="име", db_index=True)
    prezime = models.CharField(max_length=100, verbose_name="презиме", db_index=True)

    devojacko = models.CharField(
        max_length=100, verbose_name="девојачко презиме", blank=True, null=True
    )

    gradjansko_ime = models.CharField(
        max_length=100,
        verbose_name="грађанско име",
        blank=True,
        null=True,
        help_text="Грађанско (световно) име ако се разликује од крштеног",
    )

    parohijan = models.BooleanField(
        default=False, verbose_name="парохијан", help_text="Да ли је особа парохијанин"
    )

    # Подаци специфични за парохијане (опционо за остале)
    adresa = models.ForeignKey(
        Adresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="адреса"
    )
    tel_fiksni = TenantPhoneNumberField(
        verbose_name="фиксни телефон", blank=True, null=True
    )
    tel_mobilni = TenantPhoneNumberField(
        verbose_name="мобилни телефон", blank=True, null=True
    )
    email = models.EmailField(
        max_length=254, verbose_name="имејл", blank=True, null=True
    )

    # Основни подаци о особи
    mesto_rodjenja = models.CharField(
        max_length=100, verbose_name="место рођења", blank=True, null=True
    )
    datum_rodjenja = models.DateField(
        verbose_name="датум рођења", blank=True, null=True
    )
    vreme_rodjenja = models.TimeField(
        verbose_name="време рођења", blank=True, null=True
    )
    pol = models.CharField(
        max_length=1,
        verbose_name="пол",
        choices=[("М", "мушки"), ("Ж", "женски")],
        blank=True,
        null=True,
        db_index=True,
    )

    zanimanje = models.ForeignKey(
        Zanimanje,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="занимање",
    )
    veroispovest = models.ForeignKey(
        Veroispovest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="вероисповест",
    )
    narodnost = models.ForeignKey(
        Narodnost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="народност",
    )

    history = HistoricalRecords(user_db_constraint=False)

    def __str__(self):
        """Женске особе са девојачким презименом приказују га уз редовно име —
        „Љиљана Ристивојевић (рођ. Јовановић)" — свуда где се Osoba
        приказује као чист текст (select2 опције, поља улога у
        венчању, админ ознаке). HTML-стилизовани поднаслови
        детаља и даље исписују делове ручно ради посебне типографије.
        """
        if self.pol == "Ж" and self.devojacko:
            return f"{self.ime} {self.prezime} (рођ. {self.devojacko})"
        return f"{self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table = "osobe"
        verbose_name = "Особа"
        verbose_name_plural = "Особе"
        ordering = ["prezime", "ime"]
        indexes = [
            # Supports the "-created" / "created" sort options on parohijani list.
            models.Index(fields=["created"], name="osoba_created_idx"),
        ]
