"""WeasyPrint render smoke — ре-верификација за Django 6 (#304).

PDF преписи иду кроз WeasyPrint (``registar/views/pdf.py``). WeasyPrint
62.3 је закуцан уз ``pydyf < 0.12``; овај тест потврђује да рендеровање и
даље даје валидан PDF на текућем стеку (Django 6), независно од погледа.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.test import SimpleTestCase
from weasyprint import HTML


class WeasyPrintRenderTests(SimpleTestCase):
    def test_renders_pdf_bytes(self):
        pdf = HTML(string="<h1>Тест</h1>").write_pdf()
        self.assertTrue(pdf.startswith(b"%PDF"))
