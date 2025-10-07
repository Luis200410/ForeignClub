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
from django.db.models import Prefetch
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



PROGRAM_LEVELS = [
    {
        "code": Profile.FluencyLevel.BEGINNER,
        "title": "A1 · Awakening",
        "headline": "Build instincts for everyday survival conversations.",
        "tagline": "Intentional micro-missions to spark your English reflexes.",
    },
    {
        "code": Profile.FluencyLevel.ELEMENTARY,
        "title": "A2 · Momentum",
        "headline": "Navigate daily life with clarity and confidence.",
        "tagline": "Roleplay-powered labs designed to automate essential phrases.",
    },
    {
        "code": Profile.FluencyLevel.INTERMEDIATE,
        "title": "B1 · Expression",
        "headline": "Think in English during fast-paced conversations.",
        "tagline": "High-tempo exchanges and adaptive story games to unlock spontaneity.",
    },
    {
        "code": Profile.FluencyLevel.UPPER_INTERMEDIATE,
        "title": "B2 · Influence",
        "headline": "Lead conversations, presentations, and collaborations.",
        "tagline": "Strategic labs that sharpen persuasion and nuance.",
    },
    {
        "code": Profile.FluencyLevel.ADVANCED,
        "title": "C1 · Command",
        "headline": "Operate like a native in high-stakes environments.",
        "tagline": "Executive simulations, rapid feedback, and precision coaching.",
    },
    {
        "code": Profile.FluencyLevel.PROFICIENT,
        "title": "C2 · Legacy",
        "headline": "Shape culture, mentor others, and craft impact.",
        "tagline": "Mastery studios focused on performance, storytelling, and nuance.",
    },
]

PROGRAM_LOOKUP = {level["code"]: level for level in PROGRAM_LEVELS}


MODULE_STAGE_SEQUENCE = [
    {
        "key": "launch-pad",
        "label": "Launch Pad",
        "tagline": "NotebookLM Prep",
        "summary": "Prime your instincts with curated NotebookLM missions before we go live.",
    },
    {
        "key": "flight-deck",
        "label": "Flight Deck",
        "tagline": "Live Studio",
        "summary": "Choose the live labs you will join and lock your Friday agenda.",
    },
    {
        "key": "afterburner",
        "label": "Afterburner",
        "tagline": "Retention Lab",
        "summary": "Play, review, and loop spaced repetition to secure retention.",
    },
]

for idx, stage in enumerate(MODULE_STAGE_SEQUENCE, start=1):
    stage["order"] = idx

MODULE_STAGE_LOOKUP = {stage["key"]: stage for stage in MODULE_STAGE_SEQUENCE}

PRE_SESSION_TASKS = [task["title"] for task in DEFAULT_LAUNCH_PAD_TASKS]

POST_SESSION_TASKS = [
    "NotebookLM game mission",
    "Spaced repetition review (48h)",
    "Peer feedback exchange",
    "Mini challenge unlocked via app",
    "Signal reminder: next live cue",
    "Evidence upload checkpoint",
]

AFTERBURNER_CARD_LIBRARY = {
    Profile.FluencyLevel.BEGINNER: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Talk & Record Challenge",
            "description": "Press record. Say the model sentence slowly. Listen. Try again with clear sounds.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Read & Highlight",
            "description": "Read the short text out loud. Underline three new words and say them again.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Use today's phrase in real life. Ask a friend or mirror one easy question.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Snapshot",
            "description": "Watch the quick grammar clip. Write two present simple sentences about you.",
        },
    },
    Profile.FluencyLevel.ELEMENTARY: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Pronunciation Replay",
            "description": "Record yourself at natural speed. Compare stress with the sample and adjust endings.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Guided Reading Burst",
            "description": "Read the article aloud, pausing to note useful collocations and rhythm shifts.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Start a short chat using this week's pattern. Log one win in your NotebookLM notes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Booster",
            "description": "Review the focus tense and craft three personal example sentences with it.",
        },
    },
    Profile.FluencyLevel.INTERMEDIATE: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Voice Precision Lab",
            "description": "Record a 30-second response and analyze rhythm, intonation, and connected speech.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Insight Reading Loop",
            "description": "Annotate the text for tone shifts, then summarize the key evidence aloud.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Apply the scenario in a real or simulated conversation and capture feedback notes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Systems Review",
            "description": "Deconstruct the structure in context and rewrite complex sentences using it.",
        },
    },
    Profile.FluencyLevel.UPPER_INTERMEDIATE: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Delivery Masterclass",
            "description": "Capture a speaking sample focusing on stress, linking, and persuasive cadence.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Critical Reading Pulse",
            "description": "Dissect the article's argument, mark discourse markers, and brief it back.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Challenge",
            "description": "Lead a live interaction mirroring the week's case study and reflect on outcomes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Structure Upgrade",
            "description": "Integrate the grammar focus into original paragraphs, highlighting register shifts.",
        },
    },
    Profile.FluencyLevel.ADVANCED: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Narrative Delivery Studio",
            "description": "Record a concise story, refine nuance and pacing, and evaluate audience impact.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Analytical Reading Exchange",
            "description": "Interrogate author intent, map advanced lexis, and present a critical response.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Strategy Challenge",
            "description": "Execute a mission-critical conversation and capture insights for a cohort debrief.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Refinement Clinic",
            "description": "Stress-test complex syntax by reshaping examples into formal and informal versions.",
        },
    },
    Profile.FluencyLevel.PROFICIENT: {
        ModuleAfterburnerActivity.Slot.TALK_RECORD: {
            "title": "Executive Delivery Audit",
            "description": "Produce a high-stakes delivery sample, calibrating executive presence and flow.",
        },
        ModuleAfterburnerActivity.Slot.READING: {
            "title": "Scholarly Reading Sprint",
            "description": "Synthesize advanced texts, extract thesis frameworks, and articulate counterpoints.",
        },
        ModuleAfterburnerActivity.Slot.REAL_WORLD: {
            "title": "Real World Impact Challenge",
            "description": "Drive an authentic negotiation or leadership moment and document measured outcomes.",
        },
        ModuleAfterburnerActivity.Slot.GRAMMAR: {
            "title": "Grammar Edge Lab",
            "description": "Manipulate nuanced structures across registers, ensuring precision under pressure.",
        },
    },
}

