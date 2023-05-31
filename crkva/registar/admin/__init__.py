from django.contrib import admin

from registar.models.c_domacinstvo import HSPDOMACINI
from registar.models.c_error import hsperror
from registar.models.c_krstenje import HSPKRST
from registar.models.c_meni import hspmeni
from registar.models.c_pass import HSPPASS
from registar.models.c_set import hspset
from registar.models.c_slava import hspslave
from registar.models.c_svestenik import HSPSVEST
from registar.models.c_ukucani import HSPUKUCANI
from registar.models.c_ulica import HSPULICE
from registar.models.c_vencanje import HSPVENC

from .c_domacinstvo_admin import DomacinstvoAdmin



# Register your models here.
admin.site.register(HSPDOMACINI, DomacinstvoAdmin)
admin.site.register(hsperror)
admin.site.register(HSPKRST)
admin.site.register(hspmeni)
admin.site.register(HSPPASS)
admin.site.register(hspset)
admin.site.register(HSPSVEST)
admin.site.register(HSPUKUCANI)
admin.site.register(HSPULICE)
admin.site.register(HSPVENC)