from django.db import models

class Adresa(models.Model):

    ulica = models.CharField(max_length=100, verbose_name="улица")
    mesto = models.CharField(max_length=100, verbose_name="место")
    opstina = models.CharField(max_length=100, verbose_name="општина")
    postanski_broj = models.CharField(max_length=10, verbose_name="поштански број")
    drzava = models.CharField(max_length=100, verbose_name="држава")

    def __str__(self):
        return f"{self.ulica}, {self.mesto}, {self.opstina}, {self.postanski_broj}, {self.drzava}"

    class Meta:
        managed = True
        db_table = "adrese"
        verbose_name = "Адреса"
        verbose_name_plural = "Адресе"