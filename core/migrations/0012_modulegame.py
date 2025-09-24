"""Create ModuleGame model."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_update_modulelivemeeting_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModuleGame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=160)),
                ("description", models.TextField(blank=True)),
                (
                    "game_type",
                    models.CharField(
                        choices=[("letter-sequence", "Letter Sequence")],
                        default="letter-sequence",
                        max_length=32,
                    ),
                ),
                ("word", models.CharField(blank=True, max_length=64)),
                ("definition", models.TextField(blank=True)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="games",
                        to="core.coursemodule",
                    ),
                ),
            ],
            options={
                "ordering": ["module", "order"],
                "verbose_name": "Module game",
                "verbose_name_plural": "Module games",
            },
        ),
        migrations.AlterUniqueTogether(
            name="modulegame",
            unique_together={("module", "order")},
        ),
    ]

