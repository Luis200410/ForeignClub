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
    placement_completed = models.BooleanField(default=False)
    placement_completed_at = models.DateTimeField(null=True, blank=True)
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

class Course(models.Model):
    """Structured learning experience learners can join."""

    class DeliveryMode(models.TextChoices):
        LIVE = "live", "Live cohort"
        HYBRID = "hybrid", "Hybrid"
        SELF_PACED = "self_paced", "Self-paced"

    class Difficulty(models.TextChoices):
        FOUNDATION = "foundation", "Foundation"
        INTENSIVE = "intensive", "Intensive"
        MASTER = "master", "Mastery"

    slug = models.SlugField(unique=True, max_length=80)
    title = models.CharField(max_length=160)
    subtitle = models.CharField(max_length=220, blank=True)
    summary = models.TextField()
    delivery_mode = models.CharField(
        max_length=16,
        choices=DeliveryMode.choices,
        default=DeliveryMode.LIVE,
    )
    difficulty = models.CharField(
        max_length=16,
        choices=Difficulty.choices,
        default=Difficulty.FOUNDATION,
    )
    focus_area = models.CharField(max_length=60, default="Communication mastery")
    fluency_level = models.CharField(
        max_length=2,
        choices=Profile.FluencyLevel.choices,
        default=Profile.FluencyLevel.INTERMEDIATE,
    )
    duration_weeks = models.PositiveSmallIntegerField(default=6)
    weekly_commitment_hours = models.DecimalField(max_digits=4, decimal_places=1, default=3)
    cohort_size = models.PositiveSmallIntegerField(default=18)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    hero_image_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self) -> str:
        return self.title

    @property
    def is_cohort_based(self) -> bool:
        return self.delivery_mode != self.DeliveryMode.SELF_PACED


class CourseModule(models.Model):
    """Curriculum block inside a course."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="modules",
    )
    order = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    outcomes = models.TextField(blank=True)
    focus_keyword = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["course", "order"]
        verbose_name = "Course module"
        verbose_name_plural = "Course modules"
        unique_together = ("course", "order")

    def __str__(self) -> str:
        return f"{self.course.title} · Module {self.order}"


class CourseSession(models.Model):
    """Live or async session that sits inside a module."""

    class SessionType(models.TextChoices):
        LAB = "lab", "Immersion lab"
        WORKSHOP = "workshop", "Workshop"
        GAME = "game", "Game mission"
        COACHING = "coaching", "Coaching"
        DEBRIEF = "debrief", "Debrief"

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    order = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=160)
    session_type = models.CharField(
        max_length=16,
        choices=SessionType.choices,
        default=SessionType.LAB,
    )
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    description = models.TextField(blank=True)
    resources = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["module", "order"]
        verbose_name = "Course session"
        verbose_name_plural = "Course sessions"
        unique_together = ("module", "order")

    def __str__(self) -> str:
        return f"{self.module.course.title} · {self.title}"


class ModuleStageProgress(models.Model):
    """Track completion of stage tasks for a learner within a module."""

    class StageKey(models.TextChoices):
        LAUNCH_PAD = "launch-pad", "Launch Pad"
        FLIGHT_DECK = "flight-deck", "Flight Deck"
        AFTERBURNER = "afterburner", "Afterburner"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="stage_progress",
    )
    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="stage_progress",
    )
    stage_key = models.CharField(max_length=32, choices=StageKey.choices)
    completed_tasks = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "module", "stage_key")
        indexes = [
            models.Index(fields=["profile", "module", "stage_key"], name="stage_progress_idx"),
        ]
        verbose_name = "Module stage progress"
        verbose_name_plural = "Module stage progress"

    def __str__(self) -> str:
        return f"{self.profile.display_name} · {self.module} · {self.stage_key}"


class ModuleGame(models.Model):
    """Configurable learning games attached to a module's stage."""

    class GameType(models.TextChoices):
        LETTER_SEQUENCE = "letter-sequence", "Letter Sequence"
        ADAPTIVE_FLASHCARDS = "adaptive-flashcards", "Adaptive Flashcards"

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="games",
    )
    title = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    game_type = models.CharField(
        max_length=32,
        choices=GameType.choices,
        default=GameType.LETTER_SEQUENCE,
    )
    word = models.CharField(max_length=64, blank=True)
    definition = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "order"]
        verbose_name = "Module game"
        verbose_name_plural = "Module games"
        unique_together = ("module", "order")

    def __str__(self) -> str:
        base = self.title or dict(ModuleGame.GameType.choices).get(self.game_type, "Game")
        return f"{self.module} · {base}"


class ModuleGameFlashcard(models.Model):
    """Static flashcard content for adaptive flashcard games."""

    game = models.ForeignKey(
        ModuleGame,
        on_delete=models.CASCADE,
        related_name="flashcards",
    )
    order = models.PositiveSmallIntegerField(default=1)
    word = models.CharField(max_length=80)
    image_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["game", "order", "id"]
        verbose_name = "Adaptive flashcard"
        verbose_name_plural = "Adaptive flashcards"
        unique_together = ("game", "order")

    def __str__(self) -> str:
        return f"{self.game} · {self.word}"


