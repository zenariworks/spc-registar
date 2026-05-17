"""Tests for the sort-as-dropdown control in the list toolbar.

The sort selector renders as a native <select> with name="sort" instead of the
old segmented radio toggle. Submission of the parent form keeps the existing
?sort=<value> contract validated by ListControlsMixin.get_ordering.
"""

import datetime
import re

from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Svestenik, Vencanje


class ListSortDropdownRendersAsSelectTests(TestCase):
    """The sort control is a native <select name='sort'> dropdown."""

    def setUp(self):
        self.client = Client()
        # A handful of parohijani so the list has rows to render.
        Osoba.objects.create(ime="Ана", prezime="Андрић", parohijan=True)
        Osoba.objects.create(ime="Бојан", prezime="Бркић", parohijan=True)
        Osoba.objects.create(ime="Васа", prezime="Васић", parohijan=True)

    def test_parohijani_renders_select_with_name_sort(self):
        """The toolbar emits exactly one <select name='sort'> with the sort class."""
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        # A <select> with name="sort" is present (single source of truth).
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body.count("<select"), body.count('name="sort"'))
        self.assertIn('name="sort"', body)
        self.assertIn("list-toolbar__sort-select", body)

    def test_parohijani_radio_toggle_is_gone(self):
        """The old radio markup must no longer appear in the toolbar."""
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        # The old toggle put radios named "sort" — that pattern must not exist.
        self.assertNotIn('type="radio" name="sort"', body)

    def test_select_has_aria_label_sortiranje(self):
        """Accessibility: the <select> exposes aria-label='Сортирање'."""
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        self.assertRegex(
            body,
            r'<select[^>]*\baria-label="Сортирање"',
        )

    def test_select_submits_form_onchange(self):
        """Picking an option must submit the enclosing GET form."""
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        self.assertRegex(
            body,
            r'<select[^>]*\bonchange="this\.form\.submit\(\)"',
        )

    def test_no_visible_sortiranje_label_next_to_dropdown(self):
        """The visible <label>Сортирање</label> must not appear.

        Accessibility comes from aria-label on the <select>; the surrounding
        toolbar must not render a visible "Сортирање" word.
        """
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        # No <label ...>Сортирање</label> anywhere — visible or visually-hidden.
        self.assertNotRegex(
            body,
            r"<label[^>]*>\s*Сортирање\s*</label>",
        )
        # The .list-toolbar__sort wrapper holds the <select> but no <label> child.
        match = re.search(
            r'<div class="list-toolbar__sort">(.*?)</div>',
            body,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "sort wrapper not rendered")
        self.assertNotIn("<label", match.group(1))

    def test_all_sort_options_appear_as_options(self):
        """Every (value, label) in sort_options renders as an <option>."""
        response = self.client.get(reverse("parohijani"))
        body = response.content.decode()
        sort_options = response.context["sort_options"]
        self.assertTrue(sort_options, "view must declare sort_options")
        for value, label in sort_options:
            self.assertIn(f'value="{value}"', body, msg=f"option {value} missing")
            self.assertIn(label, body, msg=f"label {label} missing")

    def test_current_sort_option_is_selected(self):
        """?sort=-prezime marks the matching <option> selected, not its prefix."""
        response = self.client.get(reverse("parohijani") + "?sort=-prezime")
        body = response.content.decode()
        self.assertRegex(
            body,
            r'<option value="-prezime"[^>]*\bselected\b[^>]*>',
        )
        self.assertNotRegex(
            body,
            r'<option value="prezime"[^>]*\bselected\b[^>]*>',
        )

    def test_default_sort_marks_first_matching_option(self):
        """?sort=prezime marks the matching <option> selected."""
        response = self.client.get(reverse("parohijani") + "?sort=prezime")
        body = response.content.decode()
        self.assertRegex(
            body,
            r'<option value="prezime"[^>]*\bselected\b[^>]*>',
        )

    def test_unknown_sort_value_marks_no_option_selected(self):
        """An out-of-list sort value yields a <select> with no selected option."""
        response = self.client.get(reverse("parohijani") + "?sort=bogus")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        # Pull out the inside of the sort <select> and check no option carries
        # the `selected` attribute when the user passed an invalid value.
        match = re.search(
            r'<select[^>]*class="[^"]*list-toolbar__sort-select[^"]*"[^>]*>(.*?)</select>',
            body,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match, "sort <select> not rendered")
        inner = match.group(1)
        self.assertNotIn("selected", inner)


class ListSortDropdownAcrossAllListPagesTests(TestCase):
    """Every list page that declares sort_options must render the dropdown."""

    def setUp(self):
        self.client = Client()
        self.hram = Hram.objects.create(naziv="Тест Храм")
        # parohijani
        Osoba.objects.create(ime="Петар", prezime="Петровић", parohijan=True)
        # svestenici
        Svestenik.objects.create(ime="Јован", prezime="Јовановић", zvanje="јереј")
        # krstenja
        Krstenje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
            hram=self.hram,
        )
        # vencanja
        Vencanje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 6, 1),
            hram=self.hram,
        )

    def _assert_dropdown_rendered(self, url_name):
        """Helper: GET <url_name> and assert the toolbar renders the dropdown."""
        response = self.client.get(reverse(url_name))
        self.assertEqual(response.status_code, 200, msg=url_name)
        body = response.content.decode()
        self.assertIn("list-toolbar__sort-select", body, msg=url_name)
        self.assertIn('name="sort"', body, msg=url_name)
        self.assertNotIn('type="radio" name="sort"', body, msg=url_name)

    def test_parohijani(self):
        """/parohijani/ renders the sort dropdown."""
        self._assert_dropdown_rendered("parohijani")

    def test_krstenja(self):
        """/krstenja/ renders the sort dropdown."""
        self._assert_dropdown_rendered("krstenja")

    def test_vencanja(self):
        """/vencanja/ renders the sort dropdown."""
        self._assert_dropdown_rendered("vencanja")

    def test_svestenici(self):
        """/svestenici/ renders the sort dropdown."""
        self._assert_dropdown_rendered("svestenici")

    def test_domacinstva(self):
        """/domacinstva/ renders the sort dropdown."""
        self._assert_dropdown_rendered("domacinstva")


class ListSortDropdownStillSortsTests(TestCase):
    """The dropdown still drives ordering via the ?sort=<value> contract."""

    def setUp(self):
        self.client = Client()
        # Three parohijani with surnames that have a deterministic order.
        Osoba.objects.create(ime="А", prezime="Аврамовић", parohijan=True)
        Osoba.objects.create(ime="Б", prezime="Бабић", parohijan=True)
        Osoba.objects.create(ime="Ц", prezime="Цвијић", parohijan=True)

    def test_ascending_sort_orders_object_list(self):
        """?sort=prezime sorts the object list by surname ascending."""
        response = self.client.get(reverse("parohijani") + "?sort=prezime")
        ordering = [o.prezime for o in response.context["object_list"]]
        self.assertEqual(ordering, sorted(ordering))

    def test_descending_sort_orders_object_list(self):
        """?sort=-prezime sorts the object list by surname descending."""
        response = self.client.get(reverse("parohijani") + "?sort=-prezime")
        ordering = [o.prezime for o in response.context["object_list"]]
        self.assertEqual(ordering, sorted(ordering, reverse=True))
