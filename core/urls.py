"""Core URL routes for FOREIGN."""
from django.urls import path

from .views import AuthLoginView, AuthLogoutView, DashboardView, landing, register

urlpatterns = [
    path("", landing, name="landing"),
    path("login/", AuthLoginView.as_view(), name="login"),
    path("logout/", AuthLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
