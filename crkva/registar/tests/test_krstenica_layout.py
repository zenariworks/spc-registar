"""Регресиони тестови за калибрисани распоред штампе крштенице (#17).

Координате поља се чувају као CSS променљиве `--krst-*` у
`registar/static/registar/print/krstenica.css`. Овде штитимо
кључне односе који су раније били погрешни (нпр. замена редова
„Парох“ и „парохије“ у подножју).
"""

import os
import re

from django.test import SimpleTestCase

CSS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "static",
    "registar",
    "print",
    "krstenica.css",
)


def _var_mm(css: str, name: str) -> float:
    """Враћа вредност `--krst-<name>` у милиметрима."""
    m = re.search(rf"--krst-{re.escape(name)}:\s*([\d.]+)mm", css)
    assert m, f"CSS променљива --krst-{name} није пронађена"
    return float(m.group(1))


class KrstenicaFooterLayoutTests(SimpleTestCase):
    """Подножје: име свештеника иде на ред „Парох“, парохија на ред „парохије“."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(CSS_PATH, encoding="utf-8") as fh:
            cls.css = fh.read()

    def test_paroh_line_is_above_parohija_line(self):
        # Ред „Парох“ (име свештеника) мора бити ИЗНАД реда „парохије“
        # (назив парохије) — мањи top значи виши положај на страни.
        paroh_top = _var_mm(self.css, "footer_paroh-top")
        parohija_top = _var_mm(self.css, "footer_parohija-top")
        self.assertLess(
            paroh_top,
            parohija_top,
            "footer_paroh мора бити изнад footer_parohija (били су замењени, #17)",
        )

    def test_footer_fields_within_page(self):
        # Оба реда су у зони подножја А4 стране (255–285mm), не ван папира.
        for name in ("footer_paroh-top", "footer_parohija-top"):
            top = _var_mm(self.css, name)
            self.assertTrue(
                255.0 <= top <= 285.0, f"{name}={top}mm ван зоне подножја"
            )
