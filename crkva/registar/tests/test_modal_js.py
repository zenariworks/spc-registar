"""Regression tests for ``components/modal.js``.

Krštenje and venčanje include both ``_modal_osoba.html`` and
``_modal_svestenik.html``; both declare ``#modal-ime`` and
``#modal-prezime``. ``Modal.bindForm`` used to read fields with
``document.getElementById``, so the svestenik modal read the osoba modal's
empty inputs and always failed with "Име, презиме и звање су обавезни."

A toggle choice (e.g. pol "Ж" for majka) also survived reopening the
modal: the button highlight was cleared but the stored value was still
posted for the next person.
"""

import pathlib
import re

from django.template.loader import render_to_string
from django.test import SimpleTestCase

MODAL_JS = (
    pathlib.Path(__file__).resolve().parents[1]
    / "static"
    / "registar"
    / "components"
    / "modal.js"
)


class ModalJsTests(SimpleTestCase):
    """Field lookup is scoped to the modal; opening resets toggle state."""

    def setUp(self):
        self.js = MODAL_JS.read_text(encoding="utf-8")

    def test_osoba_and_svestenik_modals_share_input_ids(self):
        """The premise: one page renders two ``#modal-ime`` inputs."""
        html = render_to_string("_partials/_modal_osoba.html") + render_to_string(
            "_partials/_modal_svestenik.html"
        )
        self.assertEqual(html.count('id="modal-ime"'), 2)
        self.assertEqual(html.count('id="modal-prezime"'), 2)

    def test_fields_are_read_inside_the_modal(self):
        """Inputs come from ``overlay.querySelector``, not the document."""
        self.assertIn('overlay.querySelector("#modal-" + f)', self.js)
        self.assertNotRegex(self.js, r'document\.getElementById\("modal-"')

    def test_toggle_groups_are_looked_up_inside_the_modal(self):
        """Toggle groups are found inside the modal too."""
        self.assertIn('overlay.querySelector("#" + groupId)', self.js)

    def test_open_resets_toggle_state(self):
        """``open()`` clears the stored toggle values of a bound form."""
        open_fn = re.search(r"function open\(.*?\n    }\n", self.js, re.S)
        self.assertIsNotNone(open_fn)
        self.assertIn("_resetHandlers[modalId]?.()", open_fn.group(0))
        self.assertIn("_resetHandlers[modalId] =", self.js)
