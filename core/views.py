"""Views powering the FOREIGN experience."""
import json
import random
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Prefetch, Count, Sum, F, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone, formats
from django.views import View
from django.views.generic import TemplateView

from .constants import DEFAULT_LAUNCH_PAD_TASKS, NOTEBOOK_LM_APP_URL
from .forms import (
    AccountForm,
    AvailabilityWindowForm,
    CourseEnrollmentForm,
    LearningGoalForm,
    PlacementExamForm,
    ProgressLogForm,
    SignUpForm,
    SkillAssessmentForm,
)
from .models import (
    Course,
    CourseEnrollment,
    CourseModule,
    ModuleGame,
    ModuleGameFlashcard,
    ModuleGameFlashcardLog,
    ModuleGameFlashcardProgress,
    ModuleLaunchPadTask,
    ModuleAfterburnerActivity,
    ModuleFlightDeckActivity,
    ModuleLiveMeeting,
    ModuleLiveMeetingSignup,
    ModuleMeetingActivity,
    ModuleMeetingPairing,
    ModuleStageProgress,
    Profile,
    SkillAssessment,
)

from .config import (
    AFTERBURNER_CARD_LIBRARY,
    AFTERBURNER_SLOT_SEQUENCE,
    ALLOWED_ENROLLMENT_STATUSES,
    FLIGHT_DECK_SLOT_SEQUENCE,
    FLIGHT_DECK_TASKS,
    LAUNCH_PAD_DEFAULT_TASKS,
    MEETING_ASSISTANT_URL,
    PROGRAM_LEVELS,
    PROGRAM_LOOKUP,
    PROGRAM_STAGE_DETAILS,
    STAGE_EXTENSION_MAP,
)
from .constants import (
    AFTERBURNER_GAME,
    FLASHCARD_SRS_INTERVALS,
    MODULE_STAGE_LOOKUP,
    MODULE_STAGE_SEQUENCE,
    NOTEBOOK_LM_APP_URL,
    POST_SESSION_TASKS,
)
from .services import (
    AccessService,
    ContentService,
    GamificationService,
    MeetingService,
    ProfileService,
)











class PlacementRequiredMixin(LoginRequiredMixin):
    placement_redirect_url = 'placement_exam'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(
                user=request.user,
                display_name=request.user.get_username(),
            )

        if not profile.placement_completed:
            current_url_name = getattr(request.resolver_match, "url_name", None)
            if current_url_name != self.placement_redirect_url:
                messages.info(request, "Complete the placement mission to unlock your FOREIGN arena.")
                return redirect(self.placement_redirect_url)

        return super().dispatch(request, *args, **kwargs)

def landing(request):
    """Landing page introducing the FOREIGN experience."""
    return render(
        request,
        "core/landing.html",
        {
            "stage_details": PROGRAM_STAGE_DETAILS,
            "landing_metrics": [
                {"value": "72%", "label": "of practice happens in small community circles"},
                {"value": "3 steps", "label": "per lesson keeps learning simple every week"},
                {"value": "38 cities", "label": "host FOREIGN community sessions today"},
            ],
        },
    )


class AuthLoginView(LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            existing_classes = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing_classes} form-control form-control-lg".strip()
            field.widget.attrs.setdefault('placeholder', field.label)
        return form



def logout_view(request):
    """Log the user out and return to the landing page instantly."""
    if request.user.is_authenticated:
        messages.info(request, "You are logged out. See you inside FOREIGN soon.")
        logout(request)
    return redirect("landing")


def register(request):
    """Handle account creation and automatic login."""
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to FOREIGN. Let's learn through real experiences.")
            return redirect("dashboard")
        messages.error(request, "Please correct the errors below and try again.")
    else:
        form = SignUpForm()
    return render(request, "core/register.html", {"form": form})


class DashboardView(PlacementRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    login_url = "login"
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        profile = getattr(user, "profile", None)
        context["profile"] = profile

        if profile is None:
            context["dashboard_ready"] = False
            return context

        goals_qs = profile.goals.all().order_by("-priority", "target_date")
        availability_qs = profile.availability_windows.all().order_by("day_of_week", "start_time")
        assessments_qs = profile.assessments.all().order_by("-assessed_at")
        progress_qs = profile.progress_logs.all().order_by("-logged_at")

        primary_goal = goals_qs.filter(is_primary=True).first()
        secondary_goals = goals_qs.exclude(pk=getattr(primary_goal, "pk", None))[:3]

        active_enrollments = list(
            profile.enrollments.select_related("course")
            .filter(
                status__in=[
                    CourseEnrollment.EnrollmentStatus.APPLIED,
                    CourseEnrollment.EnrollmentStatus.ACTIVE,
                ]
            )
            .order_by("-joined_at")
        )

        primary_course = active_enrollments[0].course if active_enrollments else None

        context.update(
            {
                "dashboard_ready": True,
                "primary_goal": primary_goal,
                "secondary_goals": list(secondary_goals),
                "availability_windows": list(availability_qs[:5]),
                "assessments": list(assessments_qs[:3]),
                "recent_progress": list(progress_qs[:3]),
                "interaction_preferences": getattr(profile, "interaction_preferences", None),
                "stats": {
                    "total_goals": goals_qs.count(),
                    "engagement_windows": availability_qs.count(),
                    "last_assessment": assessments_qs.first(),
                    "progress_notes": progress_qs.count(),
                },
                "active_enrollments": active_enrollments,
                "primary_course": primary_course,
            }
        )

        return context


class CourseListView(PlacementRequiredMixin, TemplateView):
    template_name = "core/courses/list.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = Course.objects.filter(is_published=True).order_by("title")
        profile = getattr(self.request.user, "profile", None)

        enrollments = {}
        if profile:
            enrollments = {en.course_id: en for en in profile.enrollments.select_related("course")}

        course_cards = [
            {
                "course": course,
                "enrollment": enrollments.get(course.id),
            }
            for course in courses
        ]

        context.update(
            {
                "courses": courses,
                "course_cards": course_cards,
            }
        )
        return context





class CourseDetailView(PlacementRequiredMixin, TemplateView):
    template_name = "core/courses/detail.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=kwargs["slug"],
            is_published=True,
        )
        enrollment, can_view_course = AccessService.get_enrollment_and_access(self.request.user, course)

        modules = (
            CourseModule.objects.filter(course=course)
            .prefetch_related("sessions")
            .order_by("order")
        )

        total_modules = modules.count()
        max_unlocked_order = 0
        if can_view_course and total_modules:
            completion_rate = float(getattr(enrollment, "completion_rate", 0) or 0)
            estimated_completed = int(
                max(0, min(total_modules, round((completion_rate / 100) * total_modules)))
            )
            max_unlocked_order = min(total_modules, max(1, estimated_completed + 1))

        module_cards = []
        for module in modules:
            weeks = {
                "module": module,
                "sessions": module.sessions.all(),
                "is_unlocked": module.order <= max_unlocked_order,
            }
            module_cards.append(weeks)

        context.update(
            {
                "course": course,
                "modules": module_cards,
                "enrollment": enrollment,
                "form": CourseEnrollmentForm(),
                "max_unlocked_order": max_unlocked_order,
                "can_view_course": can_view_course,
            }
        )
        return context




class CourseModuleDetailView(PlacementRequiredMixin, TemplateView):
    template_name = "core/modules/detail.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs["slug"]
        order = kwargs["order"]
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )

        user = self.request.user
        user_is_admin = user.is_superuser
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)

        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        if not user_is_admin and not AccessService.is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            previous_week = max(1, module.order - 1)
            messages.warning(
                self.request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)
        sessions_qs = module.sessions.all().order_by("order")
        sessions = list(sessions_qs)
        total_modules = course.modules.count()
        previous_order = order - 1 if order > 1 else None
        next_order = order + 1 if order < total_modules else None

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if user_is_admin:
            stage_unlocks = {stage["key"]: True for stage in MODULE_STAGE_SEQUENCE}

        stage_cards = [
            {
                **stage,
                "url": reverse(
                    "course_module_stage",
                    args=[course.slug, module.order, stage["key"]],
                ),
                "is_unlocked": stage_unlocks.get(stage["key"], False),
            }
            for stage in MODULE_STAGE_SEQUENCE
        ]

        context.update(
            {
                "course": course,
                "module": module,
                "sessions": sessions,
                "previous_order": previous_order,
                "next_order": next_order,
                "stage_cards": stage_cards,
                "stage_unlocks": stage_unlocks,
                "flight_deck_unlocked": stage_unlocks.get("flight-deck", False),
                "can_view_course": can_view_course,
            }
        )
        return context


