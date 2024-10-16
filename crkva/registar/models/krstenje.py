"""Модул модела крштења у бази података."""

import uuid

from django.db import models

from .hram import Hram
from .parohijan import Parohijan
from .svestenik import Svestenik


class Krstenje(models.Model):
    """Класа која представља крштења."""

    # redni_broj_krstenja_tekuca_godina, 
    # godina_krstenja, datum_krstenja,
    # knjiga_krstenja, 
    # broj_krstenja, 
    # strana_krstenja,
    # adresa_deteta_grad, 
    # adresa_deteta_ulica, 
    # adresa_deteta_broj,
    # godina_rodjenja,
    # mesec_rodjenja, 
    # dan_rodjenja, 
    # vreme_rodjenja, 
    # mesto_rodjenja,
    # godina_krstenja, 
    # mesec_krstenja, 
    # dan_krstenja, 
    # vreme_krstenja, 
    # mesto_krstenja, 
    # hram_krstenja, 
    # ime_deteta, 
    # gradjansko_ime_deteta, 
    # pol_deteta, 
    # ime_oca, 
    # prezime_oca, 
    # zanimanje_oca,
    # adresa_oca_mesto,
    # veroispovest_oca,
    # narodnost_oca,
    # ime_majke, 
    # prezime_majke, 
    # zanimanje_majke,
    # adresa_majke_mesto,
    # veroispovest_majke,
    # dete_rodjeno_zivo, 
    # dete_po_redu_po_majci, 
    # dete_vanbracno, 
    # dete_blizanac, 
    # drugo_dete_blizanac, 
    # dete_sa_telesnom_manom,
    # svestenik_id, 
    # ime_prezime_svestenika, 
    # zvanje_svestenika, 
    # parohija_id, 
    # ime_kuma, 
    # prezime_kuma, 
    # zanimanje_kuma, 
    # adresa_kuma_mesto,
    # mesto_registracije, 
    # datum_registracije, 
    # maticni_broj, 
    # strana_registracije

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    redni_broj_krstenja_tekuca_godina = models.IntegerField(verbose_name="редни број крштења текућа година")
    # godina_krstenja = models.IntegerField(verbose_name="година крштења") 
    # datum_krstenja = models.DateField(verbose_name="датум крштења", null=True, blank=True)
    knjiga_krstenja = models.IntegerField(verbose_name="књига крштења") 
    broj_krstenja = models.IntegerField(verbose_name="број крштења") 
    strana_krstenja = models.IntegerField(verbose_name="страна крштења")

    # adresa_deteta_grad = models.CharField(max_length=255, verbose_name="адреса детета град")
    # adresa_deteta_ulica = models.CharField(max_length=255, verbose_name="адреса детета улица", null=True, blank=True)
    # adresa_deteta_broj = models.CharField(max_length=255, verbose_name="адреса детета број", null=True, blank=True)
    # godina_rodjenja = models.IntegerField(verbose_name="година рођења")
    # mesec_rodjenja = models.IntegerField(verbose_name="месец рођења")
    # dan_rodjenja = models.IntegerField(verbose_name="дан рођења")
    # vreme_rodjenja, 
    # mesto_rodjenja,
    
    datum_krstenja = models.DateField(verbose_name="датум крштења")
    vreme_krstenja = models.TimeField(verbose_name="време крштења", null=True, blank=True)



    # mesto_krstenja, 
    # hram_krstenja, 
    # ime_deteta, 
    # gradjansko_ime_deteta, 
    # pol_deteta, 
    # ime_oca, 
    # prezime_oca, 
    # zanimanje_oca,
    # adresa_oca_mesto,
    # veroispovest_oca,
    # narodnost_oca,
    # ime_majke, 
    # prezime_majke, 
    # zanimanje_majke,
    # adresa_majke_mesto,
    # veroispovest_majke,
    # dete_rodjeno_zivo, 
    # dete_po_redu_po_majci, 
    # dete_vanbracno, 
    # dete_blizanac, 
    # drugo_dete_blizanac, 
    # dete_sa_telesnom_manom,
    # svestenik_id, 
    # ime_prezime_svestenika, 
    # zvanje_svestenika, 
    # parohija_id, 
    # ime_kuma, 
    # prezime_kuma, 
    # zanimanje_kuma, 
    # adresa_kuma_mesto,
    # mesto_registracije, 
    # datum_registracije, 
    # maticni_broj, 
    # strana_registracije




    hram = models.ForeignKey(
        Hram, on_delete=models.SET_NULL, null=True, verbose_name="место крштења"
    )

    dete = models.ForeignKey(
        Parohijan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="дете",
        verbose_name="дете",
    )
    dete_majci = models.IntegerField(verbose_name="дете по реду (по мајци)")
    dete_bracno = models.BooleanField(verbose_name="брачно дете")
    mana = models.BooleanField(verbose_name="мана")
    blizanac = models.ForeignKey(
        Parohijan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="близанац",
        verbose_name="близанац",
    )

    otac = models.ForeignKey(
        Parohijan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="отац",
        verbose_name="отац",
    )
    majka = models.ForeignKey(
        Parohijan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="мајка",
        verbose_name="мајка",
    )
    svestenik = models.ForeignKey(
        Svestenik,
        on_delete=models.SET_NULL,
        null=True,
        related_name="свештеник_крститељ",
        verbose_name="свештеник",
    )
    kum = models.ForeignKey(
        Parohijan,
        on_delete=models.SET_NULL,
        null=True,
        related_name="кум",
        verbose_name="кум",
    )

    primedba = models.TextField(blank=True, null=True, verbose_name="примедба")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
