"""
Модул модела крштења у бази података.
"""

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from ._osoba_polja import naziv_polja_osobe, polje_osobe, popunjeno_polje_osobe
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
        Hram, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="храм"
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
    zivorodjeno = models.BooleanField(verbose_name="живорођено", default=True)
    po_redu = models.PositiveSmallIntegerField(
        verbose_name="по реду мајци",
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Колико је дете по реду рођења мајци (1 = прво). Празно = није уписано.",
    )
    vanbracno = models.BooleanField(verbose_name="ванбрачно", default=False)
    blizanac = models.BooleanField(verbose_name="близанац", default=False)
    ime_blizanca = models.CharField(
        max_length=255, verbose_name="име близанца", null=True, blank=True
    )
    telesna_mana = models.BooleanField(verbose_name="телесна мана", default=False)

    svestenik = models.ForeignKey(
        Svestenik,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="свештеник_крститељ",
        verbose_name="свештеник",
    )

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

    history = HistoricalRecords(user_db_constraint=False)

    ime_deteta = polje_osobe("dete", "ime", opis="Име детета.")
    prezime_deteta = polje_osobe("dete", "prezime", opis="Презиме детета.")
    pol_deteta = polje_osobe("dete", "pol", opis="Пол детета.")
    datum_rodjenja = polje_osobe(
        "dete", "datum_rodjenja", prazno=None, opis="Датум рођења детета."
    )
    vreme_rodjenja = polje_osobe("dete", "vreme_rodjenja", opis="Време рођења детета.")
    mesto_rodjenja = polje_osobe("dete", "mesto_rodjenja", opis="Место рођења детета.")
    gradjansko_ime_deteta = popunjeno_polje_osobe(
        "dete", "gradjansko_ime", opis="Грађанско име детета."
    )
    adresa_deteta = polje_osobe("dete", "adresa", prazno=None, opis="Адреса детета.")

    ime_oca = polje_osobe("otac", "ime", opis="Име оца.")
    prezime_oca = polje_osobe("otac", "prezime", opis="Презиме оца.")
    zanimanje_oca = naziv_polja_osobe("otac", "zanimanje", opis="Занимање оца.")
    veroispovest_oca = popunjeno_polje_osobe(
        "otac", "veroispovest", opis="Вероисповест оца."
    )
    narodnost_oca = popunjeno_polje_osobe("otac", "narodnost", opis="Народност оца.")
    adresa_oca = polje_osobe("otac", "adresa", prazno=None, opis="Адреса оца.")

    ime_majke = polje_osobe("majka", "ime", opis="Име мајке.")
    prezime_majke = polje_osobe("majka", "prezime", opis="Презиме мајке.")
    zanimanje_majke = naziv_polja_osobe("majka", "zanimanje", opis="Занимање мајке.")
    veroispovest_majke = popunjeno_polje_osobe(
        "majka", "veroispovest", opis="Вероисповест мајке."
    )
    narodnost_majke = popunjeno_polje_osobe(
        "majka", "narodnost", opis="Народност мајке."
    )
    adresa_majke = polje_osobe("majka", "adresa", prazno=None, opis="Адреса мајке.")

    ime_kuma = polje_osobe("kum", "ime", opis="Име кума.")
    prezime_kuma = polje_osobe("kum", "prezime", opis="Презиме кума.")
    zanimanje_kuma = naziv_polja_osobe("kum", "zanimanje", opis="Занимање кума.")
    adresa_kuma = polje_osobe("kum", "adresa", prazno=None, opis="Адреса кума.")
    mesto_kuma = naziv_polja_osobe("kum", "adresa", opis="Адреса кума као текст.")

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
        constraints = [
            # Протоколарни број је званична гаранција јединствености уписа:
            # у оквиру једне године регистрације редни број мора бити
            # јединствен. (knjiga, strana, broj) се намерно НЕ ограничава —
            # постојећи подаци садрже легитимна понављања физичке локације.
            models.UniqueConstraint(
                fields=["godina_registracije", "redni_broj"],
                name="krstenje_god_redni_uniq",
                violation_error_message=(
                    "Крштење са овим редним бројем у датој години "
                    "регистрације већ постоји."
                ),
            ),
        ]
        indexes = [
            # Protocol lookup: knjiga/strana/broj scoped by year. Composite
            # serves both filter (find a specific protocol entry) and the
            # natural year-then-page sort with a single index scan.
            models.Index(
                fields=["godina_registracije", "knjiga", "strana", "broj"],
                name="krstenje_protocol_idx",
            ),
        ]
