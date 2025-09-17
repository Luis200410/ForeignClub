# Generated manually for initial core domain schema.
from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=120)),
                ("headline", models.CharField(blank=True, max_length=180)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("timezone", models.CharField(default="UTC", max_length=64)),
                ("native_language", models.CharField(blank=True, max_length=80)),
                (
                    "target_focus",
                    models.CharField(
                        choices=[
                            ("conversation", "Conversational agility"),
                            ("career", "Career & business impact"),
                            ("academic", "Academic excellence"),
                            ("travel", "Travel confidence"),
                            ("certification", "Certification readiness"),
                        ],
                        default="conversation",
                        max_length=40,
                    ),
                ),
                (
                    "desired_fluency_level",
                    models.CharField(
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
                ("bio", models.TextField(blank=True)),
                ("linkedin_url", models.URLField(blank=True)),
                ("phone_number", models.CharField(blank=True, max_length=32)),
                ("onboarding_completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Profile",
                "verbose_name_plural": "Profiles",
            },
        ),
        migrations.CreateModel(
            name="InteractionPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "preferred_session_format",
                    models.CharField(
                        choices=[
                            ("live", "Live experiences"),
                            ("coaching", "1:1 coaching"),
                            ("gameplay", "Gameplay missions"),
                            ("async", "Asynchronous challenges"),
                        ],
                        default="live",
                        max_length=20,
                    ),
                ),
                (
                    "preferred_group_size",
                    models.PositiveSmallIntegerField(default=4, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(12)]),
                ),
                ("availability_notes", models.TextField(blank=True)),
                (
                    "communication_channel",
                    models.CharField(
                        choices=[
                            ("email", "Email"),
                            ("whatsapp", "WhatsApp"),
                            ("telegram", "Telegram"),
                            ("sms", "SMS/Text"),
                        ],
                        default="email",
                        max_length=20,
                    ),
                ),
                ("notification_preferences", models.JSONField(blank=True, default=dict)),
                ("consent_to_research", models.BooleanField(default=False)),
                ("prefers_native_coach", models.BooleanField(default=True)),
                ("prefers_peer_feedback", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interaction_preferences",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Interaction preference",
                "verbose_name_plural": "Interaction preferences",
            },
        ),
        migrations.CreateModel(
            name="LearningGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                (
                    "focus_area",
                    models.CharField(
                        choices=[
                            ("conversation", "Conversation"),
                            ("pronunciation", "Pronunciation"),
                            ("vocabulary", "Vocabulary"),
                            ("grammar", "Grammar"),
                            ("writing", "Writing"),
                            ("leadership", "Leadership"),
                        ],
                        max_length=40,
                    ),
                ),
                ("success_metric", models.CharField(max_length=180)),
                ("target_date", models.DateField(blank=True, null=True)),
                (
                    "priority",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Low"), (2, "Medium"), (3, "High")], default=2
                    ),
                ),
                ("is_primary", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="goals",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["-priority", "target_date"],
                "verbose_name": "Learning goal",
                "verbose_name_plural": "Learning goals",
            },
        ),
        migrations.CreateModel(
            name="AvailabilityWindow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "day_of_week",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "Monday"),
                            (2, "Tuesday"),
                            (3, "Wednesday"),
                            (4, "Thursday"),
                            (5, "Friday"),
                            (6, "Saturday"),
                            (7, "Sunday"),
                        ]
                    ),
                ),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("timezone", models.CharField(default="UTC", max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="availability_windows",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["profile", "day_of_week", "start_time"],
                "verbose_name": "Availability window",
                "verbose_name_plural": "Availability windows",
            },
        ),
        migrations.CreateModel(
            name="SkillAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "assessment_type",
                    models.CharField(
                        choices=[
                            ("placement", "Placement"),
                            ("coach_review", "Coach review"),
                            ("self", "Self assessment"),
                            ("gameplay", "Gameplay analytics"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "fluency_level",
                    models.CharField(
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
                ("score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("assessed_by", models.CharField(blank=True, max_length=140)),
                ("assessed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("notes", models.TextField(blank=True)),
                ("evidence_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assessments",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["-assessed_at"],
                "verbose_name": "Skill assessment",
                "verbose_name_plural": "Skill assessments",
            },
        ),
        migrations.CreateModel(
            name="ProgressLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("summary", models.CharField(max_length=200)),
                ("details", models.TextField(blank=True)),
                (
                    "impact_rating",
                    models.PositiveSmallIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
                ),
                ("logged_by", models.CharField(max_length=120)),
                ("logged_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("tags", models.JSONField(blank=True, default=list)),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="progress_logs",
                        to="core.profile",
                    ),
                ),
            ],
            options={
                "ordering": ["-logged_at"],
                "verbose_name": "Progress log entry",
                "verbose_name_plural": "Progress log entries",
            },
        ),
        migrations.AddConstraint(
            model_name="learninggoal",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_primary=True),
                fields=("profile",),
                name="unique_primary_goal_per_profile",
            ),
        ),
        migrations.AddConstraint(
            model_name="availabilitywindow",
            constraint=models.CheckConstraint(
                check=models.Q(end_time__gt=models.F("start_time")),
                name="availability_end_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="availabilitywindow",
            constraint=models.UniqueConstraint(
                fields=("profile", "day_of_week", "start_time", "end_time"),
                name="unique_availability_slot",
            ),
        ),
        migrations.AddIndex(
            model_name="skillassessment",
            index=models.Index(fields=["profile", "assessed_at"], name="skill_assess_profile_idx"),
        ),
    ]
