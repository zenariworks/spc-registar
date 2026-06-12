"""Тестови за info_row / info_section template тагове.

Уверавају се да:

* Тагови рендерују очекивани markup (структуру) — стабилно ослањање на CSS
  у info.css зависи од тачних имена класа и угнежђивања, па их експлицитно
  фиксирамо овде.
* Bool тагови постављају checkbox као директно дете .info-row__value тако
  да CSS-ово slider правило за `.info-row--editable .info-row__value > input[type="checkbox"]`
  применљиво.
* Странице које их користе (parohijan, svestenik, krstenje, vencanje,
  domacinstvo) и даље рендерују без грешке.
"""

from django import forms
from django.template import Context, Template
from django.test import TestCase


class _BoolForm(forms.Form):
    flag = forms.BooleanField(required=False)


class _TextForm(forms.Form):
    name = forms.CharField(required=False)


class InfoRowTagTestCase(TestCase):
    """{% info_row %} inclusion tag."""

    def render(self, body, ctx=None):
        tpl = Template("{% load info_components %}" + body)
        return tpl.render(Context(ctx or {}))

    def test_renders_value_only(self):
        out = self.render(
            '{% info_row icon="fa-droplet" label="Слава" value="Никољдан" %}'
        )
        self.assertIn('<li class="info-row">', out)
        self.assertIn('<div class="info-row__icon" data-tooltip="Слава">', out)
        self.assertIn('<i class="fa-solid fa-droplet"></i>', out)
        self.assertIn('<label class="info-row__label">Слава</label>', out)
        self.assertIn('<span class="info-row__static">Никољдан</span>', out)
        # No form widget rendered when field is omitted.
        self.assertNotIn("<input", out)
        self.assertNotIn("info-row--editable", out)

    def test_renders_field_and_value(self):
        form = _TextForm()
        out = self.render(
            '{% info_row icon="fa-user" label="Име" field=form.name value="Марко" %}',
            {"form": form},
        )
        # Both static and widget are present; CSS picks which is visible.
        self.assertIn('<span class="info-row__static">Марко</span>', out)
        self.assertIn('name="name"', out)
        # Editable + stacked modifiers applied so info.css picks up the row.
        self.assertIn("info-row--editable", out)
        self.assertIn("info-row--stacked", out)
        # Label gets the for= attribute when field is supplied.
        self.assertIn('for="id_name"', out)

    def test_renders_link_around_value(self):
        out = self.render(
            '{% info_row icon="fa-house" label="Кућа" value="Адреса" link="/x/" %}'
        )
        self.assertIn('<a href="/x/">Адреса</a>', out)

    def test_muted_empty_default(self):
        out = self.render('{% info_row icon="fa-user" label="X" %}')
        self.assertIn('<span class="info-row__static--muted">—</span>', out)

    def test_muted_empty_false_renders_bare_dash(self):
        out = self.render('{% info_row icon="fa-user" label="X" muted_empty=False %}')
        self.assertNotIn("info-row__static--muted", out)
        # The bare em dash is wrapped only by the .info-row__static span.
        self.assertIn('<span class="info-row__static">—</span>', out)

    def test_sub_text_appended(self):
        out = self.render(
            '{% info_row icon="fa-x" label="X" value="Главно" sub="напомена" %}'
        )
        self.assertIn('<span class="info-row__sub">напомена</span>', out)

    def test_inline_mode_drops_body_wrapper(self):
        # Inline rows do not get info-row--stacked; the value sits directly
        # under .info-row (no .info-row__body wrapper) so the inline-grid
        # CSS rule applies.
        form = _TextForm()
        out = self.render(
            '{% info_row icon="fa-book" label="Књига" field=form.name value="1" inline=True %}',
            {"form": form},
        )
        self.assertIn("info-row--editable", out)
        self.assertNotIn("info-row--stacked", out)
        self.assertNotIn("info-row__body", out)

    def test_full_modifier_for_textarea_row(self):
        out = self.render(
            '{% info_row icon="fa-x" label="X" value="" inline=True full=True %}'
        )
        self.assertIn("info-row--full", out)


