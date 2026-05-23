"""Rename six Krstenje fields to drop the redundant `dete_` prefix.

dete_rodjeno_zivo       -> zivorodjeno
dete_po_redu_po_majci   -> po_redu
dete_vanbracno          -> vanbracno
dete_blizanac           -> blizanac
drugo_dete_blizanac_ime -> ime_blizanca
dete_sa_telesnom_manom  -> telesna_mana

Applied to both krstenje and historicalkrstenje (django-simple-history mirror).
Pure RenameField — no data loss, no schema-shape change beyond column names.
The auto-generator falls back to drop+add for these because the field
verbose_names changed alongside the field names; a hand-written RenameField
migration is the safe path.
"""

from django.db import migrations


RENAMES = [
    ("dete_rodjeno_zivo", "zivorodjeno"),
    ("dete_po_redu_po_majci", "po_redu"),
    ("dete_vanbracno", "vanbracno"),
    ("dete_blizanac", "blizanac"),
    ("drugo_dete_blizanac_ime", "ime_blizanca"),
    ("dete_sa_telesnom_manom", "telesna_mana"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("registar", "0011_alter_adresa_broj_and_more"),
    ]

    operations = [
        op
        for old, new in RENAMES
        for op in (
            migrations.RenameField(model_name="krstenje", old_name=old, new_name=new),
            migrations.RenameField(model_name="historicalkrstenje", old_name=old, new_name=new),
        )
    ]
