"""Admin configuration for core domain models."""
from __future__ import annotations

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
admin.site.site_header = "FOREIGN Command Center"
admin.site.site_title = "FOREIGN Admin"
admin.site.index_title = "Operations Dashboard"


def _superuser_only(self, request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = _superuser_only.__get__(admin.site, admin.AdminSite)
