"""Create ModuleLiveMeeting model."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_modulestageprogress"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModuleLiveMeeting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Live mission", max_length=160)),
                ("scheduled_for", models.DateTimeField()),
                ("duration_minutes", models.PositiveSmallIntegerField(default=60)),
                ("agenda", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="live_meetings",
                        to="core.coursemodule",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="live_meetings",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["-scheduled_for"],
                "verbose_name": "Module live meeting",
                "verbose_name_plural": "Module live meetings",
            },
        ),
        migrations.AddIndex(
            model_name="modulelivemeeting",
            index=models.Index(fields=["profile", "module", "scheduled_for"], name="module_live_meeting_idx"),
        ),
    ]
