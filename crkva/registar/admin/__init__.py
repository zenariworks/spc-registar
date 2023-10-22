from django.contrib import admin

from registar.models.domacinstvo import Domacinstvo
from registar.models.krstenje import Krstenje
from registar.models.osoba import Osoba
from registar.models.slava import Slava
from registar.models.svestenik import Svestenik
from registar.models.ukucanin import Ukucanin
from registar.models.ulica import Ulica
from registar.models.vencanje import Vencanje

from .domacinstvo_admin import DomacinstvoAdmin
from .svestenik_admin import SvestenikAdmin
from .krstenje_admin import KrstenjeAdmin
from .slava_admin import SlavaAdmin
from .vencanje_admin import VencanjeAdmin
from .ukucanin_admin import UkucaninAdmin
from .ulica_admin import UlicaAdmin


# Register your models here.
admin.site.register(Domacinstvo, DomacinstvoAdmin)
admin.site.register(Krstenje, KrstenjeAdmin)
admin.site.register(Osoba)
admin.site.register(Slava, SlavaAdmin)
admin.site.register(Svestenik, SvestenikAdmin)
admin.site.register(Ukucanin, UkucaninAdmin)
admin.site.register(Ulica, UlicaAdmin)
admin.site.register(Vencanje, VencanjeAdmin)
