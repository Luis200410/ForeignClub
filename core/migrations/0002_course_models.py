# Generated manually: add course domain models.
from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=160)),
                ("subtitle", models.CharField(blank=True, max_length=220)),
                ("summary", models.TextField()),
                (
                    "delivery_mode",
                    models.CharField(
                        choices=[
                            ("live", "Live cohort"),
                            ("hybrid", "Hybrid"),
                            ("self_paced", "Self-paced"),
                        ],
                        default="live",
                        max_length=16,
                    ),
                ),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("foundation", "Foundation"),
                            ("intensive", "Intensive"),
                            ("master", "Mastery"),
                        ],
                        default="foundation",
                        max_length=16,
                    ),
                ),
                ("focus_area", models.CharField(default="Communication mastery", max_length=60)),
                ("duration_weeks", models.PositiveSmallIntegerField(default=6)),
                ("weekly_commitment_hours", models.DecimalField(decimal_places=1, default=3, max_digits=4)),
                ("cohort_size", models.PositiveSmallIntegerField(default=18)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("hero_image_url", models.URLField(blank=True)),
                ("is_published", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["title"],
                "verbose_name": "Course",
                "verbose_name_plural": "Courses",
            },
        ),
        migrations.CreateModel(
            name="CourseModule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("title", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("outcomes", models.TextField(blank=True)),
                ("focus_keyword", models.CharField(blank=True, max_length=80)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="modules",
                        to="core.course",
                    ),
                ),
            ],
            options={
                "ordering": ["course", "order"],
                "verbose_name": "Course module",
                "verbose_name_plural": "Course modules",
                "unique_together": {("course", "order")},
            },
        ),
        migrations.CreateModel(
            name="CourseSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("title", models.CharField(max_length=160)),
                (
                    "session_type",
                    models.CharField(
                        choices=[
                            ("lab", "Immersion lab"),
                            ("workshop", "Workshop"),
                            ("game", "Game mission"),
                            ("coaching", "Coaching"),
                            ("debrief", "Debrief"),
                        ],
                        default="lab",
                        max_length=16,
                    ),
                ),
                ("duration_minutes", models.PositiveSmallIntegerField(default=60)),
                ("description", models.TextField(blank=True)),
                ("resources", models.JSONField(blank=True, default=list)),
                (
                    "module",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="core.coursemodule",
                    ),
                ),
            ],
            options={
                "ordering": ["module", "order"],
                "verbose_name": "Course session",
                "verbose_name_plural": "Course sessions",
                "unique_together": {("module", "order")},
            },
        ),
        migrations.CreateModel(
            name="CourseEnrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("applied", "Applied"),
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("withdrawn", "Withdrawn"),
                        ],
                        default="applied",
                        max_length=12,
                    ),
                ),
                ("motivation", models.TextField(blank=True)),
                ("joined_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("last_accessed_at", models.DateTimeField(blank=True, null=True)),
                ("completion_rate", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="core.course",
                    ),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["-joined_at"],
                "verbose_name": "Course enrollment",
                "verbose_name_plural": "Course enrollments",
                "unique_together": {("profile", "course")},
            },
        ),
    ]
