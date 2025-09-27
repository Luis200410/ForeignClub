"""Admin configuration for core domain models."""
from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.forms import Media, inlineformset_factory
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

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


class ModuleGameAdminForm(forms.ModelForm):
    class Meta:
        model = models.ModuleGame
        fields = "__all__"

    class Media:
        js = ("core/admin/module_game.js",)

    def clean(self):
        cleaned = super().clean()
        game_type = cleaned.get("game_type")
        word = (cleaned.get("word") or "").strip()
        definition = (cleaned.get("definition") or "").strip()

        if game_type == models.ModuleGame.GameType.LETTER_SEQUENCE:
            if not word:
                self.add_error("word", "Provide a target word for the letter sequence game.")
            cleaned["word"] = word
            cleaned["definition"] = definition
        else:
            cleaned["word"] = ""
            cleaned["definition"] = ""

        if game_type == models.ModuleGame.GameType.ADAPTIVE_FLASHCARDS and cleaned.get("word"):
            cleaned["word"] = ""
        return cleaned


@admin.register(models.ModuleGame)
class ModuleGameAdmin(admin.ModelAdmin):
    form = ModuleGameAdminForm
    list_display = ("module", "order", "game_type", "title", "is_active")
    list_filter = ("game_type", "is_active", "module__course")
    search_fields = ("title", "module__title", "module__course__title")
    autocomplete_fields = ("module",)
    ordering = ("module", "order")
    inlines = []
    fieldsets = (
        ("Assignment", {"fields": ("module", "order", "game_type", "is_active")}),
        ("Presentation", {"fields": ("title", "description")}),
        (
            "Letter sequence settings",
            {
                "fields": ("word", "definition"),
                "classes": ("module-game-letter",),
            },
        ),
    )


class ModuleGameFlashcardInline(admin.TabularInline):
    model = models.ModuleGameFlashcard
    extra = 1
    fields = ("order", "word", "image_url", "audio_url", "is_active")
    ordering = ("order",)


ModuleGameAdmin.inlines = [ModuleGameFlashcardInline]


def _module_game_get_inline_instances(self, request, obj=None):
    if not obj or obj.game_type != models.ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
        return []
    return [inline(self, request) for inline in self.inlines]


ModuleGameAdmin.get_inline_instances = _module_game_get_inline_instances


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

    class Media:
        js = ("core/admin/flightdeck_activity.js",)

    def clean(self):
        cleaned_data = super().clean()
        slot = cleaned_data.get("slot")
        link_url = (cleaned_data.get("link_url") or "").strip()
        link_label = (cleaned_data.get("link_label") or "").strip()

        if slot == models.ModuleFlightDeckActivity.Slot.NOTEBOOK:
            if not link_url:
                self.add_error("link_url", "Provide the Notebook link for this module.")
            cleaned_data["link_label"] = link_label or "Open NotebookLM"
        else:
            cleaned_data["link_url"] = ""
            cleaned_data["link_label"] = ""
        return cleaned_data


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


class ModuleAfterburnerReadingChapterInline(admin.StackedInline):
    model = models.ModuleAfterburnerReadingChapter
    extra = 1
    fields = ("order", "title", "content")
    ordering = ("order", "id")
    classes = ("afterburner-inline", "afterburner-inline-reading")


class ModuleAfterburnerGrammarPointInline(admin.StackedInline):
    model = models.ModuleAfterburnerGrammarPoint
    extra = 1
    fields = ("order", "formula", "explanation")
    ordering = ("order", "id")
    classes = ("afterburner-inline", "afterburner-inline-grammar")


