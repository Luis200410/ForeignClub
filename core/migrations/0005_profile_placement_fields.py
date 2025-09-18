# Generated manually: add placement tracking fields to profile.
from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_course_fluency_level"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="placement_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="profile",
            name="placement_completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
