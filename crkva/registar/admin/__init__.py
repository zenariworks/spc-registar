from django.contrib import admin
from registar.models.domacinstvo import Domacinstvo
from registar.models.eparhija import Eparhija
from registar.models.hram import Hram
from registar.models.krstenje import Krstenje
from registar.models.parohijan import Parohijan
from registar.models.slava import Slava
from registar.models.svestenik import Svestenik
from registar.models.ukucanin import Ukucanin
from registar.models.ulica import Ulica
from registar.models.vencanje import Vencanje
from registar.models.zanimanje import Zanimanje

from .domacinstvo_admin import DomacinstvoAdmin
from .eparhija_admin import EparhijaAdmin
from .hram_admin import HramAdmin
from .krstenje_admin import KrstenjeAdmin
from .parohijan_admin import parohijanAdmin
from .slava_admin import SlavaAdmin
from .svestenik_admin import SvestenikAdmin
from .ukucanin_admin import UkucaninAdmin
from .ulica_admin import UlicaAdmin
from .vencanje_admin import VencanjeAdmin
from .zanimanje_admin import ZanimanjeAdmin

admin.site.register(Domacinstvo, DomacinstvoAdmin)
admin.site.register(Eparhija, EparhijaAdmin)
admin.site.register(Hram, HramAdmin)
admin.site.register(Krstenje, KrstenjeAdmin)
admin.site.register(Parohijan, parohijanAdmin)
admin.site.register(Slava, SlavaAdmin)
admin.site.register(Svestenik, SvestenikAdmin)
admin.site.register(Ukucanin, UkucaninAdmin)
admin.site.register(Ulica, UlicaAdmin)
admin.site.register(Vencanje, VencanjeAdmin)
admin.site.register(Zanimanje, ZanimanjeAdmin)
