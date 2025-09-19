"""Create ModuleLiveMeetingSignup model."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_modulelivemeeting"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModuleLiveMeetingSignup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "meeting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="signups",
                        to="core.modulelivemeeting",
                    ),
                ),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="live_meeting_signups",
                        to="core.coursemodule",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="live_meeting_signups",
                        to="core.profile",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="modulelivemeetingsignup",
            index=models.Index(fields=["profile", "module"], name="module_live_signup_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="modulelivemeetingsignup",
            unique_together={("profile", "module")},
        ),
    ]