AFTERBURNER_GAME = {
    "key": "mission-remix",
    "title": "Didactic Game · Mission Remix",
    "description": "A collaborative remix where squads reimagine the week’s mission with new stakes, vocabulary, and constraints.",
}

AFTERBURNER_SLOT_SEQUENCE = [
    ModuleAfterburnerActivity.Slot.TALK_RECORD,
    ModuleAfterburnerActivity.Slot.READING,
    ModuleAfterburnerActivity.Slot.REAL_WORLD,
    ModuleAfterburnerActivity.Slot.GRAMMAR,
    ModuleAfterburnerActivity.Slot.GAME,
]

FLIGHT_DECK_SLOT_SEQUENCE = [
    ModuleFlightDeckActivity.Slot.SCHEDULER,
    ModuleFlightDeckActivity.Slot.NOTEBOOK,
    ModuleFlightDeckActivity.Slot.RECORDER,
]

FLASHCARD_SRS_INTERVALS = [
    timedelta(minutes=1),
    timedelta(minutes=10),
    timedelta(hours=1),
    timedelta(hours=6),
    timedelta(days=1),
    timedelta(days=3),
    timedelta(days=7),
    timedelta(days=14),
]

ALLOWED_ENROLLMENT_STATUSES = {
    CourseEnrollment.EnrollmentStatus.ACTIVE,
    CourseEnrollment.EnrollmentStatus.COMPLETED,
}


def _get_afterburner_card_configs(
    course: Course | None,
    module: CourseModule | None = None,
) -> list[dict[str, str]]:
    """Return ordered Afterburner card configs, prioritising module customisations."""

    fallback_level_map = AFTERBURNER_CARD_LIBRARY.get(
        getattr(course, "fluency_level", Profile.FluencyLevel.INTERMEDIATE),
        AFTERBURNER_CARD_LIBRARY[Profile.FluencyLevel.INTERMEDIATE],
    )

    module_activities = {}
    if module is not None:
        module_activities = {
            activity.slot: activity
            for activity in module.afterburner_activities.filter(is_active=True)
        }

    configs: list[dict[str, str | object]] = []
    for slot in AFTERBURNER_SLOT_SEQUENCE:
        activity = module_activities.get(slot)
        fallback_card = fallback_level_map.get(slot, {})
        if slot == ModuleAfterburnerActivity.Slot.GAME:
            game_instance = getattr(activity, "game", None) or _resolve_adaptive_game(module)
            configs.append(
                {
                    "slot": slot,
                    "title": (activity.title if activity and activity.title else AFTERBURNER_GAME["title"]),
                    "description": (
                        activity.description
                        if activity and activity.description
                        else AFTERBURNER_GAME["description"]
                    ),
                    "activity": activity,
                    "game": game_instance,
                    "goal": getattr(activity, "goal", "") if activity else "",
                }
            )
            continue

        configs.append(
            {
                "slot": slot,
                "title": (
                    activity.title if activity and activity.title else fallback_card.get("title", "")
                ),
                "description": (
                    activity.description
                    if activity and activity.description
                    else fallback_card.get("description", "")
                ),
                "activity": activity,
                "goal": getattr(activity, "goal", "") if activity else "",
            }
        )

    return configs


