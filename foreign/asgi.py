"""ASGI config for the FOREIGN project."""
from django.core.asgi import get_asgi_application
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foreign.settings")

application = get_asgi_application()