class ModuleGameFlashcardProgress(models.Model):
    """Per-learner spaced repetition tracking for flashcard games."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="flashcard_progress",
    )
    flashcard = models.ForeignKey(
        ModuleGameFlashcard,
        on_delete=models.CASCADE,
        related_name="progress_entries",
    )
    interval_index = models.PositiveSmallIntegerField(default=0)
    next_review_at = models.DateTimeField()
    correct_streak = models.PositiveSmallIntegerField(default=0)
    seen_count = models.PositiveIntegerField(default=0)
    last_outcome = models.CharField(max_length=12, blank=True)
    total_points = models.PositiveIntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["profile", "flashcard"]
        unique_together = ("profile", "flashcard")
        verbose_name = "Adaptive flashcard progress"
        verbose_name_plural = "Adaptive flashcard progress"
        indexes = [
            models.Index(fields=["profile", "next_review_at"], name="flashcard_progress_due_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.profile.display_name} · {self.flashcard.word}"


class ModuleGameFlashcardLog(models.Model):
    """Analytics log for adaptive flashcard reviews."""

    progress = models.ForeignKey(
        ModuleGameFlashcardProgress,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    outcome = models.CharField(max_length=12)
    streak_length = models.PositiveSmallIntegerField(default=0)
    time_spent_ms = models.PositiveIntegerField(default=0)
    points_awarded = models.IntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name = "Adaptive flashcard log"
        verbose_name_plural = "Adaptive flashcard logs"

    def __str__(self) -> str:
        return f"{self.progress} · {self.outcome}"


class ModuleMeetingActivity(models.Model):
    """Planned activity inside a module meeting."""

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="meeting_activities",
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "order"]
        verbose_name = "Module meeting activity"
        verbose_name_plural = "Module meeting activities"
        unique_together = ("module", "order")

    def __str__(self) -> str:
        return f"{self.module} · {self.title}"


class ModuleFlightDeckActivity(models.Model):
    """Configurable cards for Flight Deck (stage two) activities."""

    class Slot(models.TextChoices):
        SCHEDULER = "scheduler", "Meeting Scheduler"
        NOTEBOOK = "notebook", "Notebook Prep"
        RECORDER = "recorder", "Mission Recorder"

    SLOT_DEFAULT_ORDER = {
        Slot.SCHEDULER: 1,
        Slot.NOTEBOOK: 2,
        Slot.RECORDER: 3,
    }

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="flightdeck_activities",
    )
    slot = models.CharField(max_length=32, choices=Slot.choices)
    title = models.CharField(max_length=160)
    subtitle = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    link_label = models.CharField(max_length=120, blank=True)
    link_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "order", "slot"]
        verbose_name = "Stage 2 · Flight Deck activity"
        verbose_name_plural = "Stage 2 · Flight Deck activities"
        unique_together = ("module", "slot")

    def __str__(self) -> str:
        return f"{self.module} · {self.get_slot_display()}"

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.SLOT_DEFAULT_ORDER.get(self.slot, self.order or 1)
        super().save(*args, **kwargs)


class ModuleAfterburnerActivity(models.Model):
    """Configurable cards for Afterburner (stage three) activities."""

    class Slot(models.TextChoices):
        TALK_RECORD = "talk-record", "Talk & Record"
        READING = "reading", "Read & Highlight"
        REAL_WORLD = "real-world", "Real World Challenge"
        GRAMMAR = "grammar", "Grammar Snapshot"
        GAME = "game", "Game Mission"

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="afterburner_activities",
    )
    slot = models.CharField(max_length=32, choices=Slot.choices)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    game = models.ForeignKey(
        ModuleGame,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="afterburner_activity",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module", "slot"]
        verbose_name = "Stage 3 · Afterburner activity"
        verbose_name_plural = "Stage 3 · Afterburner activities"
        unique_together = ("module", "slot")

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.slot == self.Slot.GAME and not self.game:
            raise ValidationError({"game": "Select a game for the Afterburner game slot."})
        if self.slot != self.Slot.GAME and self.game:
            raise ValidationError({"game": "Only the game slot can be linked to a game."})

    def __str__(self) -> str:
        return f"{self.module} · {self.get_slot_display()}"


class ModuleLiveMeeting(models.Model):
    """Admin-configured live meeting option for a module."""

    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="live_meeting_options",
    )
    title = models.CharField(max_length=160, blank=True)
    scheduled_for = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    agenda = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for"]
        verbose_name = "Module live meeting option"
        verbose_name_plural = "Module live meeting options"
        indexes = [
            models.Index(
                fields=["module", "scheduled_for"],
                name="module_live_meeting_idx",
            )
        ]

    def __str__(self) -> str:
        title = self.title or f"Live mission · Week {self.module.order}"
        return f"{self.module.course.title} · {title} · {self.scheduled_for:%Y-%m-%d %H:%M}"


class ModuleLiveMeetingSignup(models.Model):
    """Learner selection of a module's live meeting."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="live_meeting_signups",
    )
    module = models.ForeignKey(
        CourseModule,
        on_delete=models.CASCADE,
        related_name="live_meeting_signups",
    )
    meeting = models.ForeignKey(
        ModuleLiveMeeting,
        on_delete=models.CASCADE,
        related_name="signups",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "module")
        indexes = [
            models.Index(fields=["profile", "module"], name="module_live_signup_idx"),
        ]

    def save(self, *args, **kwargs):
        self.module = self.meeting.module
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.profile.display_name} · {self.module} · {self.meeting.scheduled_for:%Y-%m-%d %H:%M}"


class CourseEnrollment(models.Model):
    """Enrollment linking a learner profile to a course."""

    class EnrollmentStatus(models.TextChoices):
        APPLIED = "applied", "Applied"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        WITHDRAWN = "withdrawn", "Withdrawn"

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(
        max_length=12,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.APPLIED,
    )
    motivation = models.TextField(blank=True)
    joined_at = models.DateTimeField(default=timezone.now)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["-joined_at"]
        verbose_name = "Course enrollment"
        verbose_name_plural = "Course enrollments"
        unique_together = ("profile", "course")

    def __str__(self) -> str:
        return f"{self.profile.display_name} → {self.course.title}"

    @property
    def is_active(self) -> bool:
        return self.status in {self.EnrollmentStatus.APPLIED, self.EnrollmentStatus.ACTIVE}
