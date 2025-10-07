"""Admin configuration for core domain models."""
from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.forms import Media, inlineformset_factory
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
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


@admin.register(models.ModuleGame)
class ModuleGameAdmin(admin.ModelAdmin):
    list_display = ("module", "order", "game_type", "title", "is_active")
    list_filter = ("game_type", "is_active", "module__course")
    search_fields = ("title", "module__title", "module__course__title")
    autocomplete_fields = ("module",)
    ordering = ("module", "order")

    def get_model_perms(self, request):
        return {}


@admin.register(models.ModuleGameFlashcard)
class ModuleGameFlashcardAdmin(admin.ModelAdmin):
    list_display = ("game", "order", "word", "is_active")
    list_filter = ("game__module__course", "is_active")
    search_fields = ("word", "game__module__title", "game__title")
    autocomplete_fields = ("game",)
    ordering = ("game", "order")

    def get_model_perms(self, request):
        return {}


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

    def get_model_perms(self, request):
        return {}


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

    def get_model_perms(self, request):
        return {}


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


class ModuleAfterburnerRealWorldStepInline(admin.StackedInline):
    model = models.ModuleAfterburnerRealWorldStep
    extra = 1
    fields = ("order", "title", "instruction")
    ordering = ("order", "id")
    classes = ("afterburner-inline", "afterburner-inline-realworld")


class ModuleMeetingInstructionInline(admin.StackedInline):
    model = models.ModuleMeetingActivityInstruction
    extra = 1
    fields = ("order", "text")
    ordering = ("order", "id")
    classes = ("collapse",)