class InfoRowBoolTagTestCase(TestCase):
    """{% info_row_bool %} inclusion tag — slider toggle."""

    def render(self, body, ctx):
        tpl = Template("{% load info_components %}" + body)
        return tpl.render(Context(ctx))

    def test_checkbox_is_direct_child_of_info_row_value(self):
        # CSS contract: the slider rule in info.css targets
        # `.info-row--editable .info-row__value > input[type="checkbox"]`,
        # so the checkbox MUST be a direct child of .info-row__value.
        form = _BoolForm()
        out = self.render(
            '{% info_row_bool icon="fa-droplet" label="Х" value_label="Х" field=form.flag value=v %}',
            {"form": form, "v": True},
        )
        self.assertIn('<div class="info-row__value">', out)
        # Find: <div class="info-row__value">…<input type="checkbox" …
        # with only whitespace and the static <span> between.
        import re

        m = re.search(
            r'<div class="info-row__value">.*?'
            r'<input type="checkbox"[^>]*name="flag"',
            out,
            re.S,
        )
        self.assertIsNotNone(
            m,
            "checkbox must be a direct child of .info-row__value, "
            "otherwise the slider-toggle CSS does not apply",
        )

    def test_bool_label_uses_dedicated_class(self):
        # The inline label next to the slider uses .info-row__bool-label
        # (info.css applies margin-left + cursor:pointer to it).
        form = _BoolForm()
        out = self.render(
            '{% info_row_bool icon="fa-droplet" label="Славска" value_label="Славска" field=form.flag value=v %}',
            {"form": form, "v": False},
        )
        self.assertIn('class="info-row__bool-label"', out)
        # The label is for= the field id.
        self.assertIn('for="id_flag"', out)
        # The plain .info-row__label is NOT used inside bool rows (it would
        # apply the wrong "label-above-input" styling).
        self.assertNotIn('class="info-row__label"', out)

    def test_bool_view_toggle_reflects_value(self):
        """The disabled view-mode toggle is checked iff value is truthy.
        The static label (value_label) always renders alongside."""
        form = _BoolForm()
        out_da = self.render(
            '{% info_row_bool icon="fa-x" label="X" value_label="Велико X" field=form.flag value=True %}',
            {"form": form},
        )
        out_ne = self.render(
            '{% info_row_bool icon="fa-x" label="X" value_label="Велико X" field=form.flag value=False %}',
            {"form": form},
        )
        # Truthy → disabled view toggle is checked.
        self.assertIn('class="info-row__bool-view"', out_da)
        self.assertIn("checked", out_da)
        self.assertIn("Велико X", out_da)
        # Falsy → disabled view toggle exists but has no checked attribute.
        self.assertIn('class="info-row__bool-view"', out_ne)
        self.assertNotIn("checked", out_ne)
        self.assertIn("Велико X", out_ne)

    def test_sub_appended_to_static(self):
        form = _BoolForm()
        out = self.render(
            '{% info_row_bool icon="fa-x" label="Близанац" value_label="Близанац" field=form.flag value=True sub="(Петар)" %}',
            {"form": form},
        )
        self.assertIn('<span class="info-row__sub">(Петар)</span>', out)


class InfoSectionTagTestCase(TestCase):
    """{% info_section %} simple_block_tag wraps content in section markup."""

    def test_wraps_content_in_section(self):
        tpl = Template(
            "{% load info_components %}"
            '{% info_section title="Контакт" icon="fa-phone" %}'
            "<li>row</li>"
            "{% endinfo_section %}"
        )
        out = tpl.render(Context({}))
        self.assertIn('<div class="info-section">', out)
        self.assertIn('<h2 class="info-section__title">', out)
        self.assertIn('<i class="fa-solid fa-phone"></i>', out)
        self.assertIn("Контакт</h2>", out)
        self.assertIn('<ul class="info-rows">', out)
        self.assertIn("<li>row</li>", out)

    def test_no_icon_renders_no_icon_tag(self):
        tpl = Template(
            "{% load info_components %}"
            '{% info_section title="Чланови" %}content{% endinfo_section %}'
        )
        out = tpl.render(Context({}))
        self.assertIn("Чланови", out)
        # No <i class="fa-solid …"></i> when icon is omitted.
        self.assertNotIn("fa-solid", out)

    def test_inline_flag_swaps_ul_class(self):
        tpl = Template(
            "{% load info_components %}"
            '{% info_section title="Запис" icon="fa-file-lines" inline=True %}'
            "{% endinfo_section %}"
        )
        out = tpl.render(Context({}))
        self.assertIn('<ul class="info-rows info-rows--inline">', out)


class FullPageRenderSmokeTest(TestCase):
    """End-to-end smoke: each refactored page renders without raising.

    Uses a stub object with attributes set to None / empty / falsy values so
    the templates exercise every "render the static span" branch (which is
    where the info_row tag does most of its work).
    """

    @staticmethod
    def _stub(**attrs):
        return type("Stub", (), attrs)()

    def _render(self, template_name, instance_key, **extra):
        from django.template.loader import render_to_string

        ctx = {instance_key: None, "form": None, "is_edit": False}
        ctx.update(extra)
        return render_to_string(template_name, ctx)

    def test_svestenik_renders_no_form(self):
        # No form, no svestenik — page-header-only rendering.
        out = self._render("registar/svestenik.html", "svestenik")
        self.assertIn("info-page", out)

    def test_domacinstvo_renders_no_form(self):
        out = self._render("registar/domacinstvo.html", "domacinstvo")
        self.assertIn("info-page", out)

    def test_parohijan_renders_no_form(self):
        out = self._render("registar/parohijan.html", "parohijan")
        self.assertIn("info-page", out)

    def test_krstenje_renders_no_form(self):
        out = self._render("registar/krstenje.html", "krstenje")
        self.assertIn("info-page", out)

    def test_vencanje_renders_no_form(self):
        out = self._render("registar/vencanje.html", "vencanje")
        self.assertIn("info-page", out)
