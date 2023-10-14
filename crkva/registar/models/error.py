"""
Model class for representing errors in the database.
"""
from django.db import models


class Error(models.Model):
    err_rbr = models.IntegerField()
    err_dt = models.TextField()
    err_user = models.TextField()
    err_id = models.IntegerField()
    err_mess = models.TextField()
    err_mess1 = models.TextField()
    err_prog = models.TextField()

    def __str__(self):
        return f"{self.err_rbr}"

    class Meta:
        managed = True
        db_table = "errors"
        verbose_name = "Грешка"
        verbose_name_plural = "Грешке"