class MeetingActivityForm(forms.ModelForm):
    instructions_raw = forms.CharField(
        label=_("Instructions"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Enter one instruction per line; they will display in the learner carousel."),
    )

    class Meta:
        model = models.ModuleMeetingActivity
        fields = ("order", "title", "description", "grammar_formula", "example", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "example": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instructions = []
        if self.instance.pk:
            instructions = [
                instruction.text.strip()
                for instruction in self.instance.instructions.all().order_by("order", "id")
            ]
        self.initial["instructions_raw"] = "\n".join(instructions)
        self.fields["instructions_raw"].label = _("Instructions")
        self.fields["instructions_raw"].help_text = _("Enter each instruction on a new line.")

    def clean_order(self):
        value = self.cleaned_data.get("order")
        if not value or value <= 0:
            return 0
        return value


MeetingActivityFormSet = inlineformset_factory(
    models.CourseModule,
    models.ModuleMeetingActivity,
    form=MeetingActivityForm,
    extra=0,
    can_delete=True,
)

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
        fields = ("title", "goal", "description", "game", "is_active")
        widgets = {
            "goal": forms.TextInput(attrs={"class": "vTextField"}),
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

        goal_field = self.fields.get("goal")
        if goal_field:
            goal_field.label = _("Mission goal")
            if self.slot == models.ModuleAfterburnerActivity.Slot.REAL_WORLD:
                goal_field.help_text = _("Define the real-world outcome learners should achieve.")
            else:
                goal_field.help_text = _("Optional mission goal copied to the learner view.")

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
    extra=0,
    can_delete=True,
    widgets={
        "content": forms.Textarea(attrs={"rows": 3}),
    },
)


GrammarPointFormSet = inlineformset_factory(
    models.ModuleAfterburnerActivity,
    models.ModuleAfterburnerGrammarPoint,
    fields=("order", "formula", "explanation"),
    extra=0,
    can_delete=True,
    widgets={
        "explanation": forms.Textarea(attrs={"rows": 3}),
    },
)

RealWorldStepFormSet = inlineformset_factory(
    models.ModuleAfterburnerActivity,
    models.ModuleAfterburnerRealWorldStep,
    fields=("order", "title", "instruction"),
    extra=0,
    can_delete=True,
    widgets={
        "title": forms.TextInput(attrs={"class": "vTextField"}),
        "instruction": forms.Textarea(attrs={"rows": 3}),
    },
)


FlashcardFormSet = inlineformset_factory(
    models.ModuleGame,
    models.ModuleGameFlashcard,
    fields=("order", "word", "meaning", "is_active"),
    extra=0,
    can_delete=True,
    widgets={
        "order": forms.NumberInput(attrs={"class": "vIntegerField", "min": 1}),
        "word": forms.TextInput(attrs={"class": "vTextField"}),
        "meaning": forms.Textarea(attrs={"rows": 3}),
    },
)


class ModuleGameForm(forms.ModelForm):
    class Meta:
        model = models.ModuleGame
        fields = ("title", "description", "game_type", "is_active")

    def __init__(self, *args, module=None, **kwargs):
        self._module = module or kwargs.get("instance", None).module if kwargs.get("instance") else module
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["game_type"].disabled = True
        if len(self.fields["game_type"].choices) == 1:
            self.fields["game_type"].help_text = "Only adaptive flashcards are available right now."
        else:
            self.fields["game_type"].help_text = "Pick which game engine this configuration should use."

    def clean(self):
        cleaned = super().clean()
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self._module is not None:
            instance.module = self._module
        if commit:
            instance.save()
        return instance


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
            realworld_formset = None
            game_form = None
            flashcard_formset = None
            game_progress = []
            game_logs = []
            game_instance = None

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
            elif slot_value == slot_enum.REAL_WORLD:
                realworld_formset = RealWorldStepFormSet(
                    post_data,
                    instance=activity,
                    prefix=f"realworld_{slot_value}",
                )
            elif slot_value == slot_enum.GAME:
                defaults = {
                    "title": activity.title or f"{module.title} Vocabulary Deck",
                    "description": activity.description or "Adaptive flashcards to anchor this week’s vocabulary.",
                    "game_type": models.ModuleGame.GameType.ADAPTIVE_FLASHCARDS,
                }
                game_instance, _created = models.ModuleGame.objects.get_or_create(
                    module=module,
                    defaults=defaults,
                )
                if activity.game_id != game_instance.id:
                    activity.game = game_instance
                    activity.save(update_fields=["game", "updated_at"])
                game_form = ModuleGameForm(
                    post_data,
                    instance=game_instance,
                    prefix="game",
                    module=module,
                )
                flashcard_formset = FlashcardFormSet(
                    post_data,
                    instance=game_instance,
                    prefix="flashcards",
                )
                game_progress = list(
                    models.ModuleGameFlashcardProgress.objects.filter(
                        flashcard__game=game_instance
                    )
                    .select_related("profile", "flashcard")
                    .order_by("-updated_at")[:20]
                )
                game_logs = list(
                    models.ModuleGameFlashcardLog.objects.filter(
                        progress__flashcard__game=game_instance
                    )
                    .select_related("progress__profile", "progress__flashcard")
                    .order_by("-recorded_at")[:20]
                )

            slot_entries.append(
                {
                    "slot": slot_value,
                    "label": slot_label,
                    "activity": activity,
                    "form": form,
                    "chapters_formset": chapters_formset,
                    "grammar_formset": grammar_formset,
                    "realworld_formset": realworld_formset,
                    "game_form": game_form,
                    "flashcard_formset": flashcard_formset,
                    "game_progress": game_progress,
                    "game_logs": game_logs,
                    "game_instance": game_instance,
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
                if entry.get("realworld_formset") is not None:
                    forms_valid = entry["realworld_formset"].is_valid() and forms_valid
                if entry.get("game_form") is not None:
                    forms_valid = entry["game_form"].is_valid() and forms_valid
                if entry.get("flashcard_formset") is not None:
                    entry["flashcard_formset"].instance = entry["game_instance"]
                    forms_valid = entry["flashcard_formset"].is_valid() and forms_valid

            if forms_valid:
                for entry in slot_entries:
                    activity_instance = entry["form"].save()
                    entry["activity"] = activity_instance
                    if entry["chapters_formset"] is not None:
                        entry["chapters_formset"].instance = activity_instance
                        entry["chapters_formset"].save()
                    if entry["grammar_formset"] is not None:
                        entry["grammar_formset"].instance = activity_instance
                        entry["grammar_formset"].save()
                    if entry.get("realworld_formset") is not None:
                        entry["realworld_formset"].instance = activity_instance
                        entry["realworld_formset"].save()
                    if entry.get("game_form") is not None:
                        game_instance = entry["game_form"].save()
                        entry["game_instance"] = game_instance
                        if activity_instance.game_id != game_instance.id:
                            activity_instance.game = game_instance
                            activity_instance.save(update_fields=["game", "updated_at"])
                        flashcard_formset = entry.get("flashcard_formset")
                        if flashcard_formset is not None:
                            flashcard_formset.instance = game_instance
                            flashcard_formset.save()

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
            if entry.get("realworld_formset") is not None:
                media = media + entry["realworld_formset"].media
            if entry.get("game_form") is not None:
                media = media + entry["game_form"].media
            if entry.get("flashcard_formset") is not None:
                media = media + entry["flashcard_formset"].media

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
        ("Content", {"fields": ("title", "goal", "description")}),
        (
            "Game configuration",
            {
                "fields": ("game",),
                "classes": ("collapse", "afterburner-game-config"),
            },
        ),
    )
    inlines = (
        ModuleAfterburnerReadingChapterInline,
        ModuleAfterburnerGrammarPointInline,
        ModuleAfterburnerRealWorldStepInline,
    )

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
            if inline_model is models.ModuleAfterburnerRealWorldStep and obj.slot != models.ModuleAfterburnerActivity.Slot.REAL_WORLD:
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


@admin.register(models.ModuleMeetingActivity)
class ModuleMeetingActivityAdmin(admin.ModelAdmin):
    module_selection_template = "admin/core/modulemeetingactivity/module_selection.html"
    list_display = ("module", "order", "title", "is_active", "updated_at")
    list_filter = ("module__course", "is_active")
    search_fields = ("title", "module__title", "module__course__title")
    ordering = ("module", "order")
    autocomplete_fields = ("module",)
    fieldsets = (
        ("Assignment", {"fields": ("module", "order", "is_active")}),
        (
            "Slide content",
            {"fields": ("title", "description", "grammar_formula", "example")},
        ),
    )
    inlines = (ModuleMeetingInstructionInline,)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "module/<int:module_id>/manage/",
                self.admin_site.admin_view(self.manage_module_view),
                name="core_modulemeetingactivity_manage_module",
            )
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        return self._render_module_selector(
            request,
            extra_context=extra_context,
            title=_("Select a module to manage slides"),
        )

    def _render_module_selector(self, request, extra_context=None, title=None):
        modules = (
            models.CourseModule.objects.select_related("course")
            .order_by("course__title", "order")
        )
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "modules": modules,
            "title": title or _("Select a module to manage meeting activities"),
        }
        if extra_context:
            context.update(extra_context)
        return TemplateResponse(
            request,
            self.module_selection_template,
            context,
        )

    def add_view(self, request, form_url="", extra_context=None):
        module_id = request.GET.get("module")
        if module_id and str(module_id).isdigit():
            module = get_object_or_404(models.CourseModule, pk=module_id)
            return self._render_module_manager(request, module, extra_context)
        return self._render_module_selector(
            request,
            extra_context=extra_context,
            title=_("Select a module to create meeting activities"),
        )

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if obj is None:
            messages.error(request, _("Meeting slide not found."))
            return self._render_module_selector(request, extra_context)
        return self._render_module_manager(request, obj.module, extra_context)

    def manage_module_view(self, request, module_id):
        module = get_object_or_404(models.CourseModule, pk=module_id)
        return self._render_module_manager(request, module)

    def _render_module_manager(self, request, module, extra_context=None):
        formset = MeetingActivityFormSet(request.POST or None, instance=module, prefix="activities")

        if request.method == "POST":
            if formset.is_valid():
                formset.save(commit=False)
                prepared_entries: list[tuple[models.ModuleMeetingActivity, list[str]]] = []

                for form in formset.forms:
                    if not hasattr(form, "cleaned_data"):
                        continue
                    if form.cleaned_data.get("DELETE"):
                        if form.instance.pk:
                            form.instance.delete()
                        continue
                    if not form.has_changed():
                        continue

                    activity = form.save(commit=False)
                    activity.module = module
                    if activity.order <= 0:
                        max_order = (
                            models.ModuleMeetingActivity.objects.filter(module=module)
                            .exclude(pk=activity.pk)
                            .aggregate(Max("order"))
                            .get("order__max")
                            or 0
                        )
                        activity.order = max_order + 1
                    activity.save()
                    form.save_m2m()

                    instructions_raw = form.cleaned_data.get("instructions_raw", "")
                    lines = [line.strip() for line in instructions_raw.splitlines() if line.strip()]
                    prepared_entries.append((activity, lines))

                for obj in formset.deleted_objects:
                    obj.delete()

                for activity, lines in prepared_entries:
                    models.ModuleMeetingActivityInstruction.objects.filter(activity=activity).delete()
                    if lines:
                        models.ModuleMeetingActivityInstruction.objects.bulk_create(
                            [
                                models.ModuleMeetingActivityInstruction(
                                    activity=activity,
                                    order=index + 1,
                                    text=line,
                                )
                                for index, line in enumerate(lines)
                            ]
                        )

                formset.save_m2m()

                messages.success(
                    request,
                    _("Meeting activities for %(module)s have been updated.")
                    % {"module": module.title},
                )
                return redirect(request.path)
            else:
                messages.error(request, _("Please correct the highlighted errors."))

        available_modules = (
            models.CourseModule.objects.select_related("course")
            .order_by("course__title", "order")
        )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "module_obj": module,
            "activity_formset": formset,
            "activity_empty_form": formset.empty_form,
            "module_selection_url": reverse("admin:core_modulemeetingactivity_changelist"),
            "title": _("Meeting activities for %(module)s") % {"module": module.title},
            "module_selection_modules": available_modules,
            "current_path": request.path,
        }
        if extra_context:
            context.update(extra_context)

        return TemplateResponse(
            request,
            "admin/core/modulemeetingactivity/manage_module.html",
            context,
        )

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


