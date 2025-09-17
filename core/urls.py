"""Core URL routes for FOREIGN."""
from django.urls import path

from .views import (
    AuthLoginView,
    AuthLogoutView,
    CourseDetailView,
    CourseEnrollView,
    CourseListView,
    DashboardView,
    ProgramDetailView,
    ProgramListView,
    landing,
    register,
)

urlpatterns = [
    path("", landing, name="landing"),
    path("login/", AuthLoginView.as_view(), name="login"),
    path("logout/", AuthLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("courses/", CourseListView.as_view(), name="course_list"),
    path("courses/<slug:slug>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<slug:slug>/enroll/", CourseEnrollView.as_view(), name="course_enroll"),
    path("programs/", ProgramListView.as_view(), name="program_list"),
    path("programs/<str:code>/", ProgramDetailView.as_view(), name="program_detail"),
]
