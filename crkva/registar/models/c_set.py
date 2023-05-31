from django.db import models


class hspset(models.Model):
    hsp_godina = models.IntegerField()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "sets"