class CourseModuleStageView(PlacementRequiredMixin, TemplateView):
    template_name = "core/modules/stage.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs["slug"]
        order = kwargs["order"]
        stage_key = kwargs["stage"]

        stage_config = MODULE_STAGE_LOOKUP.get(stage_key)
        if stage_config is None:
            raise Http404("Unknown module stage")

        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )
        user = self.request.user
        user_is_admin = user.is_superuser
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        if not user_is_admin and not AccessService.is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            previous_week = max(1, module.order - 1)
            messages.warning(
                self.request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)
        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if user_is_admin:
            stage_unlocks = {stage["key"]: True for stage in MODULE_STAGE_SEQUENCE}

        if not user_is_admin and stage_key != "launch-pad" and not stage_unlocks.get(
            stage_key, False
        ):
            messages.warning(self.request, "Complete the previous stage to unlock this mission.")
            return redirect("course_module", slug=slug, order=order)

        sessions_qs = module.sessions.all().order_by("order")
        sessions = list(sessions_qs)

        post_session_games = POST_SESSION_TASKS[:3]
        post_session_loops = POST_SESSION_TASKS[3:]

        stage_cards = [
            {
                **stage,
                "url": reverse(
                    "course_module_stage",
                    args=[course.slug, module.order, stage["key"]],
                ),
                "is_active": stage["key"] == stage_key,
                "is_unlocked": stage_unlocks.get(stage["key"], False),
            }
            for stage in MODULE_STAGE_SEQUENCE
        ]

        profile = ProfileService.resolve_profile(user, allow_admin_create=user_is_admin)
        meeting_signup = None
        selected_meeting = None
        can_cancel_meeting = False
        if profile is not None:
            meeting_signup = (
                ModuleLiveMeetingSignup.objects.filter(
                    profile=profile,
                    module=module,
                )
                .select_related("meeting")
                .first()
            )
            if meeting_signup and meeting_signup.meeting:
                selected_meeting = meeting_signup.meeting

        launch_configs = ContentService.get_launch_pad_task_configs(course, module)
        launch_progress = None
        if profile:
            launch_progress = ModuleStageProgress.objects.filter(
                profile=profile,
                module=module,
                stage_key=ModuleStageProgress.StageKey.LAUNCH_PAD,
            ).first()
        launch_completed_flags = list(launch_progress.completed_tasks or []) if launch_progress else []

        launch_tasks = [
            {
                "index": idx,
                "title": config.get("title", ""),
                "description": config.get("description", ""),
                "link_label": config.get("link_label", "Open NotebookLM"),
                "link_url": config.get("link_url") or NOTEBOOK_LM_APP_URL,
                "completed": bool(launch_completed_flags[idx - 1])
                if (idx - 1) < len(launch_completed_flags)
                else False,
            }
            for idx, config in enumerate(launch_configs, start=1)
        ]
        flight_deck_tasks = []
        meeting_activities_qs = (
            module.meeting_activities.filter(is_active=True)
            .prefetch_related("instructions")
            .order_by("order")
        )
        meeting_board: list[dict[str, object]] = []
        meeting_guides: list[dict[str, object]] = []
        afterburner_configs = ContentService.get_afterburner_card_configs(course, module)
        afterburner_cards: list[dict[str, object]] = []
        game_config: dict[str, object] | None = None
        afterburner_progress = None
        if profile:
            afterburner_progress = ModuleStageProgress.objects.filter(
                profile=profile,
                module=module,
                stage_key=ModuleStageProgress.StageKey.AFTERBURNER,
            ).first()
        ab_completed_flags = list(afterburner_progress.completed_tasks or []) if afterburner_progress else []

        for config in afterburner_configs:
            if config["slot"] == ModuleAfterburnerActivity.Slot.GAME:
                game_config = config
                continue
            
            card_index = len(afterburner_cards)
            is_completed = bool(ab_completed_flags[card_index]) if card_index < len(ab_completed_flags) else False

            afterburner_cards.append(
                {
                    "index": card_index + 1,
                    "title": config["title"],
                    "description": config["description"],
                    "completed": is_completed,
                    "slot": config["slot"],
                    "dashboard_url": None,
                    "goal": config.get("goal", ""),
                }
            )

        selected_game = None
        if game_config:
            if game_config.get("activity"):
                selected_game = getattr(game_config["activity"], "game", None)
            if selected_game is None:
                selected_game = game_config.get("game") or GamificationService.resolve_adaptive_game(module)

        afterburner_game_card = {
            "index": len(afterburner_cards) + 1,
            "title": (game_config or {}).get("title", AFTERBURNER_GAME["title"]),
            "description": (game_config or {}).get(
                "description", AFTERBURNER_GAME["description"]
            ),
            "completed": False,
            "slot": ModuleAfterburnerActivity.Slot.GAME,
            "game_type": selected_game.game_type if selected_game else ModuleGame.GameType.ADAPTIVE_FLASHCARDS,
            "word": "",
            "definition": "",
            "dashboard_url": None,
            "unlock_at": None,
            "is_locked": False,
            "lock_message": "",
            "goal": (game_config or {}).get("goal", ""),
        }

        now = timezone.now()

        meeting_end_dt = None
        meeting_end_local = None
        meeting_unlock_date = None
        meeting_tz = timezone.get_current_timezone()
        if selected_meeting:
            meeting_end_dt = selected_meeting.scheduled_for + timedelta(
                minutes=selected_meeting.duration_minutes or 60
            )
            if timezone.is_naive(meeting_end_dt):
                meeting_end_dt = timezone.make_aware(
                    meeting_end_dt, timezone.get_current_timezone()
                )
            meeting_end_local = timezone.localtime(meeting_end_dt)
            meeting_unlock_date = meeting_end_local.date()
            meeting_tz = meeting_end_local.tzinfo or timezone.get_current_timezone()

        slot_unlock_offsets = {
            ModuleAfterburnerActivity.Slot.TALK_RECORD: 1,
            ModuleAfterburnerActivity.Slot.READING: 3,
            ModuleAfterburnerActivity.Slot.REAL_WORLD: 5,
            ModuleAfterburnerActivity.Slot.GRAMMAR: 7,
        }

        for card in afterburner_cards:
            offset_days = slot_unlock_offsets.get(card["slot"], 0)
            if meeting_unlock_date is None:
                card["unlock_at"] = None
                if user_is_admin:
                    card["is_locked"] = False
                    card["lock_message"] = ""
                else:
                    card["is_locked"] = True
                    card["lock_message"] = "Schedule your live mission to unlock this mission."
                continue

            unlock_date = meeting_unlock_date + timedelta(days=offset_days)
            unlock_naive = datetime.combine(unlock_date, time.min)
            unlock_at = timezone.make_aware(unlock_naive, meeting_tz)
            card["unlock_at"] = timezone.localtime(unlock_at)
            is_locked = (now < unlock_at) and not user_is_admin
            card["is_locked"] = is_locked
            if is_locked:
                formatted = formats.date_format(card["unlock_at"], "M j, g:i a")
                card["lock_message"] = f"Unlocks on {formatted}"
            else:
                card["lock_message"] = ""

        game_props_for_stage = {}
        initial_flashcards: list[dict[str, str]] = []
        if selected_game:
            afterburner_game_card.update(
                {
                    "title": selected_game.title or afterburner_game_card["title"],
                    "description": selected_game.description
                    or afterburner_game_card["description"],
                    "game_type": selected_game.game_type,
                }
            )
            if selected_game.game_type == ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
                afterburner_game_card.update(
                    {
                        "flashcards_api": {
                            "queue": reverse(
                                "course_module_flashcards_queue",
                                args=[course.slug, module.order],
                            ),
                            "log": reverse(
                                "course_module_flashcards_log",
                                args=[course.slug, module.order],
                            ),
                            "analytics": reverse(
                                "course_module_flashcards_analytics",
                                args=[course.slug, module.order],
                            ),
                        }
                    }
                )
                initial_flashcards = [
                    {
                        "id": card.id,
                        "word": card.word,
                        "meaning": card.meaning,
                    }
                    for card in selected_game.flashcards.filter(is_active=True).order_by("order", "id")
                ]
                game_props_for_stage = {
                    "queueUrl": afterburner_game_card["flashcards_api"]["queue"],
                    "logUrl": afterburner_game_card["flashcards_api"]["log"],
                    "analyticsUrl": afterburner_game_card["flashcards_api"]["analytics"],
                }
                if initial_flashcards:
                    game_props_for_stage["initialCards"] = initial_flashcards
        afterburner_game_card["game_props_json"] = json.dumps(game_props_for_stage)
        for idx, card in enumerate(afterburner_cards, start=1):
            card["index"] = idx
            card["dashboard_url"] = reverse(
                "course_module_afterburner_dashboard",
                args=[course.slug, module.order, card["slot"]],
            )

        afterburner_game_card["index"] = len(afterburner_cards) + 1
        afterburner_game_card["dashboard_url"] = reverse(
            "course_module_afterburner_dashboard",
            args=[course.slug, module.order, ModuleAfterburnerActivity.Slot.GAME],
        )

        if selected_meeting:
            can_cancel_meeting = selected_meeting.scheduled_for - now >= timedelta(hours=48)

        existing_signup = meeting_signup
        meeting_options: list[ModuleLiveMeeting] = []
        show_meeting_carousel = False
        if stage_key == ModuleStageProgress.StageKey.FLIGHT_DECK:
            meeting_board = [
                {
                    "index": idx,
                    "title": activity.title,
                    "description": activity.description,
                }
                for idx, activity in enumerate(meeting_activities_qs, start=1)
            ]

            pairings_map: dict[int, dict[int, ModuleMeetingPairing]] = {}
            if (
                selected_meeting
                and course.fluency_level
                in {
                    Profile.FluencyLevel.BEGINNER,
                    Profile.FluencyLevel.ELEMENTARY,
                }
            ):
                pairings_map = MeetingService.ensure_meeting_pairings(module, selected_meeting)
                show_meeting_carousel = True

            for idx, activity in enumerate(meeting_activities_qs, start=1):
                instructions = [
                    instruction.text
                    for instruction in activity.instructions.all().order_by("order", "id")
                ]

                partner_payload: dict[str, object] | None = None
                if profile and pairings_map:
                    activity_pairs = pairings_map.get(activity.id, {})
                    pairing = activity_pairs.get(profile.id)
                    if pairing:
                        partner_profile = pairing.partner_for(profile)
                        if pairing.paired_with_assistant or not partner_profile:
                            partner_payload = {
                                "label": "Mission Assistant",
                                "is_assistant": True,
                            }
                        else:
                            partner_payload = {
                                "label": partner_profile.display_name,
                                "is_assistant": False,
                            }

                meeting_guides.append(
                    {
                        "index": idx,
                        "title": activity.title,
                        "summary": activity.description,
                        "grammar_formula": activity.grammar_formula,
                        "example": activity.example,
                        "instructions": instructions,
                        "partner": partner_payload,
                    }
                )
        
        if profile:
            if stage_key == ModuleStageProgress.StageKey.LAUNCH_PAD:
                progress, _ = ModuleStageProgress.objects.get_or_create(
                    profile=profile,
                    module=module,
                    stage_key=ModuleStageProgress.StageKey.LAUNCH_PAD,
                )
                tasks_state = list(progress.completed_tasks or [])
                required = len(launch_tasks)
                if len(tasks_state) < required:
                    tasks_state.extend([False] * (required - len(tasks_state)))
                elif len(tasks_state) > required:
                    tasks_state = tasks_state[:required]
                if progress.completed_tasks != tasks_state:
                    progress.completed_tasks = tasks_state
                    progress.save(update_fields=["completed_tasks", "updated_at"])
                for idx in range(1, required + 1):
                    launch_tasks[idx - 1]["completed"] = bool(tasks_state[idx - 1])
            elif stage_key == ModuleStageProgress.StageKey.FLIGHT_DECK:
                progress, _ = ModuleStageProgress.objects.get_or_create(
                    profile=profile,
                    module=module,
                    stage_key=ModuleStageProgress.StageKey.FLIGHT_DECK,
                )
                tasks_state = list(progress.completed_tasks or [])
                flight_configs = ContentService.get_flight_deck_activity_configs(module)
                required = len(flight_configs)
                if len(tasks_state) < required:
                    tasks_state.extend([False] * (required - len(tasks_state)))
                elif len(tasks_state) > required:
                    tasks_state = tasks_state[:required]
                scheduler_complete = bool(existing_signup)
                meeting_options = list(
                    ModuleLiveMeeting.objects.filter(module=module).order_by("scheduled_for")
                )
                if existing_signup:
                    selected_meeting = existing_signup.meeting
                    can_cancel_meeting = selected_meeting.scheduled_for - timezone.now() >= timedelta(hours=48)
                if scheduler_complete != bool(tasks_state[0]):
                    tasks_state[0] = scheduler_complete
                    progress.completed_tasks = tasks_state
                    progress.save(update_fields=["completed_tasks", "updated_at"])
                for idx, task in enumerate(flight_configs, start=1):
                    task_type = task.get("slot", ModuleFlightDeckActivity.Slot.NOTEBOOK)
                    entry = {
                        "index": idx,
                        "type": task_type,
                        "title": task["title"],
                        "subtitle": task.get("subtitle"),
                        "url": task.get("url"),
                        "link_label": task.get("link_label", "Open Link"),
                        "completed": tasks_state[idx - 1],
                    }
                    if task_type == ModuleFlightDeckActivity.Slot.SCHEDULER:
                        assistant_start = None
                        assistant_end = None
                        assistant_available = False
                        assistant_url = None
                        if selected_meeting:
                            assistant_start = selected_meeting.scheduled_for
                            assistant_end = assistant_start + timedelta(
                                minutes=selected_meeting.duration_minutes
                            )
                            now = timezone.now()
                            assistant_available = assistant_start <= now <= assistant_end
                            assistant_url = MEETING_ASSISTANT_URL
                        entry.update(
                            {
                                "meeting_options": meeting_options,
                                "selected_meeting_id": selected_meeting.id if selected_meeting else None,
                                "selected_meeting": selected_meeting,
                                "can_cancel": can_cancel_meeting,
                                "cancel_url": reverse(
                                    "course_module_meeting_cancel",
                                    args=[course.slug, module.order],
                                ),
                                "assistant_available": assistant_available,
                                "assistant_start": assistant_start,
                                "assistant_end": assistant_end,
                                "assistant_url": assistant_url,
                            }
                        )
                    flight_deck_tasks.append(entry)
            elif stage_key == ModuleStageProgress.StageKey.AFTERBURNER:
                progress, _ = ModuleStageProgress.objects.get_or_create(
                    profile=profile,
                    module=module,
                    stage_key=ModuleStageProgress.StageKey.AFTERBURNER,
                )
                tasks_state = list(progress.completed_tasks or [])
                required = AccessService.get_stage_required_tasks(ModuleStageProgress.StageKey.AFTERBURNER, module)
                if len(tasks_state) < required:
                    tasks_state.extend([False] * (required - len(tasks_state)))
                elif len(tasks_state) > required:
                    tasks_state = tasks_state[:required]

                for idx, card in enumerate(afterburner_cards, start=1):
                    card["index"] = idx
                    card["completed"] = bool(tasks_state[idx - 1])
                game_index = afterburner_game_card["index"]
                afterburner_game_card["completed"] = bool(tasks_state[game_index - 1])

        context.update(
            {
                "course": course,
                "module": module,
                "sessions": sessions,
                "stage": stage_config,
                "stage_key": stage_key,
                "stage_cards": stage_cards,
                "post_session_games": post_session_games,
                "post_session_loops": post_session_loops,
                "afterburner_cards": afterburner_cards,
                "afterburner_game_card": afterburner_game_card,
                "stage_unlocks": stage_unlocks,
                "launch_pad_tasks": launch_tasks,
                "flight_deck_tasks": flight_deck_tasks,
                "meeting_board": meeting_board,
                "meeting_guides": meeting_guides,
                "show_meeting_carousel": show_meeting_carousel,
                "selected_meeting": selected_meeting,
                "can_view_course": can_view_course,
            }
        )
        return context


