from django.contrib import admin

from registar.models.domacinstvo import Domacinstvo
from registar.models.error import Error
from registar.models.krstenje import Krstenje
from registar.models.menu import Menu
from registar.models.password import Password
from registar.models.set import Set
from registar.models.slava import Slava
from registar.models.svestenik import Svestenik
from registar.models.ukucanin import Ukucanin
from registar.models.ulica import Ulica
from registar.models.vencanje import Vencanje

from .c_domacinstvo_admin import DomacinstvoAdmin



# Register your models here.
admin.site.register(Domacinstvo, DomacinstvoAdmin)
admin.site.register(Error)
admin.site.register(Krstenje)
admin.site.register(Menu)
admin.site.register(Password)
admin.site.register(Set)
admin.site.register(Slava)
admin.site.register(Svestenik)
admin.site.register(Ukucanin)
admin.site.register(Ulica)
admin.site.register(Vencanje)
