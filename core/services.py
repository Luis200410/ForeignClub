"""Business logic services for the FOREIGN platform."""
import random
from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any

from django.db.models import QuerySet
from django.utils import formats, timezone

from .config import (
    AFTERBURNER_CARD_LIBRARY,
    AFTERBURNER_SLOT_SEQUENCE,
    ALLOWED_ENROLLMENT_STATUSES,
    FLIGHT_DECK_SLOT_SEQUENCE,
    FLIGHT_DECK_TASKS,
    LAUNCH_PAD_DEFAULT_TASKS,
)
from .constants import (
    AFTERBURNER_GAME,
    FLASHCARD_SRS_INTERVALS,
    MODULE_STAGE_SEQUENCE,
    NOTEBOOK_LM_APP_URL,
)
from .models import (
    Course,
    CourseEnrollment,
    CourseModule,
    ModuleAfterburnerActivity,
    ModuleFlightDeckActivity,
    ModuleGame,
    ModuleGameFlashcardProgress,
    ModuleLaunchPadTask,
    ModuleLiveMeeting,
    ModuleLiveMeetingSignup,
    ModuleMeetingPairing,
    ModuleStageProgress,
    Profile,
)


class ProfileService:
    @staticmethod
    def resolve_profile(user, *, allow_admin_create: bool = False) -> Profile | None:
        """Return the user's profile, auto-creating one for admins when needed."""
        profile = getattr(user, "profile", None)
        if profile is not None or not getattr(user, "is_authenticated", False):
            return profile

        if allow_admin_create and getattr(user, "is_superuser", False):
            display_name = (
                user.get_full_name() or user.get_username() or "Mission Control"
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


class ContentService:
    @staticmethod
    def get_launch_pad_task_configs(
        course: Course | None, module: CourseModule | None
    ) -> list[dict[str, Any]]:
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
                    ModuleLaunchPadTask.objects.filter(
                        module=module, is_active=True
                    ).order_by("order", "id")
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

    @staticmethod
    def get_flight_deck_activity_configs(
        module: CourseModule | None,
    ) -> list[dict[str, str]]:
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

    @staticmethod
    def get_afterburner_card_configs(
        course: Course | None,
        module: CourseModule | None = None,
    ) -> list[dict[str, Any]]:
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

        configs: list[dict[str, Any]] = []
        for slot in AFTERBURNER_SLOT_SEQUENCE:
            activity = module_activities.get(slot)
            fallback_card = fallback_level_map.get(slot, {})
            if slot == ModuleAfterburnerActivity.Slot.GAME:
                game_instance = getattr(
                    activity, "game", None
                ) or GamificationService.resolve_adaptive_game(module)
                configs.append(
                    {
                        "slot": slot,
                        "title": (
                            activity.title
                            if activity and activity.title
                            else AFTERBURNER_GAME["title"]
                        ),
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
                        activity.title
                        if activity and activity.title
                        else fallback_card.get("title", "")
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


class GamificationService:
    @staticmethod
    def resolve_adaptive_game(module: CourseModule | None) -> ModuleGame | None:
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
            if (
                game.is_active
                and game.game_type == ModuleGame.GameType.ADAPTIVE_FLASHCARDS
            ):
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

    @staticmethod
    def ensure_flashcard_progress_map(
        profile: Profile,
        game: ModuleGame,
    ) -> dict[int, ModuleGameFlashcardProgress]:
        """Ensure progress rows exist for each active flashcard and return a map."""
        now = timezone.now()
        flashcards = list(
            game.flashcards.filter(is_active=True).order_by("order", "id")
        )
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

    @staticmethod
    def flashcard_interval_for_index(index: int) -> timedelta:
        if index < 0:
            index = 0
        if not FLASHCARD_SRS_INTERVALS:
            return timedelta(minutes=5)
        if index >= len(FLASHCARD_SRS_INTERVALS):
            index = len(FLASHCARD_SRS_INTERVALS) - 1
        return FLASHCARD_SRS_INTERVALS[index]


class MeetingService:
    @staticmethod
    def pair_key(primary_id: int, partner_id: int | None) -> tuple[int, int] | None:
        if primary_id is None or partner_id is None:
            return None
        return (
            (primary_id, partner_id)
            if primary_id <= partner_id
            else (partner_id, primary_id)
        )

    @staticmethod
    def assign_meeting_pairs(
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
                key = MeetingService.pair_key(primary_id, candidate)
                if key and key not in avoided_pairs and key not in used_this_round:
                    candidate_index = idx
                    break

            if candidate_index is None:
                assignments.append((primary_id, None))
                continue

            partner_id = remaining.pop(candidate_index)
            normalized = MeetingService.pair_key(primary_id, partner_id)
            if normalized:
                used_this_round.add(normalized)
                assignments.append(normalized)
            else:
                assignments.append((primary_id, partner_id))

        if remaining:
            assignments.append((remaining.pop(), None))

        return assignments, used_this_round

    @staticmethod
    def build_pair_map(
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

    @staticmethod
    def ensure_meeting_pairings(
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

        participant_ids = [
            signup.profile_id for signup in participants if signup.profile_id
        ]
        if not participant_ids:
            return {}

        historical_pairs = {
            key
            for key in (
                MeetingService.pair_key(primary_id, partner_id)
                for primary_id, partner_id in ModuleMeetingPairing.objects.filter(
                    module=module
                )
                .exclude(meeting=meeting)
                .values_list("profile_primary_id", "profile_partner_id")
            )
            if key
        }

        ModuleMeetingPairing.objects.filter(meeting=meeting).delete()

        activities = list(
            module.meeting_activities.filter(is_active=True).order_by("order")
        )
        if not activities:
            return {}

        avoided_pairs = set(historical_pairs)
        pairings_to_create: list[ModuleMeetingPairing] = []

        for activity in activities:
            assignments, used_this_round = MeetingService.assign_meeting_pairs(
                participant_ids, avoided_pairs
            )
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

                ordered_pair = MeetingService.pair_key(primary_id, partner_id)
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

        return MeetingService.build_pair_map(meeting)


class AccessService:
    @staticmethod
    def get_enrollment_and_access(
        user, course: Course
    ) -> tuple[CourseEnrollment | None, bool]:
        profile = getattr(user, "profile", None)
        enrollment = None
        if profile:
            enrollment = CourseEnrollment.objects.filter(
                profile=profile, course=course
            ).first()
        can_view = (
            bool(enrollment and enrollment.status in ALLOWED_ENROLLMENT_STATUSES)
            or user.is_staff
            or user.is_superuser
        )
        return enrollment, can_view

    @staticmethod
    def get_stage_required_tasks(stage_key: str, module: CourseModule) -> int:
        if stage_key == ModuleStageProgress.StageKey.LAUNCH_PAD:
            return len(
                ContentService.get_launch_pad_task_configs(
                    getattr(module, "course", None), module
                )
            )
        if stage_key == ModuleStageProgress.StageKey.FLIGHT_DECK:
            return len(ContentService.get_flight_deck_activity_configs(module))
        if stage_key == ModuleStageProgress.StageKey.AFTERBURNER:
            return len(
                ContentService.get_afterburner_card_configs(
                    getattr(module, "course", None), module
                )
            )
        return 0

    @staticmethod
    def get_stage_unlocks(
        user,
        course: Course,
        module: CourseModule,
        enrollment: CourseEnrollment | None = None,
        can_view_course: bool = False,
    ) -> dict[str, bool]:
        unlocks = {stage["key"]: False for stage in MODULE_STAGE_SEQUENCE}
        unlocks["launch-pad"] = can_view_course
        if not unlocks["launch-pad"]:
            return unlocks

        profile = getattr(user, "profile", None)
        if profile is None:
            return unlocks

        launch_configs = ContentService.get_launch_pad_task_configs(course, module)

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

        # If there are no configured Launch Pad tasks, treat the stage as complete so learners
        # are not blocked from continuing through the module.
        stage_one_complete = required == 0 or all(
            bool(flag) for flag in tasks[:required]
        )
        unlocks["flight-deck"] = stage_one_complete

        flight_tasks_required = AccessService.get_stage_required_tasks(
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
                flight_tasks.extend(
                    [False] * (flight_tasks_required - len(flight_tasks))
                )
            elif len(flight_tasks) > flight_tasks_required:
                flight_tasks = flight_tasks[:flight_tasks_required]

            meetings_exist = ModuleLiveMeetingSignup.objects.filter(
                profile=profile,
                module=module,
            ).exists()

            if meetings_exist:
                if not flight_tasks:
                    flight_tasks = [False] * flight_tasks_required
                if flight_tasks and not flight_tasks[0]:
                    flight_tasks[0] = True
                    if flight_progress is None:
                        flight_progress, _ = ModuleStageProgress.objects.get_or_create(
                            profile=profile,
                            module=module,
                            stage_key=ModuleStageProgress.StageKey.FLIGHT_DECK,
                            defaults={"completed_tasks": flight_tasks},
                        )
                        if flight_progress.completed_tasks != flight_tasks:
                            flight_progress.completed_tasks = flight_tasks
                            flight_progress.save(update_fields=["completed_tasks", "updated_at"])
                    else:
                        flight_progress.completed_tasks = flight_tasks
                        flight_progress.save(
                            update_fields=["completed_tasks", "updated_at"]
                        )

            elif flight_tasks and flight_tasks[0]:
                flight_tasks[0] = False
                if flight_progress is not None:
                    flight_progress.completed_tasks = flight_tasks
                    flight_progress.save(
                        update_fields=["completed_tasks", "updated_at"]
                    )

            flight_stage_complete = all(
                bool(flag) for flag in flight_tasks[:flight_tasks_required]
            )
        else:
            # No configured Flight Deck tasks should not block Afterburner.
            flight_stage_complete = True

        unlocks["afterburner"] = flight_stage_complete
        return unlocks

    @staticmethod
    def is_module_unlocked(
        user,
        course: Course,
        module: CourseModule,
        enrollment: CourseEnrollment | None = None,
        can_view_course: bool = False,
    ) -> bool:
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
            previous_module = CourseModule.objects.filter(
                course=course, order=previous_order
            ).first()

        if previous_module is None:
            return True

        previous_unlocks = AccessService.get_stage_unlocks(
            user,
            course,
            previous_module,
            enrollment=enrollment,
            can_view_course=can_view_course,
        )
        return bool(previous_unlocks.get("flight-deck", False))
