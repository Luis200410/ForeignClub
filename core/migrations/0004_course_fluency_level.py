# Generated manually: add fluency_level to course.
from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_merge_course_domain"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="fluency_level",
            field=models.CharField(
                choices=[
                    ("A1", "Beginner (A1)"),
                    ("A2", "Elementary (A2)"),
                    ("B1", "Intermediate (B1)"),
                    ("B2", "Upper Intermediate (B2)"),
                    ("C1", "Advanced (C1)"),
                    ("C2", "Proficient (C2)"),
                ],
                default="B1",
                max_length=2,
            ),
        ),
    ]
