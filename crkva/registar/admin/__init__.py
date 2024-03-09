from django.contrib import admin

from registar.models.adresa import Adresa
from registar.models.crkvena_opstina import CrkvenaOpstina
from registar.models.domacinstvo import Domacinstvo
from registar.models.eparhija import Eparhija
from registar.models.hram import Hram
from registar.models.krstenje import Krstenje
from registar.models.narodnost import Narodnost
from registar.models.parohija import Parohija
from registar.models.parohijan import Parohijan
from registar.models.slava import Slava
from registar.models.svestenik import Svestenik
from registar.models.ukucanin import Ukucanin
from registar.models.ulica import Ulica
from registar.models.vencanje import Vencanje
from registar.models.zanimanje import Zanimanje

from .adresa_admin import AdresaAdmin
from .crkvena_opstina_admin import CrkvenaOpstinaAdmin
from .domacinstvo_admin import DomacinstvoAdmin
from .eparhija_admin import EparhijaAdmin
from .hram_admin import HramAdmin
from .krstenje_admin import KrstenjeAdmin
from .narodnost_admin import NarodnostAdmin
from .parohija_admin import ParohijaAdmin
from .parohijan_admin import ParohijanAdmin
from .slava_admin import SlavaAdmin
from .svestenik_admin import SvestenikAdmin
from .ukucanin_admin import UkucaninAdmin
from .ulica_admin import UlicaAdmin
from .vencanje_admin import VencanjeAdmin
from .zanimanje_admin import ZanimanjeAdmin

admin.site.register(Adresa, AdresaAdmin)
admin.site.register(CrkvenaOpstina, CrkvenaOpstinaAdmin)
admin.site.register(Domacinstvo, DomacinstvoAdmin)
admin.site.register(Eparhija, EparhijaAdmin)
admin.site.register(Hram, HramAdmin)
admin.site.register(Krstenje, KrstenjeAdmin)
admin.site.register(Narodnost, NarodnostAdmin)
admin.site.register(Parohija, ParohijaAdmin)
admin.site.register(Parohijan, ParohijanAdmin)
admin.site.register(Slava, SlavaAdmin)
admin.site.register(Svestenik, SvestenikAdmin)
admin.site.register(Ukucanin, UkucaninAdmin)
admin.site.register(Ulica, UlicaAdmin)
admin.site.register(Vencanje, VencanjeAdmin)
admin.site.register(Zanimanje, ZanimanjeAdmin)
