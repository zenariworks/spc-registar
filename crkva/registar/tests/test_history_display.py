"""Tests for FK-aware rendering of django-simple-history diffs.

The history panel used to render FK changes as raw PKs/UUIDs, e.g.
``zanimanje: — → f5f3a1b5-...``. After the fix the rendered value
must be the related row's ``__str__`` (e.g. ``радник``).
"""

# pylint: disable=missing-function-docstring

from django.test import TestCase
from registar.history import DELETED_LABEL, history_for
from registar.models import Osoba, Veroispovest, Zanimanje


class HistoryFKDisplayTests(TestCase):
    """``history_for()`` should resolve FK PKs to a readable label."""

    def test_zanimanje_resolves_to_naziv_not_uuid(self):
        radnik = Zanimanje.objects.create(sifra="1", naziv="радник")
        o = Osoba.objects.create(ime="ФК", prezime="Тест1", pol="М")
        o.zanimanje = radnik
        o.save()

        entries = history_for(o)
        # newest first: the update we just did
        update = entries[0]
        change = next(c for c in update.changes if c.field == "zanimanje")
        self.assertEqual(change.old, None)
        self.assertEqual(change.new, "радник")
        # Sanity: the raw PK must not leak through.
        self.assertNotIn(str(radnik.pk), str(change.new))

    def test_veroispovest_resolves_to_naziv_not_uuid(self):
        pravo = Veroispovest.objects.create(naziv="православна")
        o = Osoba.objects.create(ime="ФК", prezime="Тест2", pol="М")
        o.veroispovest = pravo
        o.save()

        entries = history_for(o)
        update = entries[0]
        change = next(c for c in update.changes if c.field == "veroispovest")
        self.assertEqual(change.new, "православна")
        self.assertNotIn(str(pravo.pk), str(change.new))

    def test_deleted_fk_target_falls_back_to_label(self):
        z = Zanimanje.objects.create(sifra="2", naziv="привремено")
        o = Osoba.objects.create(ime="ФК", prezime="Тест3", pol="М")
        o.zanimanje = z
        o.save()

        # Wipe the FK target after the historical record was written; the
        # historical row still points at the now-missing PK.
        z.delete()

        entries = history_for(o)
        update = entries[0]
        change = next(c for c in update.changes if c.field == "zanimanje")
        self.assertEqual(change.new, DELETED_LABEL)

    def test_non_fk_field_values_pass_through_unchanged(self):
        o = Osoba.objects.create(ime="Скаларно", prezime="Прво", pol="М")
        o.prezime = "Друго"
        o.save()

        entries = history_for(o)
        update = entries[0]
        change = next(c for c in update.changes if c.field == "prezime")
        # Plain strings should not be touched by the FK resolver.
        self.assertEqual(change.old, "Прво")
        self.assertEqual(change.new, "Друго")

    def test_template_renders_resolved_label_not_uuid(self):
        """End-to-end: the panel template must show the readable label."""
        from django.template import Context, Template

        radnik = Zanimanje.objects.create(sifra="3", naziv="радник")
        o = Osoba.objects.create(ime="Шаб.", prezime="Тест", pol="М")
        o.zanimanje = radnik
        o.save()

        entries = history_for(o)
        tpl = Template(
            "{% for e in entries %}{% for c in e.changes %}"
            "[{{ c.field }}:{{ c.old|default:'—' }}->{{ c.new|default:'—' }}]"
            "{% endfor %}{% endfor %}"
        )
        rendered = tpl.render(Context({"entries": entries}))
        self.assertIn("zanimanje:—->радник", rendered)
        self.assertNotIn(str(radnik.pk), rendered)