def _resolve_adaptive_game(module: CourseModule | None) -> ModuleGame | None:
    if module is None:
        return None

    activity_game = (
        ModuleAfterburnerActivity.objects.filter(
            module=module,
            slot=ModuleAfterburnerActivity.Slot.GAME,
        )
        .select_related("game")
        .first()
    )
    if activity_game and activity_game.game:
        game = activity_game.game
        if game.is_active and game.game_type == ModuleGame.GameType.ADAPTIVE_FLASHCARDS:
            return game

    return (
        ModuleGame.objects.filter(
            module=module,
            game_type=ModuleGame.GameType.ADAPTIVE_FLASHCARDS,
            is_active=True,
        )
        .order_by("order", "id")
        .first()
    )


def _resolve_profile(
    user,
    *,
    allow_admin_create: bool = False,
):
    """Return the user's profile, auto-creating one for admins when needed."""

    profile = getattr(user, "profile", None)
    if profile is not None or not getattr(user, "is_authenticated", False):
        return profile

    if allow_admin_create and getattr(user, "is_superuser", False):
        display_name = (
            user.get_full_name()
            or user.get_username()
            or "Mission Control"
        )
        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={
                "display_name": display_name,
                "timezone": timezone.get_current_timezone_name(),
            },
        )
        return profile

    return profile


def _pair_key(primary_id: int, partner_id: int | None) -> tuple[int, int] | None:
    if primary_id is None or partner_id is None:
        return None
    return (primary_id, partner_id) if primary_id <= partner_id else (partner_id, primary_id)


def _assign_meeting_pairs(
    participant_ids: list[int],
    avoided_pairs: set[tuple[int, int]],
) -> tuple[list[tuple[int, int | None]], set[tuple[int, int]]]:
    remaining = list(sorted(participant_ids))
    assignments: list[tuple[int, int | None]] = []
    used_this_round: set[tuple[int, int]] = set()

    while len(remaining) > 1:
        primary_id = remaining.pop(0)
        candidate_index = None
        for idx, candidate in enumerate(remaining):
            key = _pair_key(primary_id, candidate)
            if key and key not in avoided_pairs and key not in used_this_round:
                candidate_index = idx
                break

        if candidate_index is None:
            assignments.append((primary_id, None))
            continue

        partner_id = remaining.pop(candidate_index)
        normalized = _pair_key(primary_id, partner_id)
        if normalized:
            used_this_round.add(normalized)
            assignments.append(normalized)
        else:
            assignments.append((primary_id, partner_id))

    if remaining:
        assignments.append((remaining.pop(), None))

    return assignments, used_this_round


def _build_pair_map(
    meeting: ModuleLiveMeeting,
) -> dict[int, dict[int, ModuleMeetingPairing]]:
    lookup: dict[int, dict[int, ModuleMeetingPairing]] = defaultdict(dict)
    pairings = (
        ModuleMeetingPairing.objects.filter(meeting=meeting)
        .select_related("activity", "profile_primary", "profile_partner")
        .all()
    )
    for pairing in pairings:
        lookup[pairing.activity_id][pairing.profile_primary_id] = pairing
        if pairing.profile_partner_id:
            lookup[pairing.activity_id][pairing.profile_partner_id] = pairing
    return lookup


def _ensure_meeting_pairings(
    module: CourseModule,
    meeting: ModuleLiveMeeting,
) -> dict[int, dict[int, ModuleMeetingPairing]]:
    participants = list(
        ModuleLiveMeetingSignup.objects.filter(meeting=meeting)
        .select_related("profile")
        .order_by("profile__display_name")
    )
    if not participants:
        ModuleMeetingPairing.objects.filter(meeting=meeting).delete()
        return {}

    participant_ids = [signup.profile_id for signup in participants if signup.profile_id]
    if not participant_ids:
        return {}

    historical_pairs = {
        key
        for key in (
            _pair_key(primary_id, partner_id)
            for primary_id, partner_id in ModuleMeetingPairing.objects.filter(module=module)
            .exclude(meeting=meeting)
            .values_list("profile_primary_id", "profile_partner_id")
        )
        if key
    }

    ModuleMeetingPairing.objects.filter(meeting=meeting).delete()

    activities = list(module.meeting_activities.filter(is_active=True).order_by("order"))
    if not activities:
        return {}

    avoided_pairs = set(historical_pairs)
    pairings_to_create: list[ModuleMeetingPairing] = []

    for activity in activities:
        assignments, used_this_round = _assign_meeting_pairs(participant_ids, avoided_pairs)
        for primary_id, partner_id in assignments:
            if partner_id is None:
                pairings_to_create.append(
                    ModuleMeetingPairing(
                        module=module,
                        meeting=meeting,
                        activity=activity,
                        profile_primary_id=primary_id,
                        paired_with_assistant=True,
                    )
                )
                continue

            ordered_pair = _pair_key(primary_id, partner_id)
            if ordered_pair is None:
                continue
            avoided_pairs.add(ordered_pair)
            pairings_to_create.append(
                ModuleMeetingPairing(
                    module=module,
                    meeting=meeting,
                    activity=activity,
                    profile_primary_id=ordered_pair[0],
                    profile_partner_id=ordered_pair[1],
                    paired_with_assistant=False,
                )
            )

        avoided_pairs.update(used_this_round)

    if pairings_to_create:
        ModuleMeetingPairing.objects.bulk_create(pairings_to_create)

    return _build_pair_map(meeting)


