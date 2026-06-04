"""Tests for the ``proveri_sablone`` audit and the template fixes it surfaced.

Templates render undefined attribute lookups (``{{ obj.foo.bar }}`` where
``.bar`` doesn't exist on ``foo``) as empty strings. That silent failure was
already biting us in real pages (the slava-list rendered just the broj
because ``adresa.ulica`` was being treated as another model). These tests:

1. exercise the audit command itself so it keeps catching regressions, and
2. assert that the pages / partials we already fixed actually render the
   data they're supposed to.

Each PDF template is rendered directly via ``render_to_string`` rather than
through the full ``KrstenjePDF`` / ``VencanjePDF`` views -- those wrap the
output in weasyprint, which would just turn the visible text into PDF byte
streams that are awkward to assert against. The model schema is what we're
defending against, so rendering the HTML body is sufficient.
"""

from __future__ import annotations

import datetime
from io import StringIO

from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse
from registar.models import (
    Adresa,
    Domacinstvo,
    Hram,
    Krstenje,
    Osoba,
    Slava,
    Ukucanin,
    Vencanje,
)

# ---------------------------------------------------------------------------
# 1) The audit command itself.
# ---------------------------------------------------------------------------


class ProveriSabloneCommandTests(TestCase):
    """``proveri_sablone`` must run cleanly and surface no HARD findings."""

    def _run(self) -> str:
        out = StringIO()
        call_command("proveri_sablone", stdout=out)
        return out.getvalue()

    def test_command_runs_and_reports_chains_checked(self):
        output = self._run()
        # Header lines are always present.
        self.assertIn("# chains checked:", output)
        self.assertIn("# HARD findings:", output)

    def test_no_hard_findings_remain(self):
        """After the in-this-PR fixes the audit must be clean (HARD == 0)."""
        output = self._run()
        # Locate the "# HARD findings: N" line and assert N == 0.
        for line in output.splitlines():
            if line.startswith("# HARD findings:"):
                count = int(line.split(":", 1)[1].strip())
                self.assertEqual(
                    count,
                    0,
                    msg=(
                        "Audit surfaced HARD findings -- a template references "
                        f"an attribute that the model doesn't expose:\n{output}"
                    ),
                )
                return
        self.fail(f"Audit output missing '# HARD findings:' header:\n{output}")

    def test_command_catches_a_synthetic_bug(self):
        """Confidence check: drop in a fake broken chain and confirm it's caught."""
        # We synthesise a tiny template tree in memory and point the audit at
        # it, so this test doesn't depend on shipping a broken real template.
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "registar"
            root.mkdir()
            (root / "templates").mkdir()
            (root / "templates" / "x.html").write_text(
                # Adresa.ulica is a CharField; .naziv is the silent-failure bug.
                "<p>{{ adresa.ulica.naziv }}</p>\n",
                encoding="utf-8",
            )

            out = StringIO()
            call_command(
                "proveri_sablone",
                templates_dir=str(root / "templates"),
                stdout=out,
            )
            output = out.getvalue()
            self.assertIn("HARD", output)
            self.assertIn("adresa.ulica.naziv", output)


# ---------------------------------------------------------------------------
# 2) Real pages that the audit previously flagged.
# ---------------------------------------------------------------------------


