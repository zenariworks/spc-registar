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
    """Подножје: назив парохије иде на ред „парохије“ (горњи), потпис
    свештеника на доњи ред; „Парох“ је само наслов изнад."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(CSS_PATH, encoding="utf-8") as fh:
            cls.css = fh.read()

    def test_parohija_line_is_above_paroh_line(self):
        # На обрасцу: наслов „Парох“, испод њега ред „парохије [назив]“
        # (горњи), па потпис свештеника (доњи). Дакле назив парохије мора
        # бити ИЗНАД потписа свештеника — мањи top значи виши положај.
        paroh_top = _var_mm(self.css, "footer_paroh-top")
        parohija_top = _var_mm(self.css, "footer_parohija-top")
        self.assertLess(
            parohija_top,
            paroh_top,
            "footer_parohija (назив парохије) мора бити изнад footer_paroh (потпис), #17",
        )

    def test_footer_fields_within_page(self):
        # Оба реда су у зони подножја А4 стране (255–285mm), не ван папира.
        for name in ("footer_paroh-top", "footer_parohija-top"):
            top = _var_mm(self.css, name)
            self.assertTrue(255.0 <= top <= 285.0, f"{name}={top}mm ван зоне подножја")