def _get_launch_pad_task_configs(course: Course | None, module: CourseModule | None) -> list[dict[str, str]]:
    """Return launch pad task configurations with module overrides."""

    module_tasks = []
    if module is not None:
        activity = getattr(module, "launchpad_activity", None)
        if activity:
            module_tasks = list(
                activity.tasks.filter(is_active=True).order_by("order", "id")
            )
        else:
            module_tasks = list(
                ModuleLaunchPadTask.objects.filter(module=module, is_active=True).order_by("order", "id")
            )

    if module_tasks:
        return [
            {
                "title": task.title,
                "description": task.description,
                "link_label": task.link_label or "Open NotebookLM",
                "link_url": task.link_url,
            }
            for task in module_tasks
        ]

    return [task.copy() for task in LAUNCH_PAD_DEFAULT_TASKS]


def _get_flight_deck_activity_configs(module: CourseModule | None) -> list[dict[str, str]]:
    """Return ordered Flight Deck activity configs with module overrides."""

    defaults = {task["slot"]: {**task} for task in FLIGHT_DECK_TASKS}
    if module is None:
        return [defaults[slot] for slot in FLIGHT_DECK_SLOT_SEQUENCE]

    module_activities = {
        activity.slot: activity
        for activity in module.flightdeck_activities.filter(is_active=True)
    }

    configs: list[dict[str, str]] = []
    for slot in FLIGHT_DECK_SLOT_SEQUENCE:
        base_config = defaults.get(slot, {"slot": slot})
        activity = module_activities.get(slot)
        config = {**base_config}
        if activity:
            if activity.title:
                config["title"] = activity.title
            if activity.subtitle:
                config["subtitle"] = activity.subtitle
            if activity.description:
                config["description"] = activity.description
            if activity.link_label:
                config["link_label"] = activity.link_label
            if activity.link_url:
                config["url"] = activity.link_url
        configs.append(config)

    return configs


def _ensure_flashcard_progress_map(
    profile: Profile,
    game: ModuleGame,
) -> dict[int, ModuleGameFlashcardProgress]:
    """Ensure progress rows exist for each active flashcard and return a map."""

    now = timezone.now()
    flashcards = list(game.flashcards.filter(is_active=True).order_by("order", "id"))
    if not flashcards:
        return {}

    existing = (
        ModuleGameFlashcardProgress.objects.select_related("flashcard")
        .filter(profile=profile, flashcard__in=flashcards)
        .all()
    )
    progress_map = {progress.flashcard_id: progress for progress in existing}

    to_create: list[ModuleGameFlashcardProgress] = []
    for card in flashcards:
        if card.id not in progress_map:
            to_create.append(
                ModuleGameFlashcardProgress(
                    profile=profile,
                    flashcard=card,
                    next_review_at=now,
                )
            )

    if to_create:
        ModuleGameFlashcardProgress.objects.bulk_create(to_create)
        existing = (
            ModuleGameFlashcardProgress.objects.select_related("flashcard")
            .filter(profile=profile, flashcard__in=flashcards)
            .all()
        )
        progress_map = {progress.flashcard_id: progress for progress in existing}

    return progress_map


def _flashcard_interval_for_index(index: int) -> timedelta:
    if index < 0:
        index = 0
    if not FLASHCARD_SRS_INTERVALS:
        return timedelta(minutes=5)
    if index >= len(FLASHCARD_SRS_INTERVALS):
        index = len(FLASHCARD_SRS_INTERVALS) - 1
    return FLASHCARD_SRS_INTERVALS[index]

