from django.db import models


class HSPUKUCANI(models.Model):
    uk_rbr = models.IntegerField()
    uk_rbrdom = models.IntegerField()
    uk_ime = models.TextField()
    uk_akt = models.TextField()
    uk_flag = models.TextField()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "ukucani"