class ModuleAfterburnerDashboardView(PlacementRequiredMixin, TemplateView):
    template_name = "core/modules/afterburner_dashboard.html"
    login_url = "login"

    def get(self, request, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = kwargs["slug"]
        order = kwargs["order"]
        slot = kwargs["slot"]

        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )
        user = request.user
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not AccessService.is_module_unlocked(user, course, module, enrollment, can_view_course):
            previous_week = max(1, module.order - 1)
            messages.warning(
                request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if not stage_unlocks.get(ModuleStageProgress.StageKey.AFTERBURNER, False):
            messages.warning(request, "Unlock Afterburner to view this dashboard.")
            return redirect("course_module", slug=slug, order=order)

        try:
            slot_enum = ModuleAfterburnerActivity.Slot(slot)
        except ValueError as exc:  # pragma: no cover - defensive
            raise Http404("Unknown afterburner slot") from exc

        activity = (
            ModuleAfterburnerActivity.objects.filter(module=module, slot=slot_enum)
            .select_related("game", "module")
            .first()
        )

        slot_label = (
            activity.get_slot_display() if activity else slot_enum.label if hasattr(slot_enum, 'label') else slot_enum
        )

        selected_game = None
        if slot_enum == ModuleAfterburnerActivity.Slot.GAME:
            if activity and activity.game:
                selected_game = activity.game
            else:
                selected_game = (
                    ModuleGame.objects.filter(module=module, is_active=True)
                    .order_by("order")
                    .first()
                )
            if selected_game is None or selected_game.game_type != ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
                # Fallback to any adaptive game tied to the module so the dashboard always has a queue.
                selected_game = GamificationService.resolve_adaptive_game(module)

        reading_chapters = []
        grammar_points = []
        real_world_steps = []
        real_world_goal = ""
        if activity:
            if slot_enum == ModuleAfterburnerActivity.Slot.READING:
                reading_chapters = list(
                    activity.reading_chapters.all().order_by("order", "id")
                )
            elif slot_enum == ModuleAfterburnerActivity.Slot.GRAMMAR:
                grammar_points = list(
                    activity.grammar_points.all().order_by("order", "id")
                )
            elif slot_enum == ModuleAfterburnerActivity.Slot.REAL_WORLD:
                real_world_steps = list(
                    activity.real_world_steps.all().order_by("order", "id")
                )
                real_world_goal = activity.goal or ""

        game_props = {}
        initial_flashcards: list[dict[str, str]] = []
        if slot_enum == ModuleAfterburnerActivity.Slot.GAME and selected_game:
            if selected_game.game_type == ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
                initial_flashcards = [
                    {
                        "id": card.id,
                        "word": card.word,
                        "meaning": card.meaning,
                    }
                    for card in selected_game.flashcards.filter(is_active=True).order_by("order", "id")
                ]
                game_props = {
                    "queueUrl": reverse(
                        "course_module_flashcards_queue",
                        args=[course.slug, module.order],
                    ),
                    "logUrl": reverse(
                        "course_module_flashcards_log",
                        args=[course.slug, module.order],
                    ),
                    "analyticsUrl": reverse(
                        "course_module_flashcards_analytics",
                        args=[course.slug, module.order],
                    ),
                }
                if initial_flashcards:
                    game_props["initialCards"] = initial_flashcards

        context.update(
            {
                "course": course,
                "module": module,
                "slot_enum": slot_enum,
                "slot_label": slot_label,
                "activity": activity,
                "selected_game": selected_game,
                "game_props_json": json.dumps(game_props),
                "game_slot_value": ModuleAfterburnerActivity.Slot.GAME,
                "talk_slot_value": ModuleAfterburnerActivity.Slot.TALK_RECORD,
                "reading_slot_value": ModuleAfterburnerActivity.Slot.READING,
                "grammar_slot_value": ModuleAfterburnerActivity.Slot.GRAMMAR,
                "real_world_slot_value": ModuleAfterburnerActivity.Slot.REAL_WORLD,
                "real_world_steps": real_world_steps,
                "real_world_goal": real_world_goal,
                "reading_chapters": reading_chapters,
                "grammar_points": grammar_points,
            }
        )
        return self.render_to_response(context)


class ModuleMeetingSignupView(PlacementRequiredMixin, View):
    login_url = "login"

    def post(self, request, slug: str, order: int):
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )
        user = request.user
        user_is_admin = user.is_superuser
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not AccessService.is_module_unlocked(user, course, module, enrollment, can_view_course):
            previous_week = max(1, module.order - 1)
            messages.warning(
                request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)

        profile = ProfileService.resolve_profile(user, allow_admin_create=user_is_admin)
        if profile is None:
            messages.error(request, "Complete your profile to track progress.")
            return redirect("course_module_stage", slug=slug, order=order, stage=ModuleStageProgress.StageKey.FLIGHT_DECK)

        meeting_id = request.POST.get("meeting_id")
        if not meeting_id:
            messages.error(request, "Select a meeting slot to continue.")
            return redirect(
                "course_module_stage",
                slug=slug,
                order=order,
                stage=ModuleStageProgress.StageKey.FLIGHT_DECK,
            )

        meeting = get_object_or_404(ModuleLiveMeeting, id=meeting_id, module=module)

        ModuleLiveMeetingSignup.objects.update_or_create(
            profile=profile,
            module=module,
            defaults={"meeting": meeting},
        )

        progress, _ = ModuleStageProgress.objects.get_or_create(
            profile=profile,
            module=module,
            stage_key=ModuleStageProgress.StageKey.FLIGHT_DECK,
        )
        tasks_state = list(progress.completed_tasks or [])
        required = AccessService.get_stage_required_tasks(ModuleStageProgress.StageKey.FLIGHT_DECK, module)
        if len(tasks_state) < required:
            tasks_state.extend([False] * (required - len(tasks_state)))
        tasks_state[0] = True
        progress.completed_tasks = tasks_state[:required]
        progress.save(update_fields=["completed_tasks", "updated_at"])

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            assistant_start_dt = meeting.scheduled_for
            assistant_end_dt = assistant_start_dt + timedelta(minutes=meeting.duration_minutes)
            assistant_available = assistant_start_dt <= timezone.now() <= assistant_end_dt
            return JsonResponse(
                {
                    "selected_meeting": {
                        "id": meeting.id,
                        "title": meeting.title,
                        "scheduled_for": timezone.localtime(meeting.scheduled_for).strftime("%b %d, %Y · %H:%M"),
                        "duration_minutes": meeting.duration_minutes,
                        "can_cancel": meeting.scheduled_for - timezone.now() >= timedelta(hours=48),
                        "assistant_start": timezone.localtime(assistant_start_dt).isoformat(),
                        "assistant_end": timezone.localtime(assistant_end_dt).isoformat(),
                        "assistant_available": assistant_available,
                        "assistant_url": MEETING_ASSISTANT_URL,
                    },
                    "stage_unlocks": stage_unlocks,
                }
            )

        messages.success(request, "Live mission locked in. See you in Flight Deck.")
        return redirect(
            "course_module_stage",
            slug=slug,
            order=order,
            stage=ModuleStageProgress.StageKey.FLIGHT_DECK,
        )


