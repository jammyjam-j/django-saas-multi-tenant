import re
from typing import Callable, Iterable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin
from tenants.models import Tenant


class TenantMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        self.domain_pattern = re.compile(r"^(?P<subdomain>[^.]+)\.")
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> None | HttpResponse:
        host = request.get_host().split(":")[0]
        match = self.domain_pattern.match(host)
        tenant: Tenant | None = None
        if match:
            subdomain = match.group("subdomain")
            try:
                tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
            except Tenant.DoesNotExist:
                pass
        if not tenant:
            try:
                tenant = Tenant.objects.filter(is_default=True).first()
            except Exception:
                tenant = None
        request.tenant = tenant

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        super().__init__(get_response)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "no-referrer"
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response["Content-Security-Policy"] = csp
        return response


class AllowedHostsMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        self.allowed_hosts = set(settings.ALLOWED_HOSTS)
        super().__init__(get_response)

    def process_request(self, request: HttpRequest) -> None | HttpResponse:
        host = request.get_host().split(":")[0]
        if host not in self.allowed_hosts:
            return HttpResponse(status=400)


class RequestLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        super().__init__(get_response)

    def process_view(self, request: HttpRequest, view_func: Callable, view_args: Iterable, view_kwargs: dict) -> None | HttpResponse:
        path = request.path
        method = request.method
        user = getattr(request, "user", None)
        tenant_id = getattr(request.tenant, "id", None)
        # logging is assumed to be configured elsewhere
        import logging

        logger = logging.getLogger("django.request")
        logger.info(
            f"{method} {path} by {user} tenant {tenant_id}"
        )
        return None


class CacheControlMiddleware(MiddlewareMixin):
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response
        super().__init__(get_response)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if getattr(request, "tenant", None):
            response["Cache-Control"] = "private, max-age=60"
        else:
            response["Cache-Control"] = "public, max-age=120"
        return response