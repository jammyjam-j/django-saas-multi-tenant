"""URL configuration for the saas project."""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

from api.routers import APIRouter as router

urlpatterns = [
    path("", include("tenants.urls")),
    path("billing/", include("billing.urls")),
    path("api/", include(router.urls)),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATIC_ROOT},
        ),
    ]