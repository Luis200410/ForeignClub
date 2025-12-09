import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "foreign.settings")

# WSGI entrypoint for Vercel (@vercel/python expects `app`)
app = get_wsgi_application()
