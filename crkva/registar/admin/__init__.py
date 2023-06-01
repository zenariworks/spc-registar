from django.contrib import admin

from registar.models.c_domacinstvo import Domacinstvo
from registar.models.c_error import Error
from registar.models.c_krstenje import Krstenje
from registar.models.c_meni import hspmeni
from registar.models.c_pass import Password
from registar.models.c_set import Set
from registar.models.c_slava import Slava
from registar.models.c_svestenik import Svestenik
from registar.models.c_ukucani import Ukucanin
from registar.models.c_ulica import Ulica
from registar.models.c_vencanje import Vencanje

from .c_domacinstvo_admin import DomacinstvoAdmin



# Register your models here.
admin.site.register(Domacinstvo, DomacinstvoAdmin)
admin.site.register(Error)
admin.site.register(Krstenje)
admin.site.register(hspmeni)
admin.site.register(Password)
admin.site.register(Set)
admin.site.register(Svestenik)
admin.site.register(Ukucanin)
admin.site.register(Ulica)
admin.site.register(Vencanje)