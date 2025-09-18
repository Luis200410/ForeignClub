"""Forms used across the FOREIGN experience."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    AvailabilityWindow,
    LearningGoal,
    Profile,
    ProgressLog,
    SkillAssessment,
)


class SignUpForm(UserCreationForm):
    """Custom sign-up form with minimalist styling hooks."""

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "Email",
            "class": "form-control form-control-lg",
        }),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Username", "class": "form-control form-control-lg"}
        )
        self.fields["password1"].widget.attrs.update(
            {
                "placeholder": "Password",
                "class": "form-control form-control-lg",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "placeholder": "Confirm password",
                "class": "form-control form-control-lg",
            }
        )


class CourseEnrollmentForm(forms.Form):
    """Simple enrollment form capturing learner intent."""

    motivation = forms.CharField(
        label="Why this course?",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Share what you want to unlock, so we can tailor your experience.",
                "class": "form-control",
            }
        ),
        required=False,
    )

    def clean_motivation(self):
        motivation = self.cleaned_data.get("motivation", "").strip()
        if motivation and len(motivation) < 12:
            raise forms.ValidationError("Tell us a bit more about what you're aiming for.")
        return motivation


class AccountForm(forms.Form):
    """Allow learners to update basic account and profile information."""

    first_name = forms.CharField(max_length=30, required=False, label="First name")
    last_name = forms.CharField(max_length=150, required=False, label="Last name")
    email = forms.EmailField(label="Email")
    display_name = forms.CharField(max_length=120, label="Display name")
    headline = forms.CharField(max_length=180, required=False, label="Headline", widget=forms.TextInput(attrs={"placeholder": "What describes your current focus?"}))
    country = forms.CharField(max_length=100, required=False, label="Country")
    timezone = forms.CharField(max_length=64, required=False, label="Timezone")
    native_language = forms.CharField(max_length=80, required=False, label="Native language")
    bio = forms.CharField(required=False, label="Bio", widget=forms.Textarea(attrs={"rows": 3}))
    linkedin_url = forms.URLField(required=False, label="LinkedIn URL")
    phone_number = forms.CharField(max_length=32, required=False, label="Phone number")
    target_focus = forms.ChoiceField(label="Focus", choices=Profile._meta.get_field("target_focus").choices)
    desired_fluency_level = forms.ChoiceField(label="Target level", choices=Profile.FluencyLevel.choices)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        profile = getattr(user, "profile", None)
        initial = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }
        target_focus_default = Profile._meta.get_field("target_focus").default
        fluency_default = Profile.FluencyLevel.INTERMEDIATE

        if profile:
            initial.update(
                {
                    "display_name": profile.display_name,
                    "headline": profile.headline,
                    "country": profile.country,
                    "timezone": profile.timezone,
                    "native_language": profile.native_language,
                    "bio": profile.bio,
                    "linkedin_url": profile.linkedin_url,
                    "phone_number": profile.phone_number,
                    "target_focus": profile.target_focus,
                    "desired_fluency_level": profile.desired_fluency_level,
                }
            )
        else:
            initial.setdefault("display_name", user.get_username())
        initial.setdefault("target_focus", target_focus_default)
        initial.setdefault("desired_fluency_level", fluency_default)
        for name, value in initial.items():
            if name in self.fields:
                self.fields[name].initial = value
        # Styling
        for name, field in self.fields.items():
            if name in {"target_focus", "desired_fluency_level"}:
                field.widget.attrs.setdefault("class", "form-select")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self):
        cleaned = self.cleaned_data
        user = self.user
        user.first_name = cleaned.get("first_name", "")
        user.last_name = cleaned.get("last_name", "")
        user.email = cleaned["email"]
        user.save(update_fields=["first_name", "last_name", "email"])

        profile = getattr(user, "profile", None)
        if profile is None:
            profile = Profile.objects.create(user=user, display_name=cleaned.get("display_name") or user.get_username())
        profile.display_name = cleaned.get("display_name") or profile.display_name
        profile.headline = cleaned.get("headline") or ""
        profile.country = cleaned.get("country") or ""
        profile.timezone = cleaned.get("timezone") or profile.timezone
        profile.native_language = cleaned.get("native_language") or ""
        profile.bio = cleaned.get("bio") or ""
        profile.linkedin_url = cleaned.get("linkedin_url") or ""
        profile.phone_number = cleaned.get("phone_number") or ""
        profile.target_focus = cleaned.get("target_focus") or profile.target_focus
        profile.desired_fluency_level = cleaned.get("desired_fluency_level") or profile.desired_fluency_level
        profile.save()
        return user


class PlacementExamForm(forms.Form):
    level = forms.ChoiceField(
        label="Choose your current level",
        choices=Profile.FluencyLevel.choices,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    focus = forms.ChoiceField(
        label="Primary focus",
        choices=Profile._meta.get_field("target_focus").choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    intent = forms.CharField(
        label="What do you want to unlock?",
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Presenting at global standups, negotiating, storytelling..."}),
        required=False,
    )


class LearningGoalForm(forms.ModelForm):
    class Meta:
        model = LearningGoal
        fields = ["title", "focus_area", "success_metric", "target_date", "priority", "is_primary"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Pitch confidently, negotiate in English"}),
            "focus_area": forms.Select(attrs={"class": "form-select"}),
            "success_metric": forms.TextInput(attrs={"class": "form-control"}),
            "target_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProgressLogForm(forms.ModelForm):
    tags = forms.CharField(
        label="Tags",
        required=False,
        help_text="Comma separated labels",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "confidence, pitch, Q4"}),
    )

    class Meta:
        model = ProgressLog
        fields = ["summary", "details", "impact_rating"]
        widgets = {
            "summary": forms.TextInput(attrs={"class": "form-control"}),
            "details": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "What happened?"}),
            "impact_rating": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
        }

    def clean_tags(self):
        raw = self.cleaned_data.get("tags", "")
        if not raw:
            return []
        return [t.strip() for t in raw.split(',') if t.strip()]


class AvailabilityWindowForm(forms.ModelForm):
    class Meta:
        model = AvailabilityWindow
        fields = ["day_of_week", "start_time", "end_time", "timezone"]
        widgets = {
            "day_of_week": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "timezone": forms.TextInput(attrs={"class": "form-control"}),
        }


class SkillAssessmentForm(forms.ModelForm):
    class Meta:
        model = SkillAssessment
        fields = ["assessment_type", "fluency_level", "score", "assessed_by", "notes", "evidence_url"]
        widgets = {
            "assessment_type": forms.Select(attrs={"class": "form-select"}),
            "fluency_level": forms.Select(attrs={"class": "form-select"}),
            "score": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "assessed_by": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control", "placeholder": "Key observations"}),
            "evidence_url": forms.URLInput(attrs={"class": "form-control"}),
        }
