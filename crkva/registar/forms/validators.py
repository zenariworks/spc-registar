"""Заједничке валидације и подешавања за форме регистра."""

from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from django import forms


def validate_distinct_roles(form: "forms.BaseForm", role_names: Iterable[str]) -> None:
    """Иста особа не сме да попуњава две улоге у истој форми.

    За сваки пар поља из ``role_names`` чије су вредности једнаке и
    непразне, додаје грешку на друго поље у пару. Порука користи имена
    поља онако како су наведена (нпр. „и dete и kum“).
    """
    cleaned = form.cleaned_data
    for name_a, name_b in combinations(role_names, 2):
        val_a = cleaned.get(name_a)
        val_b = cleaned.get(name_b)
        if val_a and val_b and val_a == val_b:
            form.add_error(name_b, f"Иста особа не може бити и {name_a} и {name_b}.")


def default_parohijan_off(form: "forms.BaseForm", field_names: Iterable[str]) -> None:
    """Искључи подразумевани „парохијан“ брзи унос за дата поља.

    Кумови, таст/ташта и сродне улоге су често из друге парохије, па
    њихов quick-add toggle не треба да их подразумевано додаје у овдашњи
    списак.
    """
    for name in field_names:
        form.fields[name].widget.attrs["data-osoba-parohijan-default"] = "0"
