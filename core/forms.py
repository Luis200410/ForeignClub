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