@admin.register(models.ModuleMeetingPairing)
class ModuleMeetingPairingAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "activity",
        "primary_display",
        "partner_display",
        "paired_with_assistant",
        "created_at",
    )
    list_filter = ("meeting__module__course", "activity__module")
    search_fields = (
        "meeting__title",
        "activity__title",
        "profile_primary__display_name",
        "profile_partner__display_name",
    )
    raw_id_fields = ("meeting", "activity", "profile_primary", "profile_partner")
    ordering = ("-created_at",)

    def get_readonly_fields(self, request, obj=None):  # pragma: no cover - admin hook
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):  # pragma: no cover - admin hook
        return False

    def has_change_permission(self, request, obj=None):  # pragma: no cover
        return False

    def has_delete_permission(self, request, obj=None):  # pragma: no cover
        return False

    def primary_display(self, obj):  # pragma: no cover - admin display helper
        return obj.profile_primary.display_name

    primary_display.short_description = "Primary"

    def partner_display(self, obj):  # pragma: no cover - admin display helper
        if obj.paired_with_assistant or not obj.profile_partner_id:
            return "Assistant"
        return obj.profile_partner.display_name

    partner_display.short_description = "Partner"

admin.site.site_header = "FOREIGN Command Center"
admin.site.site_title = "FOREIGN Admin"
admin.site.index_title = "Operations Dashboard"


def _superuser_only(self, request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = _superuser_only.__get__(admin.site, admin.AdminSite)
