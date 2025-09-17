from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "FOREIGN Experience"

    def ready(self) -> None:
        from . import signals  # noqa: F401

        return super().ready()
