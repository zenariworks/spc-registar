"""#417: сваки URL, осим изричито јавних, анонимног корисника шаље на пријаву.

Тест обилази цео URLconf (без `admin/`, који има своју пријаву), прави URL са
лажним аргументима и шаље анонимни GET. Нов поглед без заштите обара CI.
"""

import uuid

from django.conf import settings
from django.test import Client, TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.urls.converters import IntConverter, UUIDConverter

# Погледи који морају остати доступни без пријаве (по путањи без аргумената).
JAVNI = {
    "healthz",  # liveness проба
    "readyz",  # readiness проба
    "prijava/",  # пријава
}

LAZNI_ARGUMENTI = {
    IntConverter: 1,
    UUIDConverter: uuid.UUID(int=1),
}


def url_obrasci(resolver=None, prefiks=""):
    """Сви (путања, образац) парови, рекурзивно, без `admin/`."""
    resolver = resolver or get_resolver()
    for obrazac in resolver.url_patterns:
        ruta = prefiks + str(obrazac.pattern)
        if isinstance(obrazac, URLResolver):
            if ruta.startswith("admin/"):
                continue
            yield from url_obrasci(obrazac, ruta)
        elif isinstance(obrazac, URLPattern):
            yield ruta, obrazac


def napravi_url(ruta, obrazac):
    """Конкретан URL: сваки конвертер добија лажну вредност."""
    url = "/" + ruta
    for ime, konverter in obrazac.pattern.converters.items():
        vrednost = LAZNI_ARGUMENTI[type(konverter)]
        oznaka = f"<{type(konverter).__name__.removesuffix('Converter').lower()}:{ime}>"
        url = url.replace(oznaka, konverter.to_url(vrednost))
    return url


class UrlLoginRequiredTests(TestCase):
    """Анонимни приступ сваком URL-у."""

    def test_middleware_installed(self):
        """LoginRequiredMiddleware је укључен, после AuthenticationMiddleware."""
        mw = settings.MIDDLEWARE
        auth = mw.index("django.contrib.auth.middleware.AuthenticationMiddleware")
        login = mw.index("django.contrib.auth.middleware.LoginRequiredMiddleware")
        self.assertGreater(login, auth)

    def test_private_urls_redirect_to_login(self):
        """Сваки URL ван списка JAVNI анонимног корисника шаље на пријаву."""
        prijava = reverse("login")
        client = Client()
        provereno = 0
        for ruta, obrazac in url_obrasci():
            if ruta in JAVNI:
                continue
            url = napravi_url(ruta, obrazac)
            with self.subTest(url=url, name=obrazac.name):
                response = client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    response["Location"].startswith(prijava),
                    f"{url} → {response['Location']}",
                )
            provereno += 1
        self.assertGreater(provereno, 40)

    def test_public_urls_stay_public(self):
        """URL-ови са списка JAVNI раде без пријаве."""
        client = Client()
        for ruta in JAVNI:
            with self.subTest(ruta=ruta):
                self.assertEqual(client.get("/" + ruta).status_code, 200)

    def test_public_list_matches_urlconf(self):
        """Сваки унос у JAVNI и даље постоји у URLconf-у (без застарелих)."""
        rute = {ruta for ruta, _ in url_obrasci()}
        self.assertEqual(JAVNI - rute, set())
