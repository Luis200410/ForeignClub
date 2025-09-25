"""Admin configuration for core domain models."""
from __future__ import annotations

from django import forms
from django.contrib import admin

from . import models


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "country", "desired_fluency_level", "created_at")
    list_filter = ("desired_fluency_level", "target_focus", "created_at")
    search_fields = ("display_name", "user__username", "user__email", "country", "native_language")
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.LearningGoal)
class LearningGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "profile", "focus_area", "priority", "is_primary", "target_date")
    list_filter = ("focus_area", "priority", "is_primary")
    search_fields = ("title", "profile__display_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.AvailabilityWindow)
class AvailabilityWindowAdmin(admin.ModelAdmin):
    list_display = ("profile", "day_of_week", "start_time", "end_time", "timezone")
    list_filter = ("day_of_week", "timezone")
    search_fields = ("profile__display_name",)


@admin.register(models.InteractionPreference)
class InteractionPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "preferred_session_format",
        "preferred_group_size",
        "communication_channel",
        "prefers_native_coach",
        "prefers_peer_feedback",
    )
    list_filter = (
        "preferred_session_format",
        "communication_channel",
        "prefers_native_coach",
        "prefers_peer_feedback",
    )
    search_fields = ("profile__display_name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.SkillAssessment)
class SkillAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "assessment_type",
        "fluency_level",
        "score",
        "assessed_by",
        "assessed_at",
    )
    list_filter = ("assessment_type", "fluency_level", "assessed_at")
    search_fields = ("profile__display_name", "assessed_by")
    autocomplete_fields = ("profile",)


@admin.register(models.ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ("profile", "summary", "impact_rating", "logged_by", "logged_at")
    list_filter = ("impact_rating", "logged_at")
    search_fields = ("summary", "profile__display_name", "logged_by")
    autocomplete_fields = ("profile",)
    readonly_fields = ("logged_at",)



class CourseModuleInline(admin.TabularInline):
    model = models.CourseModule
    extra = 1
    fields = ("order", "title", "focus_keyword")
    show_change_link = True
    ordering = ("order",)


class CourseSessionInline(admin.TabularInline):
    model = models.CourseSession
    extra = 1
    fields = ("order", "title", "session_type", "duration_minutes")
    ordering = ("order",)


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "delivery_mode",
        "difficulty",
        "fluency_level",
        "focus_area",
        "start_date",
        "end_date",
        "is_published",
    )
    list_filter = ("delivery_mode", "difficulty", "fluency_level", "is_published")
    search_fields = ("title", "subtitle", "summary", "focus_area")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (CourseModuleInline,)
    readonly_fields = ("created_at", "updated_at")


@admin.register(models.CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "title", "focus_keyword")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("course", "order")
    inlines = (CourseSessionInline,)