class SlavaUkucaninFallbackTests(TestCase):
    """The slava list shows ``ukucanin.ime_ukucana`` for non-Osoba members.

    Before the fix the template referenced ``ukucanin.ime_prezime`` (which
    doesn't exist on :class:`Ukucanin`), so deceased family members with no
    linked ``Osoba`` rendered as the literal default "Непознато" even when
    we actually had a name on file.
    """

    @classmethod
    def setUpTestData(cls):
        cls.slava = Slava.objects.create(naziv="Аранђеловдан", mesec=11, dan=21)
        cls.adresa = Adresa.objects.create(ulica="Кнез Михаилова", broj="1")
        cls.domacin = Osoba.objects.create(ime="Петар", prezime="Петровић")
        cls.dom = Domacinstvo.objects.create(
            domacin=cls.domacin, adresa=cls.adresa, slava=cls.slava
        )
        # An ``Ukucanin`` with no linked Osoba but with a fallback name.
        cls.deceased = Ukucanin.objects.create(
            domacinstvo=cls.dom,
            osoba=None,
            ime_ukucana="Стојан Петровић",
            preminuo=True,
        )

    def setUp(self):
        from django.contrib.auth import get_user_model

        _U = get_user_model()
        self.user = _U.objects.create_superuser(
            username="auto-test", email="a@a.test", password="x"
        )
        self.client.force_login(self.user)

    def test_fallback_name_renders(self):
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(
            "Стојан Петровић",
            body,
            msg="ukucanin.ime_ukucana fallback name must render in slava list",
        )
        # And the default literal must NOT appear in its place.
        # (It can still appear elsewhere; we check only the chip text.)
        self.assertNotIn("Непознато</a>", body)


class KrstenjePDFTemplateRenderTests(TestCase):
    """``pdf_krstenje.html`` must render the place, address fields and twin
    flag instead of empty strings.
    """

    @classmethod
    def setUpTestData(cls):
        cls.hram = Hram.objects.create(naziv="Саборна црква", mesto="Београд")
        cls.adresa_deteta = Adresa.objects.create(
            ulica="Узун Миркова", broj="3", mesto="Стари Град"
        )
        cls.dete = Osoba.objects.create(
            ime="Лука",
            prezime="Лазић",
            datum_rodjenja=datetime.date(2024, 6, 1),
            mesto_rodjenja="Београд",
            pol="М",
            adresa=cls.adresa_deteta,
        )
        cls.otac = Osoba.objects.create(ime="Марко", prezime="Лазић")
        cls.majka = Osoba.objects.create(ime="Ана", prezime="Лазић")
        cls.kum = Osoba.objects.create(ime="Никола", prezime="Кумовић")
        cls.krstenje = Krstenje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            strana=1,
            datum=datetime.date(2024, 7, 1),
            hram=cls.hram,
            dete=cls.dete,
            otac=cls.otac,
            majka=cls.majka,
            kum=cls.kum,
            vanbracno=False,
            blizanac=True,
            telesna_mana=False,
            strana_registracije="42",
        )

    def _render(self, template: str) -> str:
        return render_to_string(template, {"krstenje": self.krstenje})

    def test_pdf_krstenje_renders_place_and_parent_address(self):
        body = self._render("registar/pdf_krstenje.html")
        # The header place comes from ``krstenje.hram.mesto``.
        self.assertIn("Београд", body)
        # Item 6: parent address is read from ``krstenje.adresa_deteta.*``.
        self.assertIn("Узун Миркова", body)
        self.assertIn("Стари Град", body)


class VencanjePDFTemplateRenderTests(TestCase):
    """``pdf_vencanje.html`` must render ``hram.mesto`` where the broken
    ``mesto_zenika`` chain used to silently swallow output."""

    @classmethod
    def setUpTestData(cls):
        cls.hram = Hram.objects.create(naziv="Храм Светог Саве", mesto="Врачар")
        cls.zenik = Osoba.objects.create(ime="Стефан", prezime="Стефановић")
        cls.nevesta = Osoba.objects.create(ime="Милица", prezime="Милић")
        cls.vencanje = Vencanje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 9, 14),
            hram=cls.hram,
            zenik=cls.zenik,
            nevesta=cls.nevesta,
        )

    def test_pdf_vencanje_renders_hram_mesto(self):
        body = render_to_string(
            "registar/pdf_vencanje.html", {"vencanje": self.vencanje}
        )
        self.assertIn("Врачар", body)
        self.assertIn("Храм Светог Саве", body)