STAGE_EXTENSION_MAP = {
    "launch-pad": {
        "description": "Launch Pad lays the groundwork. Learners align goals, unlock NotebookLM mission packs, and rehearse core patterns before stepping into the live arena.",
        "highlights": [
            "Calibration interview + mission blueprint",
            "NotebookLM mission decks & pronunciation drills",
            "AI warmups that surface vocabulary and rhythm gaps",
        ],
        "promise": "We prime every learner with personalized mission data so the live arena never feels like guesswork.",
    },
    "flight-deck": {
        "description": "Flight Deck is the weekly live studio. Squads choose their labs, mentors orchestrate cinematic missions, and momentum compounds in real time.",
        "highlights": [
            "Curated live labs with ambitious peers",
            "Mentor-led playbooks that adapt mid-session",
            "Adaptive AI rehearsal woven between live exchanges",
        ],
        "promise": "Every lab feels like stepping into the scenario you actually need—because it is designed around your targets.",
    },
    "afterburner": {
        "description": "Afterburner locks in the gains. Game missions, spaced repetition, and evidence reviews encode new instincts and set up the next launch.",
        "highlights": [
            "Arcade-style retention missions",
            "Spaced repetition loops across the week",
            "Coach retros and evidence reels to measure the jump",
        ],
        "promise": "We close every loop with proof—so confidence stays high and every next mission feels inevitable.",
    },
}

LAUNCH_PAD_DEFAULT_TASKS = deepcopy(DEFAULT_LAUNCH_PAD_TASKS)

MEETING_ASSISTANT_URL = getattr(
    settings,
    "MEETING_ASSISTANT_URL",
    "mailto:missioncontrol@foreign.club?subject=Live%20mission%20assist",
)

FLIGHT_DECK_TASKS = [
    {
        "slot": ModuleFlightDeckActivity.Slot.SCHEDULER,
        "title": "Schedule your live mission",
        "subtitle": "Lock your Friday studio slot directly from this page.",
    },
    {
        "slot": ModuleFlightDeckActivity.Slot.NOTEBOOK,
        "title": "Prep your NotebookLM workspace",
        "subtitle": "Spin up a fresh set of notes for this week's mission. Capture vocabulary, new expressions, and personal takeaways inside NotebookLM so you can revisit them later.",
        "url": NOTEBOOK_LM_APP_URL,
        "link_label": "NotebookLM Notes",
    },
    {
        "slot": ModuleFlightDeckActivity.Slot.RECORDER,
        "title": "Get your recorder ready",
        "subtitle": "Capture your live mission for reflection and evidence uploads",
    },
]

PROGRAM_STAGE_DETAILS = [
    {
        **stage,
        **STAGE_EXTENSION_MAP.get(stage["key"], {}),
    }
    for stage in MODULE_STAGE_SEQUENCE
]


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
                {"value": "12 weeks", "label": "To rewire instinct with our weekly loop"},
                {"value": "3 stages", "label": "Launch Pad · Flight Deck · Afterburner"},
                {"value": "90%", "label": "Members reporting faster live reactions"},
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


def _get_enrollment_and_access(user, course):
    profile = getattr(user, "profile", None)
    enrollment = None
    if profile:
        enrollment = CourseEnrollment.objects.filter(profile=profile, course=course).first()
    can_view = bool(
        enrollment and enrollment.status in ALLOWED_ENROLLMENT_STATUSES
    ) or user.is_staff or user.is_superuser
    return enrollment, can_view


