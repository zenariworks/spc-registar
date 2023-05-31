from django.db import models


class hsperror(models.Model):
    err_rbr = models.IntegerField()
    err_dt = models.TextField()
    err_user = models.TextField()
    err_id = models.IntegerField()
    err_mess = models.TextField()
    err_mess1 = models.TextField()
    err_prog = models.TextField()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "errors"
