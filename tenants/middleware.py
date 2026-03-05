import threading
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import connections
from django.utils.deprecation import MiddlewareMixin

thread_local = threading.local()


class TenantContext:
    def __init__(self, tenant=None):
        self.tenant = tenant

    @property
    def schema_name(self):
        return getattr(self.tenant, "schema_name", None)

    def apply_schema(self):
        if not self.schema_name:
            return
        cursor = connections["default"].cursor()
        try:
            cursor.execute(f"SET search_path TO {self.schema_name}")
        finally:
            cursor.close()


def get_tenant_from_request(request):
    host = request.get_host().split(":")[0]
    subdomain = host.split(".")[0]
    if not hasattr(settings, "TENANT_MODEL"):
        raise ImproperlyConfigured("TENANT_MODEL setting must be defined.")
    tenant_model_path = settings.TENANT_MODEL
    try:
        app_label, model_name = tenant_model_path.split(".")
    except ValueError:
        raise ImproperlyConfigured(
            "TENANT_MODEL must be in the form 'app.Model'."
        )
    try:
        module = __import__(f"{app_label}", fromlist=[model_name])
        TenantModel = getattr(module, model_name)
    except (ImportError, AttributeError):
        raise ImproperlyConfigured(f"Could not load tenant model {tenant_model_path}.")
    try:
        tenant = TenantModel.objects.get(subdomain=subdomain)
    except TenantModel.DoesNotExist:
        raise PermissionDenied("Tenant does not exist.")
    return tenant


class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            tenant = get_tenant_from_request(request)
        except Exception as exc:
            raise PermissionDenied(str(exc))
        thread_local.tenant_context = TenantContext(tenant=tenant)
        thread_local.tenant_context.apply_schema()
        request.tenant = tenant

    def process_response(self, request, response):
        if hasattr(thread_local, "tenant_context"):
            del thread_local.tenant_context
        return response

    def process_exception(self, request, exception):
        if hasattr(thread_local, "tenant_context"):
            del thread_local.tenant_context
        raise exception

    @staticmethod
    def get_current_tenant():
        context = getattr(thread_local, "tenant_context", None)
        return context.tenant if context else None

    @staticmethod
    def get_schema_name():
        context = getattr(thread_local, "tenant_context", None)
        return context.schema_name if context else None"