"""Data models for the FOREIGN platform."""
from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    """Supplementary profile information for each learner."""

    class FluencyLevel(models.TextChoices):
        BEGINNER = "A1", "Beginner (A1)"
        ELEMENTARY = "A2", "Elementary (A2)"
        INTERMEDIATE = "B1", "Intermediate (B1)"
        UPPER_INTERMEDIATE = "B2", "Upper Intermediate (B2)"
        ADVANCED = "C1", "Advanced (C1)"
        PROFICIENT = "C2", "Proficient (C2)"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=120)
    headline = models.CharField(max_length=180, blank=True)
    country = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    native_language = models.CharField(max_length=80, blank=True)
    target_focus = models.CharField(
        max_length=40,
        choices=[
            ("conversation", "Conversational agility"),
            ("career", "Career & business impact"),
            ("academic", "Academic excellence"),
            ("travel", "Travel confidence"),
            ("certification", "Certification readiness"),
        ],
        default="conversation",
    )
    desired_fluency_level = models.CharField(
        max_length=2,
        choices=FluencyLevel.choices,
        default=FluencyLevel.INTERMEDIATE,
    )
    bio = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self) -> str:
        return f"Profile for {self.user.get_username()}"


class LearningGoal(models.Model):
    """Goals that define what a learner wants to achieve."""

    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    class FocusArea(models.TextChoices):
        CONVERSATION = "conversation", "Conversation"
        PRONUNCIATION = "pronunciation", "Pronunciation"
        VOCABULARY = "vocabulary", "Vocabulary"
        GRAMMAR = "grammar", "Grammar"
        WRITING = "writing", "Writing"
        LEADERSHIP = "leadership", "Leadership"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="goals",
    )
    title = models.CharField(max_length=140)
    focus_area = models.CharField(max_length=40, choices=FocusArea.choices)
    success_metric = models.CharField(max_length=180)
    target_date = models.DateField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "target_date"]
        verbose_name = "Learning goal"
        verbose_name_plural = "Learning goals"
        constraints = [
            models.UniqueConstraint(
                fields=["profile"],
                condition=models.Q(is_primary=True),
                name="unique_primary_goal_per_profile",
                violation_error_message="Only one primary goal is allowed per profile.",
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_focus_area_display()})"


class AvailabilityWindow(models.Model):
    """Weekly recurring availability window for live experiences."""

    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="availability_windows",
    )
    day_of_week = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=64, default="UTC")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["profile", "day_of_week", "start_time"]
        verbose_name = "Availability window"
        verbose_name_plural = "Availability windows"
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F("start_time")),
                name="availability_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["profile", "day_of_week", "start_time", "end_time"],
                name="unique_availability_slot",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time} ({self.timezone})"


class InteractionPreference(models.Model):
    """Preferences to tailor how we engage the learner."""

    class SessionFormat(models.TextChoices):
        LIVE_EXPERIENCE = "live", "Live experiences"
        COACHING = "coaching", "1:1 coaching"
        GAMEPLAY = "gameplay", "Gameplay missions"
        ASYNCHRONOUS = "async", "Asynchronous challenges"

    class CommunicationChannel(models.TextChoices):
        EMAIL = "email", "Email"
        WHATSAPP = "whatsapp", "WhatsApp"
        TELEGRAM = "telegram", "Telegram"
        SMS = "sms", "SMS/Text"

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="interaction_preferences",
    )
    preferred_session_format = models.CharField(
        max_length=20,
        choices=SessionFormat.choices,
        default=SessionFormat.LIVE_EXPERIENCE,
    )
    preferred_group_size = models.PositiveSmallIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    availability_notes = models.TextField(blank=True)
    communication_channel = models.CharField(
        max_length=20,
        choices=CommunicationChannel.choices,
        default=CommunicationChannel.EMAIL,
    )
    notification_preferences = models.JSONField(default=dict, blank=True)
    consent_to_research = models.BooleanField(default=False)
    prefers_native_coach = models.BooleanField(default=True)
    prefers_peer_feedback = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Interaction preference"
        verbose_name_plural = "Interaction preferences"

    def __str__(self) -> str:
        return f"Preferences for {self.profile.display_name}"


class SkillAssessment(models.Model):
    """Record formal or informal assessments of a learner's skill."""

    class AssessmentType(models.TextChoices):
        PLACEMENT = "placement", "Placement"
        COACH_REVIEW = "coach_review", "Coach review"
        SELF_ASSESSMENT = "self", "Self assessment"
        GAMEPLAY = "gameplay", "Gameplay analytics"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    assessment_type = models.CharField(max_length=32, choices=AssessmentType.choices)
    fluency_level = models.CharField(
        max_length=2,
        choices=Profile.FluencyLevel.choices,
        default=Profile.FluencyLevel.INTERMEDIATE,
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    assessed_by = models.CharField(max_length=140, blank=True)
    assessed_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    evidence_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assessed_at"]
        indexes = [
            models.Index(fields=["profile", "assessed_at"], name="skill_assess_profile_idx"),
        ]
        verbose_name = "Skill assessment"
        verbose_name_plural = "Skill assessments"

    def __str__(self) -> str:
        return f"{self.get_assessment_type_display()} · {self.profile.display_name}"


class ProgressLog(models.Model):
    """Track qualitative insights and notable milestones for each learner."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="progress_logs",
    )
    summary = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    impact_rating = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    logged_by = models.CharField(max_length=120)
    logged_at = models.DateTimeField(default=timezone.now)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-logged_at"]
        verbose_name = "Progress log entry"
        verbose_name_plural = "Progress log entries"

    def __str__(self) -> str:
        return f"{self.summary} ({self.logged_at:%Y-%m-%d})"
