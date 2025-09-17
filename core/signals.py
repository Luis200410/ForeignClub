"""Signal handlers for core domain events."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import InteractionPreference, Profile

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile(sender, instance: User, created: bool, **_: object) -> None:
    """Provision baseline profile information when a new user registers."""
    if not created:
        return

    profile = Profile.objects.create(
        user=instance,
        display_name=instance.get_full_name() or instance.get_username(),
        native_language="Spanish" if instance.email.endswith(".mx") else "",
    )
    InteractionPreference.objects.create(profile=profile)
