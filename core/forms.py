"""Forms used across the FOREIGN experience."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


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
