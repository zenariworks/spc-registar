"""Регресиони тестови за калибрисани распоред штампе венчанице (#16).

Координате поља чувамо као CSS променљиве --venc-* у
registar/static/registar/print/vencanica.css. Штитимо:
- да су СВА поља потпуно вођена променљивама (top/left/width/height) —
  раније су ширине/висине биле хардкодоване па их је калибрација игнорисала,
- да назив парохије стоји изнад потписа свештеника у подножју.
"""
# pylint: disable=missing-function-docstring

import os
import re

from django.test import SimpleTestCase

CSS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "static", "registar", "print", "vencanica.css",
)

FIELD_IDS = [
    "knjiga", "strana", "tekuci", "hram", "eparhija", "mesto", "godina",
    "zenik", "nevesta", "roditelji_zenika", "roditelji_neveste",
    "rodjenje_zenika", "rodjenje_neveste", "brak_zenika", "brak_neveste",
    "ispit", "datum_vencanja", "mesto_hram", "svestenik", "svedoci",
    "razresenje", "primedba", "footer_eparhija", "footer_hram",
    "footer_datum", "footer_godina", "footer_mesto", "footer_parohija",
    "footer_paroh",
]


def _var_mm(css, name):
    m = re.search(rf"--venc-{re.escape(name)}:\s*([\d.]+)mm", css)
    assert m, f"CSS променљива --venc-{name} није пронађена"
    return float(m.group(1))


class VencanicaLayoutTests(SimpleTestCase):
    """Распоред венчанице: var-driven геометрија + ред подножја (#16)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(CSS_PATH, encoding="utf-8") as fh:
            cls.css = fh.read()

    def test_each_field_defines_all_four_vars(self):
        for fid in FIELD_IDS:
            for prop in ("top", "left", "width", "height"):
                self.assertIsNotNone(
                    re.search(rf"--venc-{fid}-{prop}:\s*[\d.]+mm", self.css),
                    f"недостаје --venc-{fid}-{prop}",
                )

    def test_field_classes_consume_size_vars(self):
        # Раније су width/height били хардкодовани па калибрација није имала
        # ефекта; сада свако поље користи var(--venc-*-width/height).
        self.assertGreaterEqual(self.css.count("width: var(--venc-"), len(FIELD_IDS))
        self.assertGreaterEqual(self.css.count("height: var(--venc-"), len(FIELD_IDS))
        self.assertNotIn("--venc-table-left", self.css)
        self.assertNotIn("--venc-table-width", self.css)

    def test_parohija_line_is_above_paroh_line(self):
        self.assertLess(
            _var_mm(self.css, "footer_parohija-top"),
            _var_mm(self.css, "footer_paroh-top"),
            "footer_parohija (назив парохије) мора бити изнад footer_paroh (потпис)",
        )

    def test_footer_fields_within_page(self):
        for name in ("footer_paroh-top", "footer_parohija-top"):
            top = _var_mm(self.css, name)
            self.assertTrue(255.0 <= top <= 285.0, f"{name}={top}mm ван зоне подножја")
