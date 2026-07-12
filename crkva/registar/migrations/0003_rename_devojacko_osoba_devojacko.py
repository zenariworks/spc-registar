from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("registar", "0002_alter_historicalvencanje_datum_ispita_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="osoba",
            old_name="devojacko_prezime",
            new_name="devojacko",
        ),
        migrations.RenameField(
            model_name="historicalosoba",
            old_name="devojacko_prezime",
            new_name="devojacko",
        ),
    ]
