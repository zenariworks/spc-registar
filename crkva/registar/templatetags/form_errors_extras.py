"""Template filter that exposes a form's field errors as a plain dict.

Used by _partials/_form_errors.html to feed components/form-errors.js, which
highlights the corresponding inputs and injects per-field error bubbles.

Why a custom filter: `form.errors` is an ErrorDict whose values are
ErrorList objects. json_script encodes those as strings of joined items,
not arrays, so we coerce to {fieldname: [str, ...]} ourselves.
"""

from django import template

register = template.Library()


@register.filter(name="field_errors_dict")
def field_errors_dict(form):
    """Return {field_name: [str, ...]} for fields that have errors.

    Skips form.non_field_errors — those are rendered in the banner directly.
    Each error is coerced via str() so lazy translation proxies materialize
    before json_script encodes them.
    """
    out = {}
    for name, error_list in form.errors.items():
        if name == "__all__":
            continue
        out[name] = [str(e) for e in error_list]
    return out
