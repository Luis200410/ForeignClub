"""Management command to provision a FOREIGN superuser from environment variables."""
from __future__ import annotations

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update the default FOREIGN superuser from environment variables."

    def handle(self, *args: object, **options: object) -> str:
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            missing = [
                name
                for name, value in (
                    ("DJANGO_SUPERUSER_USERNAME", username),
                    ("DJANGO_SUPERUSER_EMAIL", email),
                    ("DJANGO_SUPERUSER_PASSWORD", password),
                )
                if not value
            ]
            raise CommandError(
                "Missing required environment values: " + ", ".join(missing)
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if not created:
            user.email = email
            user.is_staff = True
            user.is_superuser = True

        user.set_password(password)
        if created:
            user.save()
        else:
            user.save(update_fields=["email", "password", "is_staff", "is_superuser"])

        message = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{message} superuser '{username}'."))
        return ""
