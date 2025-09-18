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
from .models import Course, CourseEnrollment, CourseModule, Profile, SkillAssessment



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
    return render(request, "core/landing.html")


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

        featured_course = Course.objects.filter(is_published=True).order_by('position', 'title').first() if hasattr(Course, 'position') else Course.objects.filter(is_published=True).order_by('title').first()
        module_links = []
        if featured_course:
            module_links = list(featured_course.modules.all().order_by('order')[:6])

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
                "module_links": module_links,
                "featured_course": featured_course,
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
        profile = getattr(self.request.user, "profile", None)
        enrollment = None
        if profile:
            enrollment = CourseEnrollment.objects.filter(profile=profile, course=course).first()

        modules = (
            CourseModule.objects.filter(course=course)
            .prefetch_related("sessions")
            .order_by("order")
        )

        module_cards = []
        for module in modules:
            weeks = {
                "module": module,
                "sessions": module.sessions.all(),
            }
            module_cards.append(weeks)

        context.update(
            {
                "course": course,
                "modules": module_cards,
                "enrollment": enrollment,
                "form": CourseEnrollmentForm(),
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
        module = get_object_or_404(
            CourseModule.objects.prefetch_related("sessions"),
            course=course,
            order=order,
        )
        sessions = module.sessions.all().order_by("order")
        total_modules = course.modules.count()
        previous_order = order - 1 if order > 1 else None
        next_order = order + 1 if order < total_modules else None

        context.update(
            {
                "course": course,
                "module": module,
                "sessions": sessions,
                "previous_order": previous_order,
                "next_order": next_order,
            }
        )
        return context

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
            context = {
                "course": course,
                "modules": course.modules.all(),
                "enrollment": enrollment,
                "form": form,
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
                "phases": [
                    {
                        "step": "Prime",
                        "headline": "Shape the target",
                        "points": [
                            "Personal calibration calls",
                            "Goal architecture + fluency baselines",
                            "Vocabulary and mindset warmups",
                        ],
                    },
                    {
                        "step": "Immerse",
                        "headline": "Live the language",
                        "points": [
                            "Cinematic missions and performance labs",
                            "Pair + squad exchanges engineered for transfer",
                            "Adaptive AI rehearsal between live missions",
                        ],
                    },
                    {
                        "step": "Elevate",
                        "headline": "Lock the instinct",
                        "points": [
                            "Rapid feedback sprints",
                            "Coach retros + reflection rituals",
                            "Evidence reels to measure the jump",
                        ],
                    },
                ],
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

