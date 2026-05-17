"""Test: select2 closed-state pill matches the list-toolbar sort dropdown chrome."""

import pathlib

from django.test import TestCase


class Select2ClosedStateMatchesSortDropdown(TestCase):
    """The select2 selection pill must share frame/chevron with .list-toolbar__sort-select."""

    SKIN = pathlib.Path("crkva/registar/static/registar/components/select2_skin.css")
    SPISKOVI = pathlib.Path("crkva/registar/static/registar/components/spiskovi.css")

    def setUp(self):
        self.skin = self.SKIN.read_text(encoding="utf-8")
        self.sort_css = self.SPISKOVI.read_text(encoding="utf-8")

    def _block(self, text, selector):
        return text.split(selector, 1)[1].split("}", 1)[0]

    def test_select2_closed_state_uses_background_chevron(self):
        """Closed pill must paint a chevron via background-image."""
        block = self._block(
            self.skin, ".select2-container--default .select2-selection--single {"
        )
        self.assertIn("background-image:", block)
        self.assertIn("%3Csvg", block)

    def test_select2_closed_state_min_height_36(self):
        """Closed pill height matches the sort dropdown (36px)."""
        block = self._block(
            self.skin, ".select2-container--default .select2-selection--single {"
        )
        self.assertIn("min-height: 36px", block)

    def test_select2_built_in_arrow_is_hidden(self):
        """Built-in select2 arrow is hidden in favour of the background chevron."""
        block = self._block(
            self.skin,
            ".select2-container--default .select2-selection--single .select2-selection__arrow {",
        )
        self.assertIn("display: none", block)

    def test_select2_rendered_padding_matches_sort_select_padding(self):
        """Inner padding is identical to .list-toolbar__sort-select."""
        select2_block = self._block(
            self.skin,
            ".select2-container--default .select2-selection--single .select2-selection__rendered {",
        )
        sort_block = self._block(self.sort_css, "select.list-toolbar__sort-select {")
        self.assertIn("padding: 8px 36px 8px 14px", select2_block)
        self.assertIn("padding: 8px 36px 8px 14px", sort_block)