class ModuleMeetingCancelView(PlacementRequiredMixin, View):
    login_url = "login"

    def post(self, request, slug: str, order: int):
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )
        user = request.user
        user_is_admin = user.is_superuser
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not AccessService.is_module_unlocked(user, course, module, enrollment, can_view_course):
            previous_week = max(1, module.order - 1)
            messages.warning(
                request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)

        profile = getattr(user, "profile", None)
        if profile is None:
            messages.error(request, "Complete your profile to track progress.")
            return redirect("course_module_stage", slug=slug, order=order, stage=ModuleStageProgress.StageKey.FLIGHT_DECK)

        signup = ModuleLiveMeetingSignup.objects.filter(profile=profile, module=module).select_related("meeting").first()
        if signup is None:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"error": "not_registered"}, status=400)
            messages.info(request, "You are not booked for this mission.")
            return redirect(
                "course_module_stage",
                slug=slug,
                order=order,
                stage=ModuleStageProgress.StageKey.FLIGHT_DECK,
            )

        meeting = signup.meeting
        meeting_id = request.POST.get("meeting_id")
        if meeting_id and str(meeting.id) != str(meeting_id):
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"error": "mismatch"}, status=400)
            messages.error(request, "We couldn't match that booking. Please refresh and try again.")
            return redirect(
                "course_module_stage",
                slug=slug,
                order=order,
                stage=ModuleStageProgress.StageKey.FLIGHT_DECK,
            )

        if meeting.scheduled_for - timezone.now() < timedelta(hours=48):
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"error": "window_closed"}, status=400)
            messages.error(request, "Changes within 48 hours require a fee. Contact support to adjust.")
            return redirect(
                "course_module_stage",
                slug=slug,
                order=order,
                stage=ModuleStageProgress.StageKey.FLIGHT_DECK,
            )

        signup.delete()

        progress, _ = ModuleStageProgress.objects.get_or_create(
            profile=profile,
            module=module,
            stage_key=ModuleStageProgress.StageKey.FLIGHT_DECK,
        )
        tasks_state = list(progress.completed_tasks or [])
        required = AccessService.get_stage_required_tasks(ModuleStageProgress.StageKey.FLIGHT_DECK, module)
        if len(tasks_state) < required:
            tasks_state.extend([False] * (required - len(tasks_state)))
        tasks_state[0] = False
        progress.completed_tasks = tasks_state[:required]
        progress.save(update_fields=["completed_tasks", "updated_at"])

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "stage_unlocks": stage_unlocks,
                }
            )

        messages.info(request, "You're no longer booked. Choose another slot when you're ready.")
        return redirect(
            "course_module_stage",
            slug=slug,
            order=order,
            stage=ModuleStageProgress.StageKey.FLIGHT_DECK,
        )


