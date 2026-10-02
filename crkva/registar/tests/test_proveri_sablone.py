"""Јединични тестови за ревизију шаблона (proveri_sablone)."""

import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase
from registar.management.commands import proveri_sablone as ps
from registar.models import Adresa, Domacinstvo, Osoba, Svestenik


class IterChainsTests(SimpleTestCase):
    """Издвајање ланаца из шаблона."""

    def chains(self, text):
        """Ланци са бројем линије и типовима петљи."""
        return list(ps.iter_chains_with_lines(text))

    def test_variable_filters_are_dropped(self):
        """Филтери и њихови аргументи нису ланци."""
        self.assertEqual(self.chains('{{ a.b|default:"x.y"|lower }}'), [(1, "a.b", {})])

    def test_tag_bodies_are_scanned_with_line_numbers(self):
        """И тагови носе ланце; број линије прати положај."""
        self.assertEqual(
            self.chains("x\n{% if a.b and c.d %}"),
            [(2, "a.b", {}), (2, "c.d", {})],
        )

    def test_for_binds_collection_type(self):
        """Позната колекција типизује променљиву петље."""
        self.assertEqual(
            self.chains("{% for k in krstenja %}{{ k.dete }}"),
            [(1, "k.dete", {"k": "Krstenje"})],
        )

    def test_for_falls_back_to_known_root_name(self):
        """Непозната колекција: име променљиве из табеле коренова."""
        result = self.chains("{% for kum, x in a.b %}{{ kum.ime }}")
        self.assertEqual(result[-1], (1, "kum.ime", {"kum": "Osoba"}))

    def test_untyped_loop_var_stays_unbound(self):
        """Непозната колекција и непознато име остају без типа."""
        self.assertEqual(self.chains("{% for x in a.b %}")[-1][2], {})


class StepTests(SimpleTestCase):
    """Један корак по моделу."""

    def test_relations(self):
        """FK је модел, обратна веза је queryset."""
        self.assertEqual(ps.step(Osoba, "adresa"), ("model", Adresa))
        self.assertEqual(ps.step(Svestenik, "adrese"), ("queryset", Adresa))

    def test_scalar_field(self):
        """Обично поље враћа само поље."""
        kind, field = ps.step(Adresa, "ulica")
        self.assertEqual((kind, field.name), ("scalar", "ulica"))

    def test_builtins_and_annotations(self):
        """pk је скалар; prefetched_* и списак живих чланова су queryset."""
        self.assertEqual(ps.step(Osoba, "pk"), ("scalar", None))
        self.assertEqual(ps.step(Osoba, "prefetched_x"), ("queryset", None))
        self.assertEqual(ps.step(Domacinstvo, "zivi_clanovi"), ("queryset", None))

    def test_property_and_missing(self):
        """Метода је непрозирна, непостојећи атрибут недостаје."""
        self.assertEqual(ps.step(Osoba, "__str__"), ("property", None))
        self.assertEqual(ps.step(Osoba, "nepostoji"), ("missing", None))


class WalkTests(SimpleTestCase):
    """Пролаз кроз цео ланац."""

    def test_clean_chains(self):
        """Исправни ланци немају налаз."""
        self.assertIsNone(ps.walk(Osoba, ["adresa", "ulica"]))
        self.assertIsNone(ps.walk(Osoba, ["datum_rodjenja", "year"]))
        self.assertIsNone(ps.walk(Svestenik, ["adrese", "all"]))

    def test_attribute_on_char_field_is_hard(self):
        """Атрибут на CharField је HARD."""
        self.assertEqual(
            ps.walk(Osoba, ["adresa", "ulica", "naziv"]),
            (
                "HARD",
                "step 'naziv' accesses attribute on CharField (parent: adresa.ulica)",
            ),
        )

    def test_missing_attribute_is_hard(self):
        """Непостојећи атрибут је HARD."""
        self.assertEqual(
            ps.walk(Osoba, ["nepostoji"]),
            ("HARD", "step 'nepostoji' not found on Osoba"),
        )

    def test_queryset_and_property_steps_are_soft(self):
        """Корак на queryset-у или после методе је SOFT; индекс није налаз."""
        self.assertEqual(
            ps.walk(Svestenik, ["adrese", "ulica"]),
            ("SOFT", "step 'ulica' on queryset (parent: adrese)"),
        )
        self.assertEqual(
            ps.walk(Osoba, ["__str__", "x"]),
            ("SOFT", "step 'x' after property/method (parent: __str__)"),
        )
        self.assertIsNone(ps.walk(Osoba, ["prefetched_x", "0"]))


class CommandTests(SimpleTestCase):
    """Команда над задатим директоријумом шаблона."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name) / "templates"
        (self.dir / "sub").mkdir(parents=True)
        (self.dir / "a.html").write_text(
            "{{ adresa.ulica.naziv }}\n{{ request.user.x }} {{ nepoznato.a }}\n",
            encoding="utf-8",
        )
        (self.dir / "sub" / "b.html").write_text(
            "{{ svestenik.adrese.ulica }} {{ osoba.ime }}", encoding="utf-8"
        )

    def run_audit(self, *args, templates_dir=None):
        """Излаз и грешке команде."""
        out, err = StringIO(), StringIO()
        call_command(
            "proveri_sablone",
            *args,
            templates_dir=str(templates_dir or self.dir),
            stdout=out,
            stderr=err,
        )
        return out.getvalue(), err.getvalue()

    def test_report_lists_hard_then_soft(self):
        """Збир, па HARD, па SOFT налази; прескочени коренови се не броје."""
        out, _ = self.run_audit()
        self.assertEqual(
            out.splitlines(),
            [
                "# chains checked: 3",
                "# HARD findings: 1",
                "# SOFT findings: 1",
                "",
                "HARD  templates/a.html:1  adresa.ulica.naziv  -- step 'naziv' "
                "accesses attribute on CharField (parent: ulica)",
                "",
                "SOFT  templates/sub/b.html:1  svestenik.adrese.ulica  -- step "
                "'ulica' on queryset (parent: adrese)",
            ],
        )

    def test_severity_filter(self):
        """--severity задржава само тражене налазе, а броји све ланце."""
        out, _ = self.run_audit("--severity", "SOFT")
        self.assertIn("# chains checked: 3", out)
        self.assertIn("# HARD findings: 0", out)
        self.assertIn("svestenik.adrese.ulica", out)
        self.assertNotIn("adresa.ulica.naziv", out)

    def test_missing_dir_is_reported(self):
        """Непостојећи директоријум се пријављује без извештаја."""
        out, err = self.run_audit(templates_dir=self.dir / "nema")
        self.assertEqual(out, "")
        self.assertIn("Templates dir not found", err)
