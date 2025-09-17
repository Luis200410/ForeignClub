"""Views powering the FOREIGN experience."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView

from .forms import CourseEnrollmentForm, SignUpForm
from .models import Course, CourseEnrollment, CourseModule, Profile



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


class AuthLogoutView(LogoutView):
    next_page = reverse_lazy("landing")


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


class DashboardView(LoginRequiredMixin, TemplateView):
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
            }
        )

        return context


class CourseListView(LoginRequiredMixin, TemplateView):
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


class CourseDetailView(LoginRequiredMixin, TemplateView):
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

        context.update(
            {
                "course": course,
                "modules": course.modules.all(),
                "enrollment": enrollment,
                "form": CourseEnrollmentForm(),
            }
        )
        return context


class CourseEnrollView(LoginRequiredMixin, View):
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

class ProgramListView(TemplateView):
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


class ProgramDetailView(TemplateView):
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

