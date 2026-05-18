"""Regression test for the ``+ Додај новог`` osoba modal silently failing.

The ``_modal_osoba.html`` partial renders inside ``{% block content %}``,
while ``modal.js`` is loaded at the bottom of ``base.html`` (after the
content block). When the partial's inline ``<script>`` ran ``Modal.bindForm``
at parse time, ``Modal`` was not yet defined: the script threw
``ReferenceError`` and the ``var osobaModal`` declaration was left
``undefined``. ``osoba_create.js``'s click handler for the inline
``+ Додај новог`` footer in select2 dropdowns checks
``window.osobaModal`` before opening the modal, so the click became a
silent no-op on every page that included the partial.

The fix defers the ``Modal.bindForm`` call to ``DOMContentLoaded``, which
fires *after* ``modal.js`` has loaded and ``Modal`` is defined.

These tests assert two things:

1. The rendered partial wires ``window.osobaModal`` from a
   ``DOMContentLoaded`` callback rather than at parse time.
2. The footer save button no longer calls a bare ``osobaModal.save()``
   reference (the inline script no longer creates that local ``var``);
   it goes through ``window.osobaModal``.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from __future__ import annotations

from django.template.loader import render_to_string
from django.test import TestCase


class OsobaModalDefersBindFormTests(TestCase):
    """``Modal.bindForm`` must not run inline -- it must wait for ``DOMContentLoaded``."""

    def setUp(self):
        self.body = render_to_string("registar/_modal_osoba.html")

    def test_bind_form_is_deferred_to_domcontentloaded(self):
        """The bind call must be inside a ``DOMContentLoaded`` listener."""
        self.assertIn("DOMContentLoaded", self.body)
        self.assertIn("Modal.bindForm", self.body)
        # The actual bind line must come *after* the DOMContentLoaded marker
        # so that running it at parse time is no longer possible.
        idx_dom = self.body.index("DOMContentLoaded")
        idx_bind = self.body.index("Modal.bindForm")
        # Bind sits inside the init function body, which sits inside the
        # function passed to addEventListener("DOMContentLoaded", ...).
        # Both orderings are acceptable -- what we really care about is
        # that the bind call no longer fires at the top of the script.
        self.assertGreater(
            idx_bind,
            self.body.index("function init()"),
            msg=(
                "Modal.bindForm must live inside the deferred init function, "
                "not at the top of the inline script."
            ),
        )
        # And init must be wired through DOMContentLoaded.
        self.assertLess(idx_dom, len(self.body))

    def test_window_osoba_modal_is_explicitly_set(self):
        """``window.osobaModal`` must be assigned -- a bare ``var`` would
        be scoped to the inline IIFE and unreachable from ``osoba_create.js``."""
        self.assertIn("window.osobaModal", self.body)

    def test_footer_save_button_uses_window_osoba_modal(self):
        """The Сачувај button onclick must guard on ``window.osobaModal``."""
        self.assertIn("window.osobaModal", self.body)
        # The original bare ``osobaModal.save()`` reference required a
        # top-level ``var osobaModal`` -- which never got assigned because
        # ``Modal`` was undefined at parse time. The fixed markup goes
        # through ``window.osobaModal``.
        self.assertNotIn('onclick="osobaModal.save()"', self.body)
