"""
Модул модела крштења у бази података.
"""

import uuid

from django.core.validators import MinValueValidator
from django.db import models

from .base import TimestampedModel
from .hram import Hram
from .parohijan import Osoba
from .svestenik import Svestenik


class Krstenje(TimestampedModel):
    """Класа која представља крштења."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    # Везе са Особама (опционо - ако су регистроване)
    dete = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="krstenja_kao_dete",
        verbose_name="дете",
    )
    otac = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="krstenja_kao_otac",
        verbose_name="отац",
    )
    majka = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="krstenja_kao_majka",
        verbose_name="мајка",
    )
    kum = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="krstenja_kao_kum",
        verbose_name="кум",
    )

    redni_broj_krstenja_tekuca_godina = models.IntegerField(
        verbose_name="редни број крштења текућа година",
        validators=[MinValueValidator(1)],
    )
    krstenje_tekuca_godina = models.IntegerField(
        verbose_name="крштењe текућа година",
        validators=[MinValueValidator(1900)],
    )

    # podaci za registar(protokol) krstenih
    knjiga = models.IntegerField(
        verbose_name="књига", validators=[MinValueValidator(1)]
    )
    broj = models.IntegerField(verbose_name="број", validators=[MinValueValidator(1)])
    strana = models.IntegerField(
        verbose_name="страна", validators=[MinValueValidator(1)]
    )

    # podaci o krstenju
    datum = models.DateField(verbose_name="датум")
    vreme = models.TimeField(verbose_name="време", null=True, blank=True)
    mesto = models.CharField(
        max_length=255, verbose_name="место", null=True, blank=True
    )
    hram = models.ForeignKey(
        Hram, on_delete=models.SET_NULL, null=True, verbose_name="храм"
    )

    # podaci o detetu (adresa je specifična za događaj)
    adresa_deteta_grad = models.CharField(
        max_length=255, verbose_name="адреса детета град"
    )
    adresa_deteta_ulica = models.CharField(
        max_length=255, verbose_name="адреса детета улица", null=True, blank=True
    )
    adresa_deteta_broj = models.CharField(
        max_length=255, verbose_name="адреса детета број", null=True, blank=True
    )
    gradjansko_ime_deteta = models.CharField(
        max_length=255, verbose_name="грађанско име детета", null=True, blank=True
    )

    # adrese roditelja (specifične za događaj)
    adresa_oca_mesto = models.CharField(
        max_length=255, verbose_name="адреса оца место", null=True, blank=True
    )
    adresa_majke_mesto = models.CharField(
        max_length=255, verbose_name="адреса мајке место", null=True, blank=True
    )

    # ostali podaci o detetu
    dete_rodjeno_zivo = models.BooleanField(
        verbose_name="дете рођено живо", default=True
    )
    dete_po_redu_po_majci = models.CharField(
        verbose_name="дете по реду (по мајци)", null=True, blank=True
    )
    dete_vanbracno = models.BooleanField(verbose_name="ванбрачно дете")
    dete_blizanac = models.BooleanField(verbose_name="дете близанац")
    drugo_dete_blizanac_ime = models.CharField(
        max_length=255, verbose_name="име другог детета близанца", null=True, blank=True
    )
    dete_sa_telesnom_manom = models.BooleanField(verbose_name="дете са телесном маном")

    # podaci o svesteniku
    svestenik = models.ForeignKey(
        Svestenik,
        on_delete=models.SET_NULL,
        null=True,
        related_name="свештеник_крститељ",
        verbose_name="свештеник",
    )

    # adresa kuma (specifična za događaj)
    adresa_kuma_mesto = models.CharField(
        max_length=255, verbose_name="адреса кума место", null=True, blank=True
    )

    # podaci iz matične knjige - anagraf
    mesto_registracije = models.CharField(
        max_length=255, verbose_name="место регистрације", null=True, blank=True
    )
    datum_registracije = models.DateField(
        verbose_name="датум регистрације", null=True, blank=True
    )
    maticni_broj = models.CharField(
        max_length=255, verbose_name="матични број", null=True, blank=True
    )
    strana_registracije = models.CharField(
        max_length=255, verbose_name="страна регистрације", null=True, blank=True
    )

    primedba = models.TextField(blank=True, null=True, verbose_name="примедба")

    @property
    def ime_deteta(self):
        """Име детета из везаног Osoba objekta."""
        return self.dete.ime if self.dete else ""

    @property
    def pol_deteta(self):
        """Пол детета из везаног Osoba objekta."""
        return self.dete.pol if self.dete else ""

    @property
    def datum_rodjenja(self):
        """Датум рођења детета из везаног Osoba objekta."""
        return self.dete.datum_rodjenja if self.dete else None

    @property
    def vreme_rodjenja(self):
        """Време рођења детета из везаног Osoba objekta."""
        return self.dete.vreme_rodjenja if self.dete else ""

    @property
    def mesto_rodjenja(self):
        """Место рођења детета из везаног Osoba objekta."""
        return self.dete.mesto_rodjenja if self.dete else ""

    @property
    def ime_oca(self):
        """Име оца из везаног Osoba objekta."""
        return self.otac.ime if self.otac else ""

    @property
    def prezime_oca(self):
        """Презиме оца из везаног Osoba objekta."""
        return self.otac.prezime if self.otac else ""

    @property
    def zanimanje_oca(self):
        """Занимање оца из везаног Osoba objekta."""
        return self.otac.zanimanje if self.otac and self.otac.zanimanje else ""

    @property
    def veroispovest_oca(self):
        """Вероисповест оца из везаног Osoba objekta."""
        return self.otac.veroispovest if self.otac and self.otac.veroispovest else ""

    @property
    def narodnost_oca(self):
        """Народност оца из везаног Osoba objekta."""
        return self.otac.narodnost if self.otac and self.otac.narodnost else ""

    @property
    def ime_majke(self):
        """Име мајке из везаног Osoba objekta."""
        return self.majka.ime if self.majka else ""

    @property
    def prezime_majke(self):
        """Презиме мајке из везаног Osoba objekta."""
        return self.majka.prezime if self.majka else ""

    @property
    def zanimanje_majke(self):
        """Занимање мајке из везаног Osoba objekta."""
        return self.majka.zanimanje if self.majka and self.majka.zanimanje else ""

    @property
    def veroispovest_majke(self):
        """Вероисповест мајке из везаног Osoba objekta."""
        return self.majka.veroispovest if self.majka and self.majka.veroispovest else ""

    @property
    def narodnost_majke(self):
        """Народност мајке из везаног Osoba objekta."""
        return self.majka.narodnost if self.majka and self.majka.narodnost else ""

    @property
    def ime_kuma(self):
        """Име кума из везаног Osoba objekta."""
        return self.kum.ime if self.kum else ""

    @property
    def prezime_kuma(self):
        """Презиме кума из везаног Osoba objekta."""
        return self.kum.prezime if self.kum else ""

    @property
    def zanimanje_kuma(self):
        """Занимање кума из везаног Osoba objekta."""
        return self.kum.zanimanje if self.kum and self.kum.zanimanje else ""

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштење"
        verbose_name_plural = "Крштења"
