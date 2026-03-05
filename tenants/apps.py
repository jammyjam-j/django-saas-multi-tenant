from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

class TenantsConfig(AppConfig):
    name = 'tenants'
    verbose_name = 'Tenants'

    def ready(self):
        try:
            from . import models  # noqa: F401
            from . import serializers  # noqa: F401
            from . import views  # noqa: F401
            from . import urls  # noqa: F401
            from . import middleware  # noqa: F401
            from . import admin  # noqa: F401
        except Exception as exc:
            raise ImproperlyConfigured(f'Failed to import tenants components: {exc}') from exc

        try:
            from django.db.models.signals import post_save, pre_delete
            from .models import Tenant
            from .signals import tenant_created, tenant_deleted
            post_save.connect(tenant_created, sender=Tenant)
            pre_delete.connect(tenant_deleted, sender=Tenant)
        except Exception as exc:
            raise ImproperlyConfigured(f'Failed to connect signals for tenants: {exc}') from exc

        try:
            from django.urls import include, path
            from .urls import urlpatterns as tenant_urls
            from saas.urls import urlpatterns as root_urlpatterns
            if hasattr(root_urlpatterns, 'extend'):
                root_urlpatterns.extend([path('tenants/', include((tenant_urls, self.name), namespace='tenants'))])
        except Exception:
            pass

        try:
            from django.contrib.admin.sites import site
            from .admin import TenantAdmin
            site.register(Tenant, TenantAdmin)
        except Exception as exc:
            raise ImproperlyConfigured(f'Failed to register admin for tenants: {exc}') from exc

        try:
            from rest_framework.routers import DefaultRouter
            from .views import TenantViewSet
            router = DefaultRouter()
            router.register(r'tenants', TenantViewSet, basename='tenant')
            if hasattr(root_urlpatterns, 'extend'):
                root_urlpatterns.extend(router.urls)
        except Exception:
            pass

        try:
            from core.middleware import CustomMiddleware
            from django.utils.module_loading import import_string
            middleware_path = import_string('tenants.middleware.TenantMiddleware')
            if middleware_path not in self.get_middleware():
                self._middleware.append(middleware_path)
        except Exception:
            pass

    def get_middleware(self):
        return []

    def _add_middleware(self, path):
        if hasattr(self, '_middleware'):
            self._middleware.append(path)
        else:
            self._middleware = [path]