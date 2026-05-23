"""
Модул модела крштења у бази података.
"""

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from .hram import Hram
from .parohijan import Osoba
from .svestenik import Svestenik


class Krstenje(TimeStampedModel):
    """Класа која представља крштења."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    godina_registracije = models.IntegerField(
        verbose_name="година регистрације",
        validators=[MinValueValidator(1900)],
        db_index=True,
    )
    redni_broj = models.IntegerField(
        verbose_name="редни број крштења",
        validators=[MinValueValidator(1)],
    )

    knjiga = models.IntegerField(
        verbose_name="књига", validators=[MinValueValidator(1)], default=1
    )
    strana = models.IntegerField(
        verbose_name="страна", validators=[MinValueValidator(1)]
    )
    broj = models.IntegerField(
        verbose_name="текући број", validators=[MinValueValidator(1)], default=1
    )

    datum = models.DateField(verbose_name="датум", null=True, blank=True, db_index=True)
    vreme = models.TimeField(verbose_name="време", null=True, blank=True)
    hram = models.ForeignKey(
        Hram, on_delete=models.SET_NULL, null=True, verbose_name="храм"
    )

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
    # ostali podaci o detetu
    zivorodjeno = models.BooleanField(verbose_name="живорођено", default=True)
    po_redu = models.CharField(verbose_name="по реду мајци", null=True, blank=True)
    vanbracno = models.BooleanField(verbose_name="ванбрачно", default=False)
    blizanac = models.BooleanField(verbose_name="близанац", default=False)
    ime_blizanca = models.CharField(
        max_length=255, verbose_name="име близанца", null=True, blank=True
    )
    telesna_mana = models.BooleanField(verbose_name="телесна мана", default=False)

    # podaci o svesteniku
    svestenik = models.ForeignKey(
        Svestenik,
        on_delete=models.SET_NULL,
        null=True,
        related_name="свештеник_крститељ",
        verbose_name="свештеник",
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

    history = HistoricalRecords()

    @property
    def ime_deteta(self):
        """Име детета из везаног Osoba objekta."""
        return self.dete.ime if self.dete else ""

    @property
    def prezime_deteta(self):
        """Презиме детета из везаног Osoba objekta."""
        return self.dete.prezime if self.dete else ""

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
        return str(self.otac.zanimanje) if self.otac and self.otac.zanimanje_id else ""

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
        return (
            str(self.majka.zanimanje) if self.majka and self.majka.zanimanje_id else ""
        )

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
        return str(self.kum.zanimanje) if self.kum and self.kum.zanimanje_id else ""

    @property
    def gradjansko_ime_deteta(self):
        """Грађанско име детета из везаног Osoba objekta."""
        return (
            self.dete.gradjansko_ime if self.dete and self.dete.gradjansko_ime else ""
        )

    @property
    def adresa_deteta(self):
        """Адреса детета из везаног Osoba objekta."""
        return self.dete.adresa if self.dete else None

    @property
    def adresa_oca(self):
        """Адреса оца из везаног Osoba objekta."""
        return self.otac.adresa if self.otac else None

    @property
    def adresa_majke(self):
        """Адреса мајке из везаног Osoba objekta."""
        return self.majka.adresa if self.majka else None

    @property
    def adresa_kuma(self):
        """Адреса кума из везаног Osoba objekta."""
        return self.kum.adresa if self.kum else None

    @property
    def adresa_kuma_mesto(self):
        """Место адресе кума из везаног Osoba objekta."""
        return str(self.kum.adresa) if self.kum and self.kum.adresa else ""

    @property
    def get_pol_deteta_display(self):
        """Приказ пола детета."""
        if not self.dete or not self.dete.pol:
            return ""
        return "мушки" if self.dete.pol == "М" else "женски"

    def __str__(self):
        ime = self.ime_deteta or ""
        datum = self.datum or ""
        return f"Крштење {ime} ({datum})" if ime else f"Крштење {self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштење"
        verbose_name_plural = "Крштења"
        ordering = ["-datum"]
        indexes = [
            # Protocol lookup: knjiga/strana/broj scoped by year. Composite
            # serves both filter (find a specific protocol entry) and the
            # natural year-then-page sort with a single index scan.
            models.Index(
                fields=["godina_registracije", "knjiga", "strana", "broj"],
                name="krstenje_protocol_idx",
            ),
        ]
