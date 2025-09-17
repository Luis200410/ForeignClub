# Merge migration to resolve parallel 0002 branches.
from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_learninggoal_unique_primary_goal_per_profile"),
        ("core", "0002_course_models"),
    ]

    operations = []
