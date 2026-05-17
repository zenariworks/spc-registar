"""Initial migration for the shared kalendar app.

Creates the canonical `slave` table in the public schema. Every tenant
references it via Domacinstvo.slava (FK with db_constraint=False — see
registar migration 0005).
"""

import django.core.validators
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Slava",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "uid",
                    models.AutoField(
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("naziv", models.CharField(verbose_name="назив")),
                ("opsti_naziv", models.CharField(verbose_name="општи назив")),
                (
                    "dan",
                    models.IntegerField(
                        blank=True,
                        db_index=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(31),
                        ],
                        verbose_name="дан",
                    ),
                ),
                (
                    "mesec",
                    models.IntegerField(
                        blank=True,
                        db_index=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(12),
                        ],
                        verbose_name="месец",
                    ),
                ),
                (
                    "pokretni",
                    models.BooleanField(
                        default=False,
                        help_text="Празник који се рачуна у односу на Васкрс",
                        verbose_name="покретни празник",
                    ),
                ),
                (
                    "offset_dani",
                    models.IntegerField(
                        blank=True,
                        help_text="Број дана у односу на Васкрс",
                        null=True,
                        verbose_name="помак у данима",
                    ),
                ),
                (
                    "offset_nedelje",
                    models.IntegerField(
                        blank=True,
                        help_text="Број недеља у односу на Васкрс",
                        null=True,
                        verbose_name="помак у недељама",
                    ),
                ),
                ("post", models.BooleanField(default=False, verbose_name="пост")),
                (
                    "post_od",
                    models.IntegerField(
                        blank=True,
                        help_text="Почетак поста у данима од Васкрса",
                        null=True,
                        verbose_name="почетак поста (дани)",
                    ),
                ),
                (
                    "post_do",
                    models.IntegerField(
                        blank=True,
                        help_text="Крај поста у данима од Васкрса",
                        null=True,
                        verbose_name="крај поста (дани)",
                    ),
                ),
                (
                    "crveno_slovo",
                    models.BooleanField(
                        default=False,
                        help_text="Велики празник (црвено слово у календару)",
                        verbose_name="црвено слово",
                    ),
                ),
            ],
            options={
                "verbose_name": "Слава",
                "verbose_name_plural": "Славе",
                "db_table": "slave",
                "managed": True,
            },
        ),
    ]