class ModuleGameFlashcardQueueView(PlacementRequiredMixin, View):
    """Return the due flashcard queue for the adaptive flashcard game."""

    login_url = "login"

    def get(self, request, slug: str, order: int):
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )

        user = request.user
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            return JsonResponse(
                {"redirect_url": reverse("course_detail", args=[course.slug])},
                status=403,
            )

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not user.is_superuser and not AccessService.is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            return JsonResponse({"error": "module_locked"}, status=403)

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if not user.is_superuser and not stage_unlocks.get(
            ModuleStageProgress.StageKey.AFTERBURNER, False
        ):
            return JsonResponse({"error": "afterburner_locked"}, status=403)

        game_activity = (
            module.afterburner_activities.filter(
                slot=ModuleAfterburnerActivity.Slot.GAME,
                is_active=True,
            )
            .select_related("game")
            .first()
        )
        module_game = getattr(game_activity, "game", None)
        if module_game is None or module_game.game_type != ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
            module_game = GamificationService.resolve_adaptive_game(module)
        if not module_game:
            return JsonResponse({"cards": [], "meta": {"total_due": 0}}, status=200)

        profile = ProfileService.resolve_profile(user, allow_admin_create=True)
        if profile is None:
            return JsonResponse({"error": "profile_missing"}, status=403)

        progress_map = GamificationService.ensure_flashcard_progress_map(profile, module_game)
        now = timezone.now()

        due_progresses = [
            progress
            for progress in progress_map.values()
            if progress.flashcard.is_active and progress.next_review_at <= now
        ]

        random.shuffle(due_progresses)

        cards_payload = [
            {
                "id": progress.flashcard_id,
                "word": progress.flashcard.word,
                "meaning": progress.flashcard.meaning,
                "interval_index": progress.interval_index,
                "correct_streak": progress.correct_streak,
                "seen_count": progress.seen_count,
                "last_outcome": progress.last_outcome,
            }
            for progress in due_progresses
        ]

        meta = {
            "total_due": len(cards_payload),
            "total_active": module_game.flashcards.filter(is_active=True).count(),
        }

        return JsonResponse({"cards": cards_payload, "meta": meta})


class ModuleGameFlashcardLogView(PlacementRequiredMixin, View):
    """Handle learner outcomes for adaptive flashcard interactions."""

    login_url = "login"

    def post(self, request, slug: str, order: int):
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            payload = {}

        card_id = payload.get("card_id")
        outcome = payload.get("outcome")
        time_spent_ms = int(payload.get("time_spent_ms") or 0)
        streak_length = int(payload.get("streak_length") or 0)
        points_awarded = int(payload.get("points_awarded") or 0)

        if not card_id or outcome not in {"knew", "didnt"}:
            return JsonResponse({"error": "invalid_payload"}, status=400)

        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )

        user = request.user
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            return JsonResponse(
                {"redirect_url": reverse("course_detail", args=[course.slug])},
                status=403,
            )

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not user.is_superuser and not AccessService.is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            return JsonResponse({"error": "module_locked"}, status=403)

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if not user.is_superuser and not stage_unlocks.get(
            ModuleStageProgress.StageKey.AFTERBURNER, False
        ):
            return JsonResponse({"error": "afterburner_locked"}, status=403)

        game_activity = (
            module.afterburner_activities.filter(
                slot=ModuleAfterburnerActivity.Slot.GAME,
                is_active=True,
            )
            .select_related("game")
            .first()
        )
        module_game = getattr(game_activity, "game", None)
        if module_game is None or module_game.game_type != ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
            module_game = GamificationService.resolve_adaptive_game(module)
        if not module_game:
            return JsonResponse({"error": "game_unavailable"}, status=400)

        profile = ProfileService.resolve_profile(user, allow_admin_create=True)
        if profile is None:
            return JsonResponse({"error": "profile_missing"}, status=403)

        flashcard = get_object_or_404(
            ModuleGameFlashcard,
            id=card_id,
            game=module_game,
        )

        with transaction.atomic():
            try:
                progress = ModuleGameFlashcardProgress.objects.select_for_update().get(
                    profile=profile,
                    flashcard=flashcard,
                )
            except ModuleGameFlashcardProgress.DoesNotExist:
                progress = ModuleGameFlashcardProgress.objects.create(
                    profile=profile,
                    flashcard=flashcard,
                    next_review_at=timezone.now(),
                )

            now = timezone.now()
            previous_index = progress.interval_index
            previous_streak = progress.correct_streak

            if outcome == "knew":
                interval_index = min(previous_index + 1, len(FLASHCARD_SRS_INTERVALS) - 1)
                correct_streak = previous_streak + 1
                last_outcome = "correct"
            else:
                interval_index = max(previous_index - 1, 0)
                correct_streak = 0
                last_outcome = "incorrect"

            next_interval = GamificationService.flashcard_interval_for_index(interval_index)

            progress.interval_index = interval_index
            progress.next_review_at = now + next_interval
            progress.correct_streak = correct_streak
            progress.seen_count += 1
            progress.last_outcome = last_outcome
            progress.total_points = max(0, progress.total_points + max(points_awarded, 0))
            progress.last_reviewed_at = now
            progress.save(
                update_fields=[
                    "interval_index",
                    "next_review_at",
                    "correct_streak",
                    "seen_count",
                    "last_outcome",
                    "total_points",
                    "last_reviewed_at",
                    "updated_at",
                ]
            )

            ModuleGameFlashcardLog.objects.create(
                progress=progress,
                outcome=last_outcome,
                streak_length=max(streak_length, correct_streak if outcome == "knew" else 0),
                time_spent_ms=max(time_spent_ms, 0),
                points_awarded=points_awarded,
            )

        remaining_due = ModuleGameFlashcardProgress.objects.filter(
            profile=profile,
            flashcard__game=module_game,
            next_review_at__lte=timezone.now(),
            flashcard__is_active=True,
        ).count()

        return JsonResponse(
            {
                "progress": {
                    "interval_index": progress.interval_index,
                    "next_review_at": progress.next_review_at.isoformat(),
                    "correct_streak": progress.correct_streak,
                    "seen_count": progress.seen_count,
                    "total_points": progress.total_points,
                    "last_outcome": progress.last_outcome,
                },
                "remaining_due": remaining_due,
            }
        )


