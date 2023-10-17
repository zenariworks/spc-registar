"""
Model class for representing errors in the database.
"""
import uuid

from django.db import models


class Error(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    dt = models.TextField()
    user = models.TextField()
    id = models.IntegerField()
    mess = models.TextField()
    mess1 = models.TextField()
    prog = models.TextField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "errors"
        verbose_name = "Грешка"
        verbose_name_plural = "Грешке"
