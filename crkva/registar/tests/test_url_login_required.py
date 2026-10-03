"""#417: сваки URL, осим изричито јавних, анонимног корисника шаље на пријаву.

Тест обилази цео URLconf (без `admin/`, који има своју пријаву), прави путању са
лажним аргументима и шаље анонимни GET. Нов поглед без заштите обара CI.
"""

import uuid

from django.conf import settings
from django.test import Client, TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.urls.converters import IntConverter, UUIDConverter

JAVNE_RUTE = {"healthz", "readyz", "prijava/"}

LAZNI_ARGUMENTI = {
    IntConverter: 1,
    UUIDConverter: uuid.UUID(int=1),
}


def svi_obrasci(razresivac=None, prefiks=""):
    """Сви парови (рута, образац), рекурзивно, без `admin/`."""
    razresivac = razresivac or get_resolver()
    for obrazac in razresivac.url_patterns:
        ruta = prefiks + str(obrazac.pattern)
        if isinstance(obrazac, URLResolver):
            if not ruta.startswith("admin/"):
                yield from svi_obrasci(obrazac, ruta)
        elif isinstance(obrazac, URLPattern):
            yield ruta, obrazac


def napravi_putanju(ruta, obrazac):
    """Конкретна путања: сваки конвертер добија лажну вредност."""
    putanja = "/" + ruta
    for ime, konverter in obrazac.pattern.converters.items():
        vrsta = type(konverter).__name__.removesuffix("Converter").lower()
        vrednost = konverter.to_url(LAZNI_ARGUMENTI[type(konverter)])
        putanja = putanja.replace(f"<{vrsta}:{ime}>", vrednost)
    return putanja


class UrlLoginRequiredTests(TestCase):
    """Анонимни приступ сваком URL-у."""

    def test_middleware_installed(self):
        """LoginRequiredMiddleware је укључен, после AuthenticationMiddleware."""
        slojevi = settings.MIDDLEWARE
        autentikacija = slojevi.index(
            "django.contrib.auth.middleware.AuthenticationMiddleware"
        )
        obavezna_prijava = slojevi.index(
            "django.contrib.auth.middleware.LoginRequiredMiddleware"
        )
        self.assertGreater(obavezna_prijava, autentikacija)

    def test_private_urls_redirect_to_login(self):
        """Сваки URL ван JAVNE_RUTE анонимног корисника шаље на пријаву."""
        prijava = reverse("login")
        klijent = Client()
        provereno = 0
        for ruta, obrazac in svi_obrasci():
            if ruta in JAVNE_RUTE:
                continue
            putanja = napravi_putanju(ruta, obrazac)
            with self.subTest(putanja=putanja, ime=obrazac.name):
                odgovor = klijent.get(putanja)
                self.assertEqual(odgovor.status_code, 302)
                self.assertTrue(
                    odgovor["Location"].startswith(prijava),
                    f"{putanja} → {odgovor['Location']}",
                )
            provereno += 1
        self.assertGreater(provereno, 40)

    def test_public_urls_stay_public(self):
        """Руте из JAVNE_RUTE (пробе и пријава) раде без пријаве."""
        klijent = Client()
        for ruta in JAVNE_RUTE:
            with self.subTest(ruta=ruta):
                self.assertEqual(klijent.get("/" + ruta).status_code, 200)

    def test_public_list_matches_urlconf(self):
        """Свака рута из JAVNE_RUTE и даље постоји у URLconf-у."""
        rute = {ruta for ruta, _ in svi_obrasci()}
        self.assertEqual(JAVNE_RUTE - rute, set())