class ModuleGameFlashcardAnalyticsView(PlacementRequiredMixin, View):
    """Return per-learner flashcard analytics for the adaptive game."""

    login_url = "login"

    def get(self, request, slug: str, order: int):
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )

        user = request.user
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            return JsonResponse(
                {"redirect_url": reverse("course_detail", args=[course.slug])},
                status=403,
            )

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not user.is_superuser and not AccessService.is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            return JsonResponse({"error": "module_locked"}, status=403)

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if not user.is_superuser and not stage_unlocks.get(
            ModuleStageProgress.StageKey.AFTERBURNER, False
        ):
            return JsonResponse({"error": "afterburner_locked"}, status=403)

        game_activity = (
            module.afterburner_activities.filter(
                slot=ModuleAfterburnerActivity.Slot.GAME,
                is_active=True,
            )
            .select_related("game")
            .first()
        )
        module_game = getattr(game_activity, "game", None)
        if module_game is None or module_game.game_type != ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
            module_game = GamificationService.resolve_adaptive_game(module)
        if not module_game:
            return JsonResponse({"error": "game_unavailable"}, status=400)

        profile = ProfileService.resolve_profile(user, allow_admin_create=True)
        if profile is None:
            return JsonResponse({"error": "profile_missing"}, status=403)

        now = timezone.now()
        progress_qs = ModuleGameFlashcardProgress.objects.filter(
            profile=profile,
            flashcard__game=module_game,
            flashcard__is_active=True,
        ).select_related("flashcard")

        logs_qs = ModuleGameFlashcardLog.objects.filter(progress__in=progress_qs)

        total_reviews = logs_qs.count()
        correct_reviews = logs_qs.filter(outcome="correct").count()
        incorrect_reviews = logs_qs.filter(outcome="incorrect").count()

        progress_totals = progress_qs.aggregate(
            total_points=Sum("total_points"),
            total_seen=Count("id", filter=Q(seen_count__gt=0)),
            due_now=Count("id", filter=Q(next_review_at__lte=now)),
        )

        most_missed = list(
            logs_qs.filter(outcome="incorrect")
            .values(
                "progress__flashcard_id",
                "progress__flashcard__word",
                "progress__flashcard__meaning",
            )
            .annotate(missed_count=Count("id"))
            .order_by("-missed_count", "progress__flashcard__word")[:8]
        )

        recent = list(
            logs_qs.order_by("-recorded_at")
            .values(
                word=F("progress__flashcard__word"),
                outcome=F("outcome"),
                recorded_at=F("recorded_at"),
                streak_length=F("streak_length"),
                points_awarded=F("points_awarded"),
            )[:6]
        )

        payload = {
            "stats": {
                "total_active": module_game.flashcards.filter(is_active=True).count(),
                "total_seen": progress_totals.get("total_seen") or 0,
                "due_now": progress_totals.get("due_now") or 0,
                "total_points": progress_totals.get("total_points") or 0,
                "total_reviews": total_reviews,
                "correct_reviews": correct_reviews,
                "incorrect_reviews": incorrect_reviews,
                "accuracy": round((correct_reviews / total_reviews) * 100, 1)
                if total_reviews
                else 0.0,
            },
            "missed_words": [
                {
                    "id": entry["progress__flashcard_id"],
                    "word": entry["progress__flashcard__word"],
                    "meaning": entry["progress__flashcard__meaning"],
                    "missed_count": entry["missed_count"],
                }
                for entry in most_missed
            ],
            "recent_activity": [
                {
                    "word": row["word"],
                    "outcome": row["outcome"],
                    "recorded_at": row["recorded_at"].isoformat()
                    if hasattr(row["recorded_at"], "isoformat")
                    else row["recorded_at"],
                    "streak_length": row["streak_length"],
                    "points_awarded": row["points_awarded"],
                }
                for row in recent
            ],
        }

        return JsonResponse(payload)

class ModuleStageTaskToggleView(PlacementRequiredMixin, View):
    login_url = "login"

    def post(self, request, slug: str, order: int, stage: str, index: int):
        stage_key = stage
        allowed_stage_keys = {
            ModuleStageProgress.StageKey.LAUNCH_PAD,
            ModuleStageProgress.StageKey.FLIGHT_DECK,
            ModuleStageProgress.StageKey.AFTERBURNER,
        }
        if stage_key not in allowed_stage_keys:
            raise Http404

        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )
        user = request.user
        user_is_admin = user.is_superuser
        enrollment, can_view_course = AccessService.get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        if not user_is_admin and not AccessService.is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            previous_week = max(1, module.order - 1)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "error": "Module locked",
                        "redirect_url": reverse(
                            "course_module",
                            args=[course.slug, previous_week],
                        ),
                    },
                    status=403,
                )
            messages.warning(
                request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)

        profile = ProfileService.resolve_profile(user, allow_admin_create=user_is_admin)

        progress, _ = ModuleStageProgress.objects.get_or_create(
            profile=profile,
            module=module,
            stage_key=stage_key,
        )

        tasks_state = list(progress.completed_tasks or [])
        required = AccessService.get_stage_required_tasks(stage_key, module)
        if len(tasks_state) < required:
            tasks_state.extend([False] * (required - len(tasks_state)))
        elif len(tasks_state) > required:
            tasks_state = tasks_state[:required]

        if index < 1 or index > required:
            raise Http404

        if stage_key == ModuleStageProgress.StageKey.FLIGHT_DECK and index == 1:
            raise Http404

        if stage_key == ModuleStageProgress.StageKey.AFTERBURNER:
            now = timezone.now()
            afterburner_configs = ContentService.get_afterburner_card_configs(course, module)
            non_game_configs: list[dict[str, object]] = []
            game_config: dict[str, object] | None = None
            for config in afterburner_configs:
                if config["slot"] == ModuleAfterburnerActivity.Slot.GAME:
                    game_config = config
                else:
                    non_game_configs.append(config)

            slot_unlock_offsets = {
                ModuleAfterburnerActivity.Slot.TALK_RECORD: 1,
                ModuleAfterburnerActivity.Slot.READING: 3,
                ModuleAfterburnerActivity.Slot.REAL_WORLD: 5,
                ModuleAfterburnerActivity.Slot.GRAMMAR: 7,
            }

            meeting_signup = (
                ModuleLiveMeetingSignup.objects.filter(profile=profile, module=module)
                .select_related("meeting")
                .first()
            )
            meeting = meeting_signup.meeting if meeting_signup else None
            meeting_end = None
            meeting_unlock_date = None
            meeting_tz = timezone.get_current_timezone()
            if meeting:
                meeting_end = meeting.scheduled_for + timedelta(
                    minutes=meeting.duration_minutes or 60
                )
                if timezone.is_naive(meeting_end):
                    meeting_end = timezone.make_aware(
                        meeting_end, timezone.get_current_timezone()
                    )
                meeting_end_local = timezone.localtime(meeting_end)
                meeting_unlock_date = meeting_end_local.date()
                meeting_tz = meeting_end_local.tzinfo or timezone.get_current_timezone()

            card_locked = False
            lock_message = ""

            if index <= len(non_game_configs):
                slot = non_game_configs[index - 1]["slot"]
                if meeting_unlock_date is None:
                    card_locked = not user_is_admin
                    if not user_is_admin:
                        lock_message = "Schedule your live mission to unlock this mission."
                else:
                    unlock_date = meeting_unlock_date + timedelta(
                        days=slot_unlock_offsets.get(slot, 0)
                    )
                    unlock_naive = datetime.combine(unlock_date, time.min)
                    unlock_at = timezone.make_aware(unlock_naive, meeting_tz)
                    if not user_is_admin and now < unlock_at:
                        card_locked = True
                        unlock_local = timezone.localtime(unlock_at)
                        lock_message = f"This mission unlocks on {formats.date_format(unlock_local, 'M j, g:i a')}"
            else:
                card_locked = False
                lock_message = ""

            if card_locked:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"error": "locked", "message": lock_message}, status=403)
                messages.info(request, lock_message or "This mission is not available yet.")
                return redirect("course_module_stage", slug=slug, order=order, stage=stage_key)

        task_idx = index - 1
        tasks_state[task_idx] = not bool(tasks_state[task_idx])
        progress.completed_tasks = tasks_state
        progress.save(update_fields=["completed_tasks", "updated_at"])

        stage_unlocks = AccessService.get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if user_is_admin:
            stage_unlocks = {stage["key"]: True for stage in MODULE_STAGE_SEQUENCE}

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "completed": bool(tasks_state[task_idx]),
                    "completed_count": sum(1 for flag in tasks_state if flag),
                    "required": required,
                    "stage_unlocks": stage_unlocks,
                }
            )

        return redirect("course_module_stage", slug=slug, order=order, stage=stage_key)

