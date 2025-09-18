"""Views powering the FOREIGN experience."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

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

PRE_SESSION_TASKS = [
    "NotebookLM briefing: theme overview",
    "Vocabulary pack with pronunciation clips",
    "Speaking drill: record a 30-second practice",
    "Micro-quiz to check comprehension",
    "Cultural insight drop",
    "Mission reflection prompt",
]

POST_SESSION_TASKS = [
    "NotebookLM game mission",
    "Spaced repetition review (48h)",
    "Peer feedback exchange",
    "Mini challenge unlocked via app",
    "Signal reminder: next live cue",
    "Evidence upload checkpoint",
]

ALLOWED_ENROLLMENT_STATUSES = {
    CourseEnrollment.EnrollmentStatus.ACTIVE,
    CourseEnrollment.EnrollmentStatus.COMPLETED,
}

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

    try:
        progress = ModuleStageProgress.objects.get(
            profile=profile,
            module=module,
            stage_key=ModuleStageProgress.StageKey.LAUNCH_PAD,
        )
        tasks = list(progress.completed_tasks or [])
    except ModuleStageProgress.DoesNotExist:
        tasks = []

    required = len(PRE_SESSION_TASKS)
    if len(tasks) < required:
        tasks.extend([False] * (required - len(tasks)))

    stage_one_complete = required > 0 and all(bool(flag) for flag in tasks[:required])
    unlocks["flight-deck"] = stage_one_complete
    unlocks["afterburner"] = stage_one_complete
    return unlocks


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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)

        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        sessions = module.sessions.all().order_by("order")
        total_modules = course.modules.count()
        previous_order = order - 1 if order > 1 else None
        next_order = order + 1 if order < total_modules else None

        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)

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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(self.request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        stage_unlocks = _get_stage_unlocks(user, course, module, enrollment, can_view_course)

        if stage_key != "launch-pad" and not stage_unlocks.get(stage_key, False):
            messages.warning(self.request, "Complete the previous stage to unlock this mission.")
            return redirect("course_module", slug=slug, order=order)

        sessions = module.sessions.all().order_by("order")

        pre_session_resources = [
            {
                "title": task,
                "url": "#",
            }
            for task in PRE_SESSION_TASKS
        ]

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

        profile = getattr(user, "profile", None)
        launch_tasks = []
        if stage_key == ModuleStageProgress.StageKey.LAUNCH_PAD and profile:
            progress, _ = ModuleStageProgress.objects.get_or_create(
                profile=profile,
                module=module,
                stage_key=ModuleStageProgress.StageKey.LAUNCH_PAD,
            )
            tasks_state = list(progress.completed_tasks or [])
            required = len(PRE_SESSION_TASKS)
            if len(tasks_state) < required:
                tasks_state.extend([False] * (required - len(tasks_state)))
            for idx, resource in enumerate(pre_session_resources, start=1):
                launch_tasks.append(
                    {
                        "index": idx,
                        "title": resource["title"],
                        "url": resource["url"],
                        "completed": tasks_state[idx - 1],
                    }
                )

        context.update(
            {
                "course": course,
                "module": module,
                "sessions": sessions,
                "stage": stage_config,
                "stage_key": stage_key,
                "stage_cards": stage_cards,
                "pre_session_resources": pre_session_resources,
                "post_session_games": post_session_games,
                "post_session_loops": post_session_loops,
                "stage_unlocks": stage_unlocks,
                "launch_pad_tasks": launch_tasks,
                "can_view_course": can_view_course,
            }
        )
        return context


class ModuleStageTaskToggleView(PlacementRequiredMixin, View):
    login_url = "login"

    def post(self, request, slug: str, order: int, stage: str, index: int):
        stage_key = stage
        if stage_key != ModuleStageProgress.StageKey.LAUNCH_PAD:
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
        enrollment, can_view_course = _get_enrollment_and_access(user, course)
        if not can_view_course:
            messages.warning(request, "Finish your application to unlock weekly missions.")
            return redirect("course_detail", slug=slug)

        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )

        profile = getattr(user, "profile", None)
        if profile is None:
            messages.error(request, "Complete your profile to track progress.")
            return redirect("course_module_stage", slug=slug, order=order, stage=stage_key)

        progress, _ = ModuleStageProgress.objects.get_or_create(
            profile=profile,
            module=module,
            stage_key=ModuleStageProgress.StageKey.LAUNCH_PAD,
        )

        tasks_state = list(progress.completed_tasks or [])
        required = len(PRE_SESSION_TASKS)
        if len(tasks_state) < required:
            tasks_state.extend([False] * (required - len(tasks_state)))

        if index < 1 or index > required:
            raise Http404

        task_idx = index - 1
        tasks_state[task_idx] = not bool(tasks_state[task_idx])
        progress.completed_tasks = tasks_state
        progress.save(update_fields=["completed_tasks", "updated_at"])

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
