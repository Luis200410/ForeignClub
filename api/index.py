import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foreign.settings")

# Expose the WSGI application for Vercel's Python runtime
app = get_wsgi_application()
handler = app