class CourseEnrollView(PlacementRequiredMixin, View):
    login_url = "login"

    def post(self, request, slug: str):
        profile = getattr(request.user, "profile", None)
        if profile is None:
            messages.error(request, "Complete your profile before enrolling in a course.")
            return redirect("dashboard")

        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=CourseModule.objects.prefetch_related("sessions").order_by("order"),
                )
            ),
            slug=slug,
            is_published=True,
        )
        form = CourseEnrollmentForm(request.POST)

        if not form.is_valid():
            enrollment = CourseEnrollment.objects.filter(profile=profile, course=course).first()
            modules_qs = (
                CourseModule.objects.filter(course=course)
                .prefetch_related("sessions")
                .order_by("order")
            )
            total_modules = modules_qs.count()
            user = request.user
            can_view_course = bool(
                enrollment and enrollment.status in ALLOWED_ENROLLMENT_STATUSES
            ) or user.is_staff or user.is_superuser

            max_unlocked_order = 0
            if can_view_course and total_modules:
                completion_rate = float(getattr(enrollment, "completion_rate", 0) or 0)
                estimated_completed = int(
                    max(0, min(total_modules, round((completion_rate / 100) * total_modules)))
                )
                max_unlocked_order = min(total_modules, max(1, estimated_completed + 1))

            modules_payload = [
                {
                    "module": module,
                    "sessions": module.sessions.all(),
                    "is_unlocked": module.order <= max_unlocked_order,
                }
                for module in modules_qs
            ]

            context = {
                "course": course,
                "modules": modules_payload,
                "enrollment": enrollment,
                "form": form,
                "max_unlocked_order": max_unlocked_order,
                "can_view_course": can_view_course,
            }
            return render(request, "core/courses/detail.html", context, status=400)

        enrollment, created = CourseEnrollment.objects.get_or_create(
            profile=profile,
            course=course,
            defaults={
                "motivation": form.cleaned_data.get("motivation", ""),
                "status": CourseEnrollment.EnrollmentStatus.APPLIED,
            },
        )

        if not created:
            enrollment.motivation = form.cleaned_data.get("motivation", enrollment.motivation)
            if enrollment.status == CourseEnrollment.EnrollmentStatus.WITHDRAWN:
                enrollment.status = CourseEnrollment.EnrollmentStatus.APPLIED
            enrollment.save(update_fields=["motivation", "status"])
            messages.success(request, "Enrollment preferences updated. We'll be in touch soon.")
        else:
            messages.success(request, "You're on the path. Our team will confirm your seat shortly.")

        return redirect("course_detail", slug=slug)

class AccountView(LoginRequiredMixin, View):
    template_name = "core/account.html"
    login_url = "login"

    def get(self, request):
        form = AccountForm(request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = AccountForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated. Your next missions will reflect these changes.")
            return redirect("account")
        messages.error(request, "Please review the highlighted fields and try again.")
        return render(request, self.template_name, {"form": form})




class PlacementExamView(LoginRequiredMixin, View):
    template_name = "core/placement_exam.html"
    login_url = "login"

    def get(self, request):
        profile = getattr(request.user, "profile", None)
        if profile and profile.placement_completed:
            return redirect("dashboard")
        initial = {}
        if profile:
            initial = {
                "level": profile.desired_fluency_level,
                "focus": profile.target_focus,
            }
        form = PlacementExamForm(initial=initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = PlacementExamForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        profile = getattr(request.user, "profile", None)
        if profile is None:
            profile = Profile.objects.create(user=request.user, display_name=request.user.get_username())

        level = form.cleaned_data["level"]
        focus = form.cleaned_data["focus"]
        profile.desired_fluency_level = level
        profile.target_focus = focus
        profile.placement_completed = True
        profile.placement_completed_at = timezone.now()
        profile.save(update_fields=[
            "desired_fluency_level",
            "target_focus",
            "placement_completed",
            "placement_completed_at",
        ])

        SkillAssessment.objects.create(
            profile=profile,
            assessment_type=SkillAssessment.AssessmentType.PLACEMENT,
            fluency_level=level,
            notes=form.cleaned_data.get("intent", ""),
            assessed_by=request.user.get_full_name() or request.user.get_username(),
            assessed_at=timezone.now(),
        )

        messages.success(request, "Placement complete. Your experiences are unlocked.")
        return redirect("dashboard")


class GoalManageView(PlacementRequiredMixin, View):
    template_name = "core/forms/form_panel.html"
    login_url = "login"

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )
        existing = profile.goals.filter(is_primary=True).first()
        if existing:
            form = LearningGoalForm(instance=existing)
        else:
            form = LearningGoalForm(initial={"is_primary": True})
        return render(request, self.template_name, {
            "form": form,
            "form_title": "Update your mission goal",
            "form_message": "Set or refine the outcome guiding your current FOREIGN loop.",
            "submit_label": "Save goal",
        })

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )
        existing = profile.goals.filter(is_primary=True).first()
        form = LearningGoalForm(request.POST, instance=existing)
        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "form_title": "Update your mission goal",
                "form_message": "Set or refine the outcome guiding your current FOREIGN loop.",
                "submit_label": "Save goal",
            }, status=400)

        goal = form.save(commit=False)
        goal.profile = profile
        goal.save()
        if goal.is_primary:
            profile.goals.exclude(pk=goal.pk).update(is_primary=False)
        messages.success(request, "Goal updated.")
        return redirect("dashboard")


class ProgressCreateView(PlacementRequiredMixin, View):
    template_name = "core/forms/form_panel.html"
    login_url = "login"

    def get(self, request):
        Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )
        form = ProgressLogForm()
        return render(request, self.template_name, {
            "form": form,
            "form_title": "Log a breakthrough",
            "form_message": "Capture what shifted so coaches can steer the next sprint.",
            "submit_label": "Add progress",
        })

    def post(self, request):
        form = ProgressLogForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "form_title": "Log a breakthrough",
                "form_message": "Capture what shifted so coaches can steer the next sprint.",
                "submit_label": "Add progress",
            }, status=400)

        entry = form.save(commit=False)
        entry.profile = Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )[0]
        entry.logged_by = request.user.get_full_name() or request.user.get_username()
        entry.logged_at = timezone.now()
        entry.tags = form.cleaned_data.get("tags", [])
        entry.save()
        messages.success(request, "Progress captured.")
        return redirect("dashboard")


class AvailabilityManageView(PlacementRequiredMixin, View):
    template_name = "core/forms/form_panel.html"
    login_url = "login"

    def get(self, request):
        Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )
        form = AvailabilityWindowForm()
        return render(request, self.template_name, {
            "form": form,
            "form_title": "Add availability",
            "form_message": "Share when you are free so we can align live missions.",
            "submit_label": "Save window",
        })

    def post(self, request):
        form = AvailabilityWindowForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "form_title": "Add availability",
                "form_message": "Share when you are free so we can align live missions.",
                "submit_label": "Save window",
            }, status=400)

        window = form.save(commit=False)
        window.profile = Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )[0]
        window.save()
        messages.success(request, "Availability saved.")
        return redirect("dashboard")


class AssessmentUploadView(PlacementRequiredMixin, View):
    template_name = "core/forms/form_panel.html"
    login_url = "login"

    def get(self, request):
        Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )
        form = SkillAssessmentForm()
        return render(request, self.template_name, {
            "form": form,
            "form_title": "Upload assessment evidence",
            "form_message": "Drop in recent reviews so coaches can calibrate your path.",
            "submit_label": "Save assessment",
        })

    def post(self, request):
        form = SkillAssessmentForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "form_title": "Upload assessment evidence",
                "form_message": "Drop in recent reviews so coaches can calibrate your path.",
                "submit_label": "Save assessment",
            }, status=400)

        assessment = form.save(commit=False)
        assessment.profile = Profile.objects.get_or_create(
            user=request.user,
            defaults={"display_name": request.user.get_username()},
        )[0]
        assessment.assessed_at = timezone.now()
        assessment.save()
        messages.success(request, "Assessment stored.")
        return redirect("dashboard")