def _get_stage_unlocks(user, course, module, enrollment=None, can_view_course=False):
    unlocks = {stage["key"]: False for stage in MODULE_STAGE_SEQUENCE}
    unlocks["launch-pad"] = can_view_course
    if not unlocks["launch-pad"]:
        return unlocks

    profile = getattr(user, "profile", None)
    if profile is None:
        return unlocks

    launch_configs = _get_launch_pad_task_configs(course, module)

    try:
        progress = ModuleStageProgress.objects.get(
            profile=profile,
            module=module,
            stage_key=ModuleStageProgress.StageKey.LAUNCH_PAD,
        )
        tasks = list(progress.completed_tasks or [])
    except ModuleStageProgress.DoesNotExist:
        tasks = []

    required = len(launch_configs)
    if len(tasks) < required:
        tasks.extend([False] * (required - len(tasks)))
    elif len(tasks) > required:
        tasks = tasks[:required]

    stage_one_complete = required > 0 and all(bool(flag) for flag in tasks[:required])
    unlocks["flight-deck"] = stage_one_complete

    flight_tasks_required = _get_stage_required_tasks(
        ModuleStageProgress.StageKey.FLIGHT_DECK, module
    )
    if flight_tasks_required:
        flight_progress = None
        try:
            flight_progress = ModuleStageProgress.objects.get(
                profile=profile,
                module=module,
                stage_key=ModuleStageProgress.StageKey.FLIGHT_DECK,
            )
            flight_tasks = list(flight_progress.completed_tasks or [])
        except ModuleStageProgress.DoesNotExist:
            flight_tasks = []

        if len(flight_tasks) < flight_tasks_required:
            flight_tasks.extend([False] * (flight_tasks_required - len(flight_tasks)))
        elif len(flight_tasks) > flight_tasks_required:
            flight_tasks = flight_tasks[:flight_tasks_required]

        meetings_exist = ModuleLiveMeetingSignup.objects.filter(
            profile=profile,
            module=module,
        ).exists()

        if meetings_exist:
            if not flight_tasks:
                flight_tasks = [False] * flight_tasks_required
            if not flight_tasks[0]:
                flight_tasks[0] = True
                if flight_progress is None:
                    flight_progress = ModuleStageProgress.objects.create(
                        profile=profile,
                        module=module,
                        stage_key=ModuleStageProgress.StageKey.FLIGHT_DECK,
                        completed_tasks=flight_tasks,
                    )
                else:
                    flight_progress.completed_tasks = flight_tasks
                    flight_progress.save(update_fields=["completed_tasks", "updated_at"])

        elif flight_tasks and flight_tasks[0]:
            flight_tasks[0] = False
            if flight_progress is not None:
                flight_progress.completed_tasks = flight_tasks
                flight_progress.save(update_fields=["completed_tasks", "updated_at"])

        flight_stage_complete = all(bool(flag) for flag in flight_tasks[:flight_tasks_required])
    else:
        flight_stage_complete = False

    unlocks["afterburner"] = flight_stage_complete
    return unlocks


def _is_module_unlocked(user, course, module, enrollment=None, can_view_course=False):
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True

    if module.order <= 1:
        return True

    previous_order = module.order - 1
    previous_module = None

    if hasattr(course, "modules"):
        for candidate in course.modules.all():
            if candidate.order == previous_order:
                previous_module = candidate
                break

    if previous_module is None:
        previous_module = (
            CourseModule.objects.filter(course=course, order=previous_order).first()
        )

    if previous_module is None:
        return True

    previous_unlocks = _get_stage_unlocks(
        user,
        course,
        previous_module,
        enrollment=enrollment,
        can_view_course=can_view_course,
    )
    return bool(previous_unlocks.get("flight-deck", False))