class AfterburnerActivityForm(forms.ModelForm):
    SLOT_LABEL_OVERRIDES = {
        models.ModuleAfterburnerActivity.Slot.TALK_RECORD: _("Talk-Record Challenge"),
        models.ModuleAfterburnerActivity.Slot.READING: _("Reading Sprint"),
        models.ModuleAfterburnerActivity.Slot.REAL_WORLD: _("Real World Challenge"),
        models.ModuleAfterburnerActivity.Slot.GRAMMAR: _("Grammar Snapshot"),
        models.ModuleAfterburnerActivity.Slot.GAME: _("Game Mission"),
    }

    class Meta:
        model = models.ModuleAfterburnerActivity
        fields = ("title", "description", "game", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.slot = kwargs.pop("slot", None) or getattr(kwargs.get("instance"), "slot", None)
        self.module = kwargs.pop("module", None) or getattr(kwargs.get("instance"), "module", None)
        super().__init__(*args, **kwargs)

        if self.slot:
            slot_label = self.SLOT_LABEL_OVERRIDES.get(self.slot, self.slot.replace("-", " ").title())
            self.fields["title"].label = _("Activity title")
            self.fields["title"].help_text = _("Displayed on the learner card for %(label)s.") % {
                "label": slot_label
            }
            self.fields["description"].label = _("Learner instructions")

        if self.slot != models.ModuleAfterburnerActivity.Slot.GAME:
            self.fields.pop("game", None)
        else:
            game_field = self.fields.get("game")
            if game_field:
                queryset = models.ModuleGame.objects.filter(module=self.module).order_by("order", "id")
                game_field.queryset = queryset
                game_field.required = False
                game_field.help_text = _("Pick the Vue game configuration to render for this module.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.slot:
            instance.slot = self.slot
        if self.module:
            instance.module = self.module
        if commit:
            instance.save()
            self.save_m2m()
        return instance


ReadingChapterFormSet = inlineformset_factory(
    models.ModuleAfterburnerActivity,
    models.ModuleAfterburnerReadingChapter,
    fields=("order", "title", "content"),
    extra=2,
    can_delete=True,
    widgets={
        "content": forms.Textarea(attrs={"rows": 3}),
    },
)


GrammarPointFormSet = inlineformset_factory(
    models.ModuleAfterburnerActivity,
    models.ModuleAfterburnerGrammarPoint,
    fields=("order", "formula", "explanation"),
    extra=2,
    can_delete=True,
    widgets={
        "explanation": forms.Textarea(attrs={"rows": 3}),
    },
)


@admin.register(models.ModuleAfterburnerStage)
class ModuleAfterburnerStageAdmin(admin.ModelAdmin):
    change_form_template = "admin/core/moduleafterburnerstage/change_form.html"
    list_display = ("course", "order", "title")
    list_select_related = ("course",)
    ordering = ("course", "order")
    search_fields = ("title", "course__title")
    list_filter = ("course",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("course")

    def _ensure_slot_activity(
        self,
        module: models.ModuleAfterburnerStage,
        slot: str,
    ) -> models.ModuleAfterburnerActivity:
        defaults = {
            "title": models.ModuleAfterburnerActivity.Slot(slot).label
            if hasattr(models.ModuleAfterburnerActivity.Slot(slot), "label")
            else slot.replace("-", " ").title(),
        }
        activity, _ = models.ModuleAfterburnerActivity.objects.get_or_create(
            module=module,
            slot=slot,
            defaults=defaults,
        )
        return activity

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        module = self.get_object(request, object_id)
        if module is None:
            return super().changeform_view(request, object_id, form_url, extra_context)

        slot_entries: list[dict[str, object]] = []
        slot_enum = models.ModuleAfterburnerActivity.Slot
        post_data = request.POST or None

        for slot_value, slot_label in slot_enum.choices:
            activity = self._ensure_slot_activity(module, slot_value)
            form = AfterburnerActivityForm(
                post_data,
                instance=activity,
                prefix=f"slot_{slot_value}",
                slot=slot_value,
                module=module,
            )

            chapters_formset = None
            grammar_formset = None

            if slot_value == slot_enum.READING:
                chapters_formset = ReadingChapterFormSet(
                    post_data,
                    instance=activity,
                    prefix=f"chapters_{slot_value}",
                )
            elif slot_value == slot_enum.GRAMMAR:
                grammar_formset = GrammarPointFormSet(
                    post_data,
                    instance=activity,
                    prefix=f"grammar_{slot_value}",
                )

            slot_entries.append(
                {
                    "slot": slot_value,
                    "label": slot_label,
                    "activity": activity,
                    "form": form,
                    "chapters_formset": chapters_formset,
                    "grammar_formset": grammar_formset,
                }
            )

        if request.method == "POST":
            forms_valid = True
            for entry in slot_entries:
                forms_valid = entry["form"].is_valid() and forms_valid
                if entry["chapters_formset"] is not None:
                    forms_valid = entry["chapters_formset"].is_valid() and forms_valid
                if entry["grammar_formset"] is not None:
                    forms_valid = entry["grammar_formset"].is_valid() and forms_valid

            if forms_valid:
                for entry in slot_entries:
                    activity_instance = entry["form"].save()
                    if entry["chapters_formset"] is not None:
                        entry["chapters_formset"].instance = activity_instance
                        entry["chapters_formset"].save()
                    if entry["grammar_formset"] is not None:
                        entry["grammar_formset"].instance = activity_instance
                        entry["grammar_formset"].save()

                messages.success(
                    request,
                    _("Afterburner activities for %(module)s have been updated.")
                    % {"module": module.title},
                )
                self.log_change(request, module, "Updated Afterburner stage")
                return redirect(request.path)

        media = Media()
        for entry in slot_entries:
            media = media + entry["form"].media
            if entry["chapters_formset"] is not None:
                media = media + entry["chapters_formset"].media
            if entry["grammar_formset"] is not None:
                media = media + entry["grammar_formset"].media

        context = {
            **self.admin_site.each_context(request),
            "title": _("Afterburner stage for %(module)s") % {"module": module.title},
            "module_obj": module,
            "forms_data": slot_entries,
            "media": media,
            "opts": self.model._meta,
            "original": module,
            "app_label": self.model._meta.app_label,
            "has_view_permission": self.has_view_permission(request, module),
            "has_change_permission": self.has_change_permission(request, module),
            "has_add_permission": self.has_add_permission(request),
            "has_delete_permission": self.has_delete_permission(request, module),
            "save_as": False,
            "save_on_top": False,
        }
        if extra_context:
            context.update(extra_context)

        return TemplateResponse(
            request,
            self.change_form_template,
            context,
        )


class ModuleLaunchPadTaskForm(forms.ModelForm):
    class Meta:
        model = models.ModuleLaunchPadTask
        fields = ("order", "is_active", "title", "description", "link_label", "link_url")

    def clean_link_url(self):
        url = (self.cleaned_data.get("link_url") or "").strip()
        if not url:
            raise forms.ValidationError("Provide a launch link for this task.")
        return url

    def clean_link_label(self):
        label = (self.cleaned_data.get("link_label") or "").strip()
        return label or "Open NotebookLM"

    def save(self, commit=True):
        instance = super().save(commit=False)
        activity = instance.activity
        if activity and not instance.order:
            existing = activity.tasks.count()
            instance.order = existing + 1
        if activity:
            instance.module = activity.module
        if commit:
            instance.save()
        return instance


class ModuleLaunchPadTaskInline(admin.StackedInline):
    model = models.ModuleLaunchPadTask
    form = ModuleLaunchPadTaskForm
    fk_name = "activity"
    extra = 1
    fields = ("order", "is_active", "title", "description", "link_label", "link_url")
    ordering = ("order", "id")


@admin.register(models.ModuleLaunchPadActivity)
class ModuleLaunchPadActivityAdmin(admin.ModelAdmin):
    list_display = ("module", "title", "is_active", "updated_at")
    list_filter = ("module__course", "is_active")
    search_fields = ("title", "module__title", "module__course__title")
    ordering = ("module",)
    inlines = (ModuleLaunchPadTaskInline,)
    fieldsets = (
        ("Assignment", {"fields": ("module", "is_active")}),
        ("Content", {"fields": ("title", "description")}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("module",)
        return ()


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
        (
            "Game configuration",
            {
                "fields": ("game",),
                "classes": ("collapse", "afterburner-game-config"),
            },
        ),
    )
    inlines = (ModuleAfterburnerReadingChapterInline, ModuleAfterburnerGrammarPointInline)

    def get_inline_instances(self, request, obj=None):  # pragma: no cover - admin hook
        instances = super().get_inline_instances(request, obj)
        if not obj:
            return []

        filtered = []
        for inline in instances:
            inline_model = getattr(inline, "model", None)
            if inline_model is models.ModuleAfterburnerReadingChapter and obj.slot != models.ModuleAfterburnerActivity.Slot.READING:
                continue
            if inline_model is models.ModuleAfterburnerGrammarPoint and obj.slot != models.ModuleAfterburnerActivity.Slot.GRAMMAR:
                continue
            filtered.append(inline)
        return filtered

    class Media:
        js = ("core/admin/afterburner_activity.js",)

    def get_model_perms(self, request):  # pragma: no cover - hides standalone admin entry
        return {}


class ModuleLaunchPadActivityInline(admin.StackedInline):
    model = models.ModuleLaunchPadActivity
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("title", "description", "is_active")
    show_change_link = True


@admin.register(models.CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "title", "focus_keyword")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("course", "order")
    inlines = (ModuleLaunchPadActivityInline, CourseSessionInline)


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
