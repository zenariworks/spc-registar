"""#223: продукцијско безбедносно учвршћивање не сме да се укључи усред тестова.

Гејт `_RUNNING_TESTS` у settings.py држи SSL-redirect, secure-cookies и
рестриктиван ALLOWED_HOSTS искљученим док траје тест-рун (иначе би сви
client тестови добијали 301 / 400). Овај тест чува тај гејт.
"""

# pylint: disable=missing-function-docstring

import os

from django.conf import settings
from django.test import SimpleTestCase


class SecurityHardeningGatingTests(SimpleTestCase):
    def test_ssl_redirect_off_during_tests(self):
        self.assertFalse(getattr(settings, "SECURE_SSL_REDIRECT", False))

    def test_secure_cookies_off_during_tests(self):
        self.assertFalse(getattr(settings, "SESSION_COOKIE_SECURE", False))
        self.assertFalse(getattr(settings, "CSRF_COOKIE_SECURE", False))

    def test_allowed_hosts_permissive_during_tests(self):
        # Гејт држи хостове пермисивним усред тестова. Ако env не задаје
        # ALLOWED_HOSTS, fallback је ["*"]; ако задаје (нпр. .env на
        # серверу), ти хостови морају бити присутни. У оба случаја
        # test client (testserver, који Django сам додаје) пролази.
        env_hosts = list(filter(None, os.environ.get("ALLOWED_HOSTS", "").split(",")))
        if env_hosts:
            for host in env_hosts:
                self.assertIn(host, settings.ALLOWED_HOSTS)
        else:
            self.assertIn("*", settings.ALLOWED_HOSTS)

    def test_proxy_ssl_header_always_set(self):
        # Не зависи од DEBUG-а: треба и у dev/тесту иза reverse-proxy-ја.
        self.assertEqual(
            settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https")
        )