class PromiseView(TemplateView):
    template_name = "core/promise.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "stage_details": PROGRAM_STAGE_DETAILS,
                "pillars": [
                    {
                        "title": "Warm circles",
                        "description": "We learn in circles that feel like family—food on the table, names remembered, wins applauded.",
                        "details": [
                            "Hosts trained to make every newcomer feel at home",
                            "Stories and check-ins before any grammar or drills",
                            "Shared rituals that build trust and courage to speak",
                        ],
                    },
                    {
                        "title": "Simple structure",
                        "description": "Every session follows the same rhythm so you can relax and focus on speaking, not guessing what’s next.",
                        "details": [
                            "One phrase, one gesture, one goal per lesson",
                            "Listen · try · use framework that keeps English digestible",
                            "Printable and digital cards so notes stay light",
                        ],
                    },
                    {
                        "title": "Shared progress",
                        "description": "We measure growth through community wins—recordings, voice notes, and celebrations logged together.",
                        "details": [
                            "Weekly highlight threads celebrating real-life conversations",
                            "Audio clips stored in personal and community journals",
                            "Mentor feedback that sounds human, not academic",
                        ],
                    },
                ],
                "modalities": [
                    {
                        "name": "Neighborhood Circles",
                        "mode": "In-person",
                        "description": "Weekly gatherings hosted in community spaces. Expect shared meals, storytelling, and practical English.",
                        "touchpoints": "Warm-up circle · paired practice · community reflection",
                    },
                    {
                        "name": "Home Streams",
                        "mode": "Online",
                        "description": "Live video sessions designed for small screens and busy homes. Bring your family, unmute when you’re ready.",
                        "touchpoints": "Live mission · instant recap · same-day action prompt",
                    },
                    {
                        "name": "Bridge Mode",
                        "mode": "Hybrid",
                        "description": "Mix in-person circles with online sessions so learning follows you—perfect for families and teams.",
                        "touchpoints": "Monthly meet-up · weekly online mission · shared progress board",
                    },
                ],
                "commitments": [
                    {
                        "label": "Curation",
                        "body": "We group learners by goals, schedules, and location so every conversation feels relevant and supportive.",
                    },
                    {
                        "label": "Evidence",
                        "body": "Voice clips, reflections, and cheer threads show progress without exam pressure.",
                    },
                    {
                        "label": "Momentum",
                        "body": "Daily nudges, light challenges, and circle shout-outs keep English alive between sessions.",
                    },
                ],
                "outcomes": [
                    {
                        "metric": "87%",
                        "caption": "of members speak English with their community at least twice a week",
                    },
                    {
                        "metric": "4.8/5",
                        "caption": "average rating for the ease and clarity of each session",
                    },
                    {
                        "metric": "3.2x",
                        "caption": "increase in self-recorded conversations within the first 30 days",
                    },
                ],
            }
        )
        return context


class MethodView(TemplateView):
    template_name = "core/method.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "stage_details": PROGRAM_STAGE_DETAILS,
                "rituals": [
                    {
                        "title": "Sunday Circle Prep",
                        "details": "Share a quick win, pick the week’s focus, and download simple phrase cards before we meet.",
                    },
                    {
                        "title": "Mid-week Practice Room",
                        "details": "Rotate through guided mini-conversations with peers while mentors keep the energy high.",
                    },
                    {
                        "title": "Friday Playback",
                        "details": "Listen back to your clips, share reflections, and choose one real-life action for the weekend.",
                    },
                ],
                "toolkit": [
                    "FOREIGN app with lesson cards, voice recorder, and celebration threads",
                    "On-demand mentors for voice notes when you need a boost",
                    "Community feed with prompts, resources, and shared wins",
                ],
                "modalities": [
                    {
                        "name": "Neighbourhood Circles",
                        "mode": "In-person",
                        "description": "Anchor weeks where squads meet locally for high-touch practice, shared snacks, and real conversation.",
                        "touchpoints": "Welcome circle · guided practice · shared reflection",
                    },
                    {
                        "name": "Home Streams",
                        "mode": "Online",
                        "description": "Adaptive live missions you can join from your sofa with instant transcripts and recap cards.",
                        "touchpoints": "Live mission · recap · community action point",
                    },
                    {
                        "name": "Bridge Mode",
                        "mode": "Hybrid",
                        "description": "Hybrid flow blending neighbourhood circles with online streams—ideal for busy families or teams.",
                        "touchpoints": "Monthly community day · flexible online sessions · shared progress board",
                    },
                ],
            }
        )
        return context



class PricingView(TemplateView):
    template_name = "core/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "tiers": [
                    {
                        "name": "Circle Pass",
                        "label": "Starter · Home Streams",
                        "price": "$149/mo",
                        "description": "Join live streams from home, meet friendly partners, and follow one simple lesson card each week.",
                        "features": [
                            "3 live Home Stream missions every week",
                            "Monthly community calibration with a coach",
                            "FOREIGN app with lesson cards & voice journal",
                            "Accountability pods that celebrate every clip",
                            "Weekly feedback notes you can read in minutes",
                        ],
                        "animations": {
                            "badge": "fade-up",
                            "card": "fade-scale",
                        },
                    },
                    {
                        "name": "Gather & Grow",
                        "label": "Flagship · Circles + Streams",
                        "price": "$329/mo",
                        "description": "Blend in-person circles with online streams for the full community experience—perfect for families and teams.",
                        "features": [
                            "Bi-weekly neighbourhood circle hosted near you",
                            "Weekly Home Stream sessions with your facilitator",
                            "Dedicated community coach for nudges and support",
                            "Quarterly showcase night with shared highlights",
                            "Priority access to partner-led community events",
                        ],
                        "highlight": True,
                        "animations": {
                            "badge": "fade-scale",
                            "card": "fade-up",
                        },
                    },
                    {
                        "name": "Community Studio",
                        "label": "Hybrid · Custom Partner Plan",
                        "price": "Custom",
                        "description": "Design a bespoke plan for workplaces, schools, or housing communities. We provide hosts, lesson cards, and ongoing coaching.",
                        "features": [
                            "On-site facilitator training & launch workshop",
                            "Weekly hybrid sessions with shared progress board",
                            "Tailored lesson decks for your group’s goals",
                            "Community success reporting every quarter",
                            "Dedicated strategist for scheduling & support",
                        ],
                        "animations": {
                            "badge": "fade-up",
                            "card": "fade-scale",
                        },
                    },
                ],
                "extras": [
                    {
                        "title": "Family Starter Kit",
                        "summary": "Story games, school scripts, and weekend challenges designed for parents and kids learning together.",
                    },
                    {
                        "title": "Workplace Circle",
                        "summary": "Custom session plan for teams who want to practise English together over lunch or stand-ups.",
                    },
                    {
                        "title": "Community Host Residency",
                        "summary": "Bring a FOREIGN facilitator to your organisation to train volunteers and launch new circles.",
                    },
                ],
            }
        )
        return context

class ExperiencesView(PlacementRequiredMixin, TemplateView):
    template_name = "core/experiences.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = Course.objects.filter(is_published=True).order_by("title")
        courses = list(queryset)
        course_groups = {
            "Foundation": [course for course in courses if course.difficulty == Course.Difficulty.FOUNDATION],
            "Intensive": [course for course in courses if course.difficulty == Course.Difficulty.INTENSIVE],
            "Mastery": [course for course in courses if course.difficulty == Course.Difficulty.MASTER],
        }
        course_groups_display: dict[str, list[dict[str, object]]] = {}
        for label, group in course_groups.items():
            cards: list[dict[str, object]] = []
            for course in group:
                cards.append(
                    {
                        "title": course.title,
                        "slug": course.slug,
                        "delivery_label": course.get_delivery_mode_display(),
                        "level_label": course.get_fluency_level_display(),
                        "subtitle": course.subtitle or course.summary or "",
                    }
                )
            course_groups_display[label] = cards

        levels = []
        for level in PROGRAM_LEVELS:
            enriched = level.copy()
            enriched['course_count'] = sum(1 for course in courses if course.fluency_level == level['code'])
            levels.append(enriched)

        context.update(
            {
                "program_levels": levels,
                "course_groups": course_groups,
                "course_groups_display": course_groups_display,
                "has_courses": bool(courses),
            }
        )
        return context


class ProgramListView(PlacementRequiredMixin, TemplateView):
    template_name = "core/programs/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published_courses = Course.objects.filter(is_published=True)
        course_counts = {code: 0 for code in PROGRAM_LOOKUP}
        for course in published_courses.values('fluency_level'):
            code = course['fluency_level']
            if code in course_counts:
                course_counts[code] += 1

        levels_with_counts = []
        for level in PROGRAM_LEVELS:
            enriched = level.copy()
            enriched['course_count'] = course_counts.get(level['code'], 0)
            levels_with_counts.append(enriched)

        context.update(
            {
                "program_levels": levels_with_counts,
            }
        )
        return context


class ProgramDetailView(PlacementRequiredMixin, TemplateView):
    template_name = "core/programs/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        code = (kwargs.get("code") or "").upper()
        program = PROGRAM_LOOKUP.get(code)
        if program is None:
            raise Http404

        courses = list(Course.objects.filter(is_published=True, fluency_level=code).order_by("title"))
        context.update(
            {
                "program": program,
                "courses": courses,
                "has_courses": bool(courses),
            }
        )
        return context