@admin.register(models.CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ("module", "order", "title", "session_type", "duration_minutes")
    list_filter = ("session_type", "module__course")
    search_fields = ("title", "module__course__title")
    ordering = ("module", "order")


@admin.register(models.CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("profile", "course", "status", "joined_at", "completion_rate")
    list_filter = ("status", "joined_at")
    search_fields = ("profile__display_name", "course__title")
    autocomplete_fields = ("profile", "course")
    readonly_fields = ("joined_at",)


@admin.register(models.ModuleLiveMeeting)
class ModuleLiveMeetingAdmin(admin.ModelAdmin):
    list_display = ("module", "scheduled_for", "duration_minutes", "title")
    list_filter = ("module__course", "scheduled_for")
    search_fields = ("title", "module__title", "module__course__title")
    autocomplete_fields = ("module",)
    ordering = ("module", "scheduled_for")


@admin.register(models.ModuleGame)
class ModuleGameAdmin(admin.ModelAdmin):
    list_display = ("module", "order", "game_type", "title", "is_active")
    list_filter = ("game_type", "is_active", "module__course")
    search_fields = ("title", "module__title", "module__course__title")
    autocomplete_fields = ("module",)
    ordering = ("module", "order")
    inlines = []


class ModuleGameFlashcardInline(admin.TabularInline):
    model = models.ModuleGameFlashcard
    extra = 1
    fields = ("order", "word", "image_url", "audio_url", "is_active")
    ordering = ("order",)


ModuleGameAdmin.inlines = [ModuleGameFlashcardInline]


@admin.register(models.ModuleGameFlashcard)
class ModuleGameFlashcardAdmin(admin.ModelAdmin):
    list_display = ("game", "order", "word", "is_active")
    list_filter = ("game__module__course", "is_active")
    search_fields = ("word", "game__module__title", "game__title")
    autocomplete_fields = ("game",)
    ordering = ("game", "order")


@admin.register(models.ModuleGameFlashcardProgress)
class ModuleGameFlashcardProgressAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "flashcard",
        "interval_index",
        "next_review_at",
        "correct_streak",
        "seen_count",
        "last_outcome",
    )
    list_filter = ("flashcard__game__module__course", "last_outcome")
    search_fields = ("profile__display_name", "flashcard__word")
    autocomplete_fields = ("profile", "flashcard")
    ordering = ("-next_review_at",)


@admin.register(models.ModuleGameFlashcardLog)
class ModuleGameFlashcardLogAdmin(admin.ModelAdmin):
    list_display = (
        "progress",
        "outcome",
        "streak_length",
        "time_spent_ms",
        "points_awarded",
        "recorded_at",
    )
    list_filter = ("outcome", "recorded_at")
    search_fields = (
        "progress__profile__display_name",
        "progress__flashcard__word",
    )
    autocomplete_fields = ("progress",)
    ordering = ("-recorded_at",)


class ModuleFlightDeckActivityAdminForm(forms.ModelForm):
    class Meta:
        model = models.ModuleFlightDeckActivity
        fields = "__all__"


class ModuleAfterburnerActivityAdminForm(forms.ModelForm):
    class Meta:
        model = models.ModuleAfterburnerActivity
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        game_field = self.fields.get("game")
        if not game_field:
            return

        queryset = models.ModuleGame.objects.filter(
            game_type=models.ModuleGame.GameType.ADAPTIVE_FLASHCARDS
        )
        module = self.instance.module if self.instance and self.instance.pk else None
        module_id = module.id if module else self.initial.get("module") or self.data.get("module")
        if module_id:
            try:
                queryset = queryset.filter(module_id=module_id)
            except (ValueError, TypeError):
                pass
            game_field.queryset = queryset
        else:
            game_field.queryset = queryset.none()
            game_field.help_text = "Select a module and save to load its available games."

    def clean(self):
        cleaned_data = super().clean()
        slot = cleaned_data.get("slot")
        game = cleaned_data.get("game")
        if slot == models.ModuleAfterburnerActivity.Slot.GAME and not game:
            self.add_error("game", "Select a game for the game slot.")
        if slot != models.ModuleAfterburnerActivity.Slot.GAME:
            cleaned_data["game"] = None
        return cleaned_data


@admin.register(models.ModuleFlightDeckActivity)
class ModuleFlightDeckActivityAdmin(admin.ModelAdmin):
    form = ModuleFlightDeckActivityAdminForm
    list_display = ("module", "slot", "title", "is_active", "updated_at")
    list_filter = ("slot", "is_active", "module__course")
    search_fields = ("title", "module__title", "module__course__title")
    autocomplete_fields = ("module",)
    ordering = ("module", "order")
    fieldsets = (
        ("Assignment", {"fields": ("module", "slot", "is_active", "order")}),
        ("Content", {"fields": ("title", "subtitle", "description")} ),
        ("Link", {"fields": ("link_label", "link_url"), "classes": ("collapse",)}),
    )


@admin.register(models.ModuleAfterburnerActivity)
class ModuleAfterburnerActivityAdmin(admin.ModelAdmin):
    form = ModuleAfterburnerActivityAdminForm
    list_display = ("module", "slot", "title", "game", "is_active", "updated_at")
    list_filter = ("slot", "is_active", "module__course")
    search_fields = ("title", "module__title", "module__course__title")
    autocomplete_fields = ("module", "game")
    ordering = ("module", "slot")
    fieldsets = (
        ("Assignment", {"fields": ("module", "slot", "is_active")}),
        ("Content", {"fields": ("title", "description")}),
        ("Game configuration", {"fields": ("game",), "classes": ("collapse",)}),
    )


@admin.register(models.ModuleLiveMeetingSignup)
class ModuleLiveMeetingSignupAdmin(admin.ModelAdmin):
    list_display = ("profile", "module", "meeting", "created_at")
    list_filter = ("module__course", "created_at")
    search_fields = ("profile__display_name", "module__title", "meeting__title")
    autocomplete_fields = ("profile", "module", "meeting")
    ordering = ("-created_at",)

admin.site.site_header = "FOREIGN Command Center"
admin.site.site_title = "FOREIGN Admin"
admin.site.index_title = "Operations Dashboard"


def _superuser_only(self, request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = _superuser_only.__get__(admin.site, admin.AdminSite)
