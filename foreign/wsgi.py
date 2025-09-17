"""WSGI config for the FOREIGN project."""
from django.core.wsgi import get_wsgi_application
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foreign.settings")

application = get_wsgi_application()
