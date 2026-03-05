import threading
from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.module_loading import import_string

_thread_local = threading.local()

class TenantsAppConfig(AppConfig):
    name = "tenants"
    verbose_name = "Tenants"

    def ready(self):
        self.register_signals()
        if not hasattr(settings, "TENANT_MODEL"):
            raise ImproperlyConfigured("TENANT_MODEL setting must be defined.")
        self.TenantModel = import_string(settings.TENANT_MODEL)

    def register_signals(self):
        @receiver(post_save, sender=self.apps.get_model("tenants", "Tenant"))
        def create_default_settings(sender, instance, created, **kwargs):
            if created:
                from .models import TenantSetting
                TenantSetting.objects.create(tenant=instance, key="currency", value="USD")
        @receiver(pre_delete, sender=self.apps.get_model("tenants", "Tenant"))
        def delete_related_data(sender, instance, **kwargs):
            instance.tenantsetting_set.all().delete()

def get_current_tenant(request=None):
    if request is not None:
        tenant = getattr(request, "_current_tenant", None)
        if tenant:
            return tenant
    return getattr(_thread_local, "current_tenant", None)

def set_current_tenant(tenant):
    _thread_local.current_tenant = tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        try:
            tenant = apps.get_model("tenants", "Tenant").objects.get(subdomain=host)
            request._current_tenant = tenant
            set_current_tenant(tenant)
        except apps.get_model("tenants", "Tenant").DoesNotExist:
            pass
        response = self.get_response(request)
        return response

def register_admin(admin_site):
    from .admin import TenantAdmin, TenantSettingAdmin
    admin_site.register(apps.get_model("tenants", "Tenant"), TenantAdmin)
    admin_site.register(apps.get_model("tenants", "TenantSetting"), TenantSettingAdmin)

__all__ = [
    "TenantsAppConfig",
    "get_current_tenant",
    "set_current_tenant",
    "TenantMiddleware",
    "register_admin",
]