def _get_stage_required_tasks(stage_key: str, module: CourseModule) -> int:
    if stage_key == ModuleStageProgress.StageKey.LAUNCH_PAD:
        return len(_get_launch_pad_task_configs(getattr(module, "course", None), module))
    if stage_key == ModuleStageProgress.StageKey.FLIGHT_DECK:
        return len(_get_flight_deck_activity_configs(module))
    if stage_key == ModuleStageProgress.StageKey.AFTERBURNER:
        return len(_get_afterburner_card_configs(getattr(module, "course", None), module))
    return 0


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
        enrollment, can_view_course = _get_enrollment_and_access(self.request.user, course)

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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)

        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        if not user_is_admin and not _is_module_unlocked(
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

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)
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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        if not user_is_admin and not _is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            previous_week = max(1, module.order - 1)
            messages.warning(
                self.request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)
        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)
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

        profile = _resolve_profile(user, allow_admin_create=user_is_admin)
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

        launch_configs = _get_launch_pad_task_configs(course, module)
        launch_tasks = [
            {
                "index": idx,
                "title": config.get("title", ""),
                "description": config.get("description", ""),
                "link_label": config.get("link_label", "Open NotebookLM"),
                "link_url": config.get("link_url") or NOTEBOOK_LM_APP_URL,
                "completed": False,
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
        afterburner_configs = _get_afterburner_card_configs(course, module)
        afterburner_cards: list[dict[str, object]] = []
        game_config: dict[str, object] | None = None
        for config in afterburner_configs:
            if config["slot"] == ModuleAfterburnerActivity.Slot.GAME:
                game_config = config
                continue
            afterburner_cards.append(
                {
                    "index": len(afterburner_cards) + 1,
                    "title": config["title"],
                    "description": config["description"],
                    "completed": False,
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
                selected_game = game_config.get("game") or _resolve_adaptive_game(module)

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
                pairings_map = _ensure_meeting_pairings(module, selected_meeting)
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
                flight_configs = _get_flight_deck_activity_configs(module)
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
                required = _get_stage_required_tasks(ModuleStageProgress.StageKey.AFTERBURNER, module)
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

    def get_context_data(self, **kwargs):
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
        user = self.request.user
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not _is_module_unlocked(user, course, module, enrollment, can_view_course):
            previous_week = max(1, module.order - 1)
            messages.warning(
                self.request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)
        if not stage_unlocks.get(ModuleStageProgress.StageKey.AFTERBURNER, False):
            messages.warning(self.request, "Unlock Afterburner to view this dashboard.")
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
        return context


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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not _is_module_unlocked(user, course, module, enrollment, can_view_course):
            previous_week = max(1, module.order - 1)
            messages.warning(
                request,
                f"Complete Week {previous_week} Launch Pad missions to unlock Week {module.order}.",
            )
            return redirect("course_module", slug=slug, order=previous_week)

        profile = _resolve_profile(user, allow_admin_create=user_is_admin)
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
        required = _get_stage_required_tasks(ModuleStageProgress.StageKey.FLIGHT_DECK, module)
        if len(tasks_state) < required:
            tasks_state.extend([False] * (required - len(tasks_state)))
        tasks_state[0] = True
        progress.completed_tasks = tasks_state[:required]
        progress.save(update_fields=["completed_tasks", "updated_at"])

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)

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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        if not _is_module_unlocked(user, course, module, enrollment, can_view_course):
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
        required = _get_stage_required_tasks(ModuleStageProgress.StageKey.FLIGHT_DECK, module)
        if len(tasks_state) < required:
            tasks_state.extend([False] * (required - len(tasks_state)))
        tasks_state[0] = False
        progress.completed_tasks = tasks_state[:required]
        progress.save(update_fields=["completed_tasks", "updated_at"])

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)

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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
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

        if not user.is_superuser and not _is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            return JsonResponse({"error": "module_locked"}, status=403)

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)
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
            module_game = _resolve_adaptive_game(module)
        if not module_game:
            return JsonResponse({"cards": [], "meta": {"total_due": 0}}, status=200)

        profile = _resolve_profile(user, allow_admin_create=True)
        if profile is None:
            return JsonResponse({"error": "profile_missing"}, status=403)

        progress_map = _ensure_flashcard_progress_map(profile, module_game)
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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
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

        if not user.is_superuser and not _is_module_unlocked(
            user, course, module, enrollment, can_view_course
        ):
            return JsonResponse({"error": "module_locked"}, status=403)

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)
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
            module_game = _resolve_adaptive_game(module)
        if not module_game:
            return JsonResponse({"error": "game_unavailable"}, status=400)

        profile = _resolve_profile(user, allow_admin_create=True)
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

            next_interval = _flashcard_interval_for_index(interval_index)

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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        if not user_is_admin and not _is_module_unlocked(
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

        profile = _resolve_profile(user, allow_admin_create=user_is_admin)
        if profile is None:
            messages.error(request, "Complete your profile to track progress.")
            return redirect("course_module_stage", slug=slug, order=order, stage=stage_key)

        progress, _ = ModuleStageProgress.objects.get_or_create(
            profile=profile,
            module=module,
            stage_key=stage_key,
        )

        tasks_state = list(progress.completed_tasks or [])
        required = _get_stage_required_tasks(stage_key, module)
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
            afterburner_configs = _get_afterburner_card_configs(course, module)
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

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)
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
                        "title": "Human-first immersion",
                        "description": "We choreograph live interactions with ambitious peers, mentors, and native speakers so English becomes lived, not recited.",
                    },
                    {
                        "title": "Game-layered mastery",
                        "description": "Adaptive missions and cinematic narratives lock in vocabulary, rhythm, and intuition by keeping you in flow state.",
                    },
                    {
                        "title": "Immediate clarity",
                        "description": "Data-rich feedback loops and mentor nudges help you correct in the moment and accelerate compounding gains.",
                    },
                ],
                "modalities": [
                    {
                        "name": "Gravity Rooms",
                        "mode": "In-person",
                        "description": "Deep-dive studio immersions hosted in our cities. You co-create with mentors and peers, surrounded by the energy of a live arena.",
                        "touchpoints": "3-hour labs · mentor council · live reflection pods",
                    },
                    {
                        "name": "Signal Streams",
                        "mode": "Online",
                        "description": "High-tempo live sessions delivered through our digital command center. Adaptive missions, instant feedback, zero commute.",
                        "touchpoints": "60-min live missions · AI rehearsal · async nudges",
                    },
                    {
                        "name": "Dual Engine",
                        "mode": "Duo",
                        "description": "Blend in-person surges with remote precision sprints so momentum never drops—perfect for execs on the move.",
                        "touchpoints": "Monthly summits · weekly online missions · personal strategist",
                    },
                ],
                "commitments": [
                    {
                        "label": "Curation",
                        "body": "Every learner is matched with a pod and mentor team engineered for tension and trust so you never plateau alone.",
                    },
                    {
                        "label": "Evidence",
                        "body": "We capture audio, video, and mission artefacts so you can see the delta in confidence, accuracy, and influence week over week.",
                    },
                    {
                        "label": "Momentum",
                        "body": "Rapid response cycles keep you shipping English in public. No ghosting, no drifting—just guided acceleration.",
                    },
                ],
                "outcomes": [
                    {
                        "metric": "92%",
                        "caption": "of members report thinking in English during live exchanges within 6 weeks",
                    },
                    {
                        "metric": "4.7/5",
                        "caption": "average coach rating for actionable feedback and accountability",
                    },
                    {
                        "metric": "3x",
                        "caption": "increase in on-demand speaking confidence measured across mission recordings",
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
                        "title": "Sunday Systems Reset",
                        "details": "Prime the week with 15-minute async planning, resource drops, and vocabulary packs tuned to upcoming missions.",
                    },
                    {
                        "title": "Mid-week Live Lab",
                        "details": "Immersive scenario where squads tackle real briefs—negotiations, pitches, storytelling—in rapid rotations.",
                    },
                    {
                        "title": "Friday Playback",
                        "details": "Coaches and AI signal engine annotate your clips, highlighting instinct wins and adjustment cues for the next loop.",
                    },
                ],
                "toolkit": [
                    "FOREIGN app for mission briefs, AI rehearsal, and evidence tracking",
                    "Mentor office hours and on-demand voice notes when you need a quick reset",
                    "Community feed with peer accountability, wins, and knowledge exchanges",
                ],
                "modalities": [
                    {
                        "name": "Gravity Rooms",
                        "mode": "In-person",
                        "description": "Anchor weeks where squads meet at our city studios for high-impact labs, feedback circles, and cultural immersions.",
                    },
                    {
                        "name": "Signal Streams",
                        "mode": "Online",
                        "description": "Adaptive live missions delivered through our digital hub, combined with async precision drills and mentor touchpoints.",
                    },
                    {
                        "name": "Dual Engine",
                        "mode": "Duo",
                        "description": "Hybrid flow blending Gravity Rooms surges with Signal Streams cadence—ideal for leaders balancing travel and deep work.",
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
                        "name": "Explorer Pass",
                        "label": "Starter · Signal Streams",
                        "price": "$149/mo",
                        "description": "Launch your English instincts with live online missions, adaptive drills, and mentor guidance wherever you are.",
                        "features": [
                            "3 live Signal Streams missions weekly",
                            "Placement + monthly calibration",
                            "FOREIGN app with unlimited AI rehearsal",
                            "Community accountability pods",
                            "Coach feedback drops every week",
                        ],
                        "animations": {
                            "badge": "fade-up",
                            "card": "fade-scale",
                        },
                    },
                    {
                        "name": "Gravity Labs",
                        "label": "Flagship · Gravity Rooms + Streams",
                        "price": "$389/mo",
                        "description": "The full FOREIGN immersion: in-person surges plus online cadence, engineered for rapid transformation.",
                        "features": [
                            "Bi-weekly Gravity Room immersions",
                            "Weekly Signal Streams missions",
                            "Dedicated mentor strategist",
                            "Quarterly evidence reel & assessment",
                            "Invites to VIP speaker labs",
                        ],
                        "highlight": True,
                        "animations": {
                            "badge": "fade-scale",
                            "card": "fade-up",
                        },
                    },
                    {
                        "name": "Dual Engine Studio",
                        "label": "Hybrid · Executive Duo",
                        "price": "Custom",
                        "description": "Design a bespoke program blending Gravity Rooms, Signal Streams, and concierge coaching for leadership teams.",
                        "features": [
                            "Private Gravity Room summits",
                            "Weekly executive Signal Streams",
                            "Cultural fluency + negotiation labs",
                            "Concierge strategist & evidence analytics",
                            "Quarterly immersion retreats",
                        ],
                        "animations": {
                            "badge": "fade-up",
                            "card": "fade-scale",
                        },
                    },
                ],
                "extras": [
                    {
                        "title": "TEAM LAUNCH",
                        "summary": "Craft a shared playbook for your global team, from cultural onboarding to pitch rehearsals.",
                    },
                    {
                        "title": "IMPACT RETAINER",
                        "summary": "Keep a FOREIGN strategist on call for ongoing missions, evidence reviews, and leadership coaching.",
                    },
                    {
                        "title": "CAMPUS PARTNER",
                        "summary": "Bring FOREIGN to your college or accelerator with tailored cohorts and faculty integration.",
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

        levels = []
        for level in PROGRAM_LEVELS:
            enriched = level.copy()
            enriched['course_count'] = sum(1 for course in courses if course.fluency_level == level['code'])
            levels.append(enriched)

        context.update(
            {
                "program_levels": levels,
                "course_groups": course_groups,
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
