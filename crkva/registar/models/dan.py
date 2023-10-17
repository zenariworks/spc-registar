"""
Model class for representing slavas in the database.
"""
from django.db import models


class Dan(models.Model):
    dan = models.IntegerField(primary_key=True, unique=True, name="дан")

    def __str__(self):
        return f"{self.дан}"

    class Meta:
        managed = True
        db_table = "дан"
        verbose_name = "Дан"
        verbose_name_plural = "Дани"
