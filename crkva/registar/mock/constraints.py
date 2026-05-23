"""Cross-field sanity constraints for generated mock data.

Each constraint takes ready-to-create data + raises AssertionError if
the data violates a domain invariant. Used by seed_* commands so
generation bugs fail loudly rather than producing nonsense records.
"""
from __future__ import annotations

from datetime import date

from .generators import TODAY, age


# --------------------------------------------------------------------
# PERSON-LEVEL
# --------------------------------------------------------------------
def assert_adult(person_birthdate: date, on: date | None = None, role: str = "person"):
    """`person` must be ≥ 18 on `on` (default today)."""
    assert age(person_birthdate, on) >= 18, (
        f"{role} mora biti punoletan/a (rodjen/a {person_birthdate}, "
        f"datum provere {on or TODAY})"
    )


def assert_priest(gender: str, birthdate: date):
    """Priest = male, age 25-80."""
    assert gender == "М", f"свештеник мора бити мушки, добио: {gender!r}"
    a = age(birthdate)
    assert 25 <= a <= 80, f"свештеник мора имати 25-80 година, добио: {a}"


# --------------------------------------------------------------------
# MARRIAGE
# --------------------------------------------------------------------
def assert_spouse_pair(zenik_gender: str, zenik_birthdate: date,
                       nevesta_gender: str, nevesta_birthdate: date,
                       datum_vencanja: date):
    """Heterosexual pair, both adults at wedding, age gap < 25 years."""
    assert zenik_gender == "М", f"женик мора бити мушки, добио: {zenik_gender!r}"
    assert nevesta_gender == "Ж", f"невеста мора бити женска, добила: {nevesta_gender!r}"
    assert_adult(zenik_birthdate, datum_vencanja, "женик")
    assert_adult(nevesta_birthdate, datum_vencanja, "невеста")
    diff = abs(age(zenik_birthdate, datum_vencanja) - age(nevesta_birthdate, datum_vencanja))
    assert diff <= 25, f"разлика година премашује 25: {diff}"


# --------------------------------------------------------------------
# BAPTISM
# --------------------------------------------------------------------
def assert_krstenje(
    dete_birthdate: date, datum_krstenja: date,
    otac_gender: str | None = None, majka_gender: str | None = None,
):
    """Child age <5 at baptism, datum after birth, parents have valid genders."""
    assert datum_krstenja >= dete_birthdate, (
        f"крштење не може бити пре рођења: {datum_krstenja} < {dete_birthdate}"
    )
    a = age(dete_birthdate, datum_krstenja)
    assert 0 <= a <= 5, f"дете треба да буде 0-5 година на крштењу, добио: {a}"
    if otac_gender is not None:
        assert otac_gender == "М", f"отац мора бити мушки, добио: {otac_gender!r}"
    if majka_gender is not None:
        assert majka_gender == "Ж", f"мајка мора бити женска, добила: {majka_gender!r}"


# --------------------------------------------------------------------
# UKUCAN (household member)
# --------------------------------------------------------------------
def assert_no_self_reference(osoba_uid, related_uids: list, kind: str):
    """A person can't be their own kum/spouse/parent."""
    assert osoba_uid not in related_uids, (
        f"{kind}: особа {osoba_uid} не може бити сама себи у овој улози"
    )
