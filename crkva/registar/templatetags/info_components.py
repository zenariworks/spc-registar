"""Reusable info-row / info-section template tags.

These tags encapsulate the markup for the ``info-row`` and ``info-section``
patterns used across the detail/edit templates (``domacinstvo.html``,
``parohijan.html``, ``svestenik.html``, ``krstenje.html``, ``vencanje.html``).

The goal is to keep the row structure in one place so that future spacing,
icon, or label tweaks happen in a single partial instead of being chased across
five 200-350 line templates.

Two tags are exported:

* :func:`info_row` (inclusion tag) — renders one ``<li class="info-row">``.
  Renders both the static (view-mode) ``<span class="info-row__static">`` and
  the bound form widget when ``field`` is supplied.  The wrapping form's
  ``data-mode`` attribute (set by ``info.css``) controls which is visible.

* :func:`info_section` (block tag) — wraps its content in an
  ``<div class="info-section">`` with an ``<h2>`` title.  Use as::

      {% info_section title="Контакт" icon="fa-address-book" %}
        {% info_row icon="fa-phone" label="Телефон" field=form.tel value=osoba.tel %}
      {% endinfo_section %}

Pragmatic rule of thumb: rows whose view-mode rendering is just text (with the
usual ``—`` fallback when empty) are perfect for ``info_row``.  Rows whose
static span has bespoke markup (OSM links, phone formatting, multi-line
composed text) stay as raw HTML — converting them does not pay for itself.
"""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag("registar/_info_row.html")
def info_row(
    icon,
    label,
    field=None,
    value=None,
    link=None,
    sub=None,
    inline=False,
    full=False,
    muted_empty=True,
):
    """Render a single info-row.

    Parameters
    ----------
    icon : str
        Font Awesome class fragment, e.g. ``"fa-droplet"``.  The
        ``fa-solid`` prefix is added by the partial.
    label : str
        Human label.  Used both as tooltip on the icon and as the
        ``<label>`` shown above the widget in edit mode.  Rows in
        ``info-rows--inline`` sections (where ``inline=True``) intentionally
        omit the label markup but keep the tooltip.
    field : BoundField, optional
        Bound form field to render in edit mode.  When ``None``, only the
        static span is rendered (view-only row).
    value : Any, optional
        Static view value.  ``None`` / empty renders the muted ``—`` marker
        (unless ``muted_empty=False``, in which case a plain ``—`` is used).
    link : str, optional
        URL.  When set and ``value`` is truthy, the value is wrapped in
        ``<a href="link">…</a>``.
    sub : str, optional
        Small muted subline appended after the value (e.g. occupation,
        place of birth qualifier).
    inline : bool, default False
        If ``True``, the row omits the stacked label/body wrapper and renders
        compact (used inside ``info-rows--inline`` sections in
        ``krstenje.html`` / ``vencanje.html``).
    full : bool, default False
        Adds ``info-row--full`` modifier (used for full-width textareas
        in inline sections, e.g. ``примедба``).
    muted_empty : bool, default True
        When ``True``, the empty placeholder is wrapped in
        ``<span class="info-row__static--muted">—</span>``.  Set to ``False``
        for rows that historically render a bare ``—`` (e.g. ``parohijan.ime``).
    """
    return {
        "icon": icon,
        "label": label,
        "field": field,
        "value": value,
        "link": link,
        "sub": sub,
        "inline": inline,
        "full": full,
        "muted_empty": muted_empty,
    }


@register.inclusion_tag("registar/_info_row_bool.html")
def info_row_bool(icon, label, value_label, field=None, value=None, sub=None):
    """Render a boolean (slider/checkbox) info-row.

    The static span reads ``"{value_label}: Да/Не"`` and the widget is a
    checkbox followed by an inline ``<label>``.

    Parameters
    ----------
    icon : str
        Font Awesome class fragment.
    label : str
        Tooltip text on the icon column and ``<label>`` text next to the
        checkbox.
    value_label : str
        Prefix shown in the static (view-mode) span before ``Да``/``Не``.
        Usually identical to ``label``.
    field : BoundField, optional
        Bound checkbox form field.
    value : bool, optional
        Static boolean value.  Renders as ``Да`` or ``Не``.
    sub : str, optional
        Small muted subline appended after the static value (e.g. the
        twin's name on ``blizanac``).
    """
    return {
        "icon": icon,
        "label": label,
        "value_label": value_label,
        "field": field,
        "value": bool(value),
        "sub": sub,
    }


@register.simple_block_tag
def info_section(content, title, icon=None, inline=False, show_mode=None):
    """Wrap content in an ``<div class="info-section">`` with an ``<h2>`` title.

    Parameters
    ----------
    title : str
        Section heading text.
    icon : str, optional
        Font Awesome class fragment for the heading icon.  Omitted on
        sections that historically had no icon (e.g. "Чланови (3)").
    inline : bool, default False
        When ``True``, the inner ``<ul>`` uses ``info-rows info-rows--inline``
        (used by the ZAPIS / АНАГРАФ sections).
    show_mode : str, optional
        Value for the ``data-show-mode`` attribute on the wrapping div
        (``"view"`` or ``"edit"``).  Used by ``info.css`` to hide
        view-only / edit-only sections.
    """
    ul_cls = "info-rows info-rows--inline" if inline else "info-rows"
    section_attrs = format_html(' data-show-mode="{}"', show_mode) if show_mode else ""
    icon_html = format_html('<i class="fa-solid {}"></i> ', icon) if icon else ""
    return format_html(
        '<div class="info-section"{}>'
        '<h2 class="info-section__title">{}{}</h2>'
        '<ul class="{}">{}</ul>'
        "</div>",
        section_attrs,
        icon_html,
        title,
        ul_cls,
        mark_safe(content),
    )
