import os
import sys
from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from django.http import HttpResponse
from django.utils.module_loading import import_string

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saas.settings")

application = get_asgi_application()

try:
    from core.middleware import CustomMiddleware
except Exception:
    CustomMiddleware = None

if CustomMiddleware is not None:
    application = CustomMiddleware(application)

async def health_check(request):
    return HttpResponse("OK", status=200)

router = [
    path("health/", health_check),
]

from django.core.asgi import URLRouter

application = URLRouter(router + getattr(application, "router", []))