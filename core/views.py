"""Views powering the FOREIGN experience."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import SignUpForm


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
        context["experiences"] = [
            {
                "title": "Live Language Exchanges",
                "description": "Meet native speakers in curated micro-sessions designed to spark real conversations.",
            },
            {
                "title": "Immersive Story Games",
                "description": "Play narrative-driven games that adapt to your vocabulary level in real time.",
            },
            {
                "title": "Rapid Feedback Labs",
                "description": "Receive instant pronunciation and grammar feedback powered by expert coaches.",
            },
        ]
        return context
