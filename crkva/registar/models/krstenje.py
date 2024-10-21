"""Модул модела крштења у бази података."""

import uuid

from django.db import models

from .hram import Hram
from .svestenik import Svestenik


class Krstenje(models.Model):
    """Класа која представља крштења."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    # tekuca godina i redni broj krstenja u godini
    redni_broj_krstenja_tekuca_godina = models.IntegerField(verbose_name="редни број крштења текућа година")
    krstenje_tekuca_godina = models.IntegerField(verbose_name="крштењe текућа година")

    # podaci za registar(protokol) krstenih
    knjiga = models.IntegerField(verbose_name="књига крштења") 
    broj = models.IntegerField(verbose_name="број крштења") 
    strana = models.IntegerField(verbose_name="страна крштења")

    # podaci o krstenju
    datum = models.DateField(verbose_name="датум крштења")
    vreme = models.TimeField(verbose_name="време крштења", null=True, blank=True)
    mesto = models.CharField(max_length=255, verbose_name="место крштења", null=True, blank=True)
    hram = models.ForeignKey(
        Hram, on_delete=models.SET_NULL, null=True, verbose_name="место крштења"
    )

    # podaci o detetu
    adresa_deteta_grad = models.CharField(max_length=255, verbose_name="адреса детета град")
    adresa_deteta_ulica = models.CharField(max_length=255, verbose_name="адреса детета улица", null=True, blank=True)
    adresa_deteta_broj = models.CharField(max_length=255, verbose_name="адреса детета број", null=True, blank=True)
    datum_rodjenja = models.DateField(verbose_name="датум рођења")
    vreme_rodjenja = models.TimeField(verbose_name="време рођења", null=True, blank=True)
    mesto_rodjenja = models.CharField(max_length=255, verbose_name="место рођења", null=True, blank=True)
    ime_deteta = models.CharField(max_length=255, verbose_name="име детета")
    gradjansko_ime_deteta = models.CharField(max_length=255, verbose_name="грађанско име детета", null=True, blank=True)
    pol_deteta = models.CharField(max_length=255, verbose_name="пол детета", null=True, blank=True) 

    # podaci o roditeljima
    ime_oca = models.CharField(max_length=255, verbose_name="име оца") 
    prezime_oca = models.CharField(max_length=255, verbose_name="презиме оца") 
    zanimanje_oca = models.CharField(max_length=255, verbose_name="занимање оца", null=True, blank=True)
    adresa_oca_mesto = models.CharField(max_length=255, verbose_name="адреса оца место", null=True, blank=True)
    veroispovest_oca = models.CharField(max_length=255, verbose_name="вероисповест оца", null=True, blank=True)
    narodnost_oca = models.CharField(max_length=255, verbose_name="народност оца", null=True, blank=True)
    
    ime_majke = models.CharField(max_length=255, verbose_name="име мајке") 
    prezime_majke = models.CharField(max_length=255, verbose_name="презиме мајке")
    zanimanje_majke = models.CharField(max_length=255, verbose_name="занимање мајке", null=True, blank=True)
    adresa_majke_mesto = models.CharField(max_length=255, verbose_name="адреса мајке место", null=True, blank=True)
    veroispovest_majke = models.CharField(max_length=255, verbose_name="вероисповест мајке", null=True, blank=True)
    
    # ostali podaci o detetu
    dete_rodjeno_zivo = models.BooleanField(verbose_name="дете рођено живо") 
    dete_po_redu_po_majci = models.CharField(verbose_name="дете по реду (по мајци)", null=True, blank=True)
    dete_vanbracno = models.BooleanField(verbose_name="ванбрачно дете") 
    dete_blizanac = models.BooleanField(verbose_name="дете близанац") 
    drugo_dete_blizanac_ime = models.CharField(max_length=255, verbose_name="име другог детета близанца", null=True, blank=True)
    dete_sa_telesnom_manom = models.BooleanField(verbose_name="дете са телесном маном")
    
    # podaci o svesteniku
    svestenik = models.ForeignKey(
        Svestenik,
        on_delete=models.SET_NULL,
        null=True,
        related_name="свештеник_крститељ",
        verbose_name="свештеник",
    )

    # podaci o kumu
    ime_kuma = models.CharField(max_length=255, verbose_name="име кума") 
    prezime_kuma = models.CharField(max_length=255, verbose_name="презиме кума") 
    zanimanje_kuma = models.CharField(max_length=255, verbose_name="занимање кума", null=True, blank=True) 
    adresa_kuma_mesto = models.CharField(max_length=255, verbose_name="адреса кума место", null=True, blank=True)
    
    # podaci iz matične knjige - anagraf
    mesto_registracije = models.CharField(max_length=255, verbose_name="место регистрације", null=True, blank=True) 
    datum_registracije = models.DateField(verbose_name="датум регистрације", null=True, blank=True) 
    maticni_broj = models.CharField(max_length=255, verbose_name="матични број", null=True, blank=True) 
    strana_registracije = models.CharField(max_length=255, verbose_name="страна регистрације", null=True, blank=True)

    #anagraf = models.TextField(verbose_name="анаграф", null=True, blank=True)
    primedba = models.TextField(blank=True, null=True, verbose_name="примедба")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
