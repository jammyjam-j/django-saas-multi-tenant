from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied

class TenantContextMixin:
    def _get_tenant(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            raise PermissionDenied("Tenant context missing.")
        return tenant

class IsAuthenticatedAndTenant(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        self._get_tenant(request)
        return True

class IsTenantAdmin(BasePermission, TenantContextMixin):
    def has_object_permission(self, request, view, obj):
        tenant = self._get_tenant(request)
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_admin = getattr(user_profile, "is_admin", False)
        belongs_to_tenant = getattr(obj, "tenant_id", None) == tenant.id
        return is_admin and belongs_to_tenant

class IsBillingUser(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_billing = getattr(user_profile, "role", "") == "billing"
        tenant = self._get_tenant(request)
        return is_billing and request.user.tenant_id == tenant.id

class IsSuperUserOrTenantAdmin(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_admin = getattr(user_profile, "is_admin", False)
        tenant = self._get_tenant(request)
        return is_admin and request.user.tenant_id == tenant.id

class IsTenantOwner(BasePermission, TenantContextMixin):
    def has_object_permission(self, request, view, obj):
        tenant = self._get_tenant(request)
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_owner = getattr(user_profile, "role", "") == "owner"
        belongs_to_tenant = getattr(obj, "tenant_id", None) == tenant.id
        return is_owner and belongs_to_tenant

class IsTenantReadOnly(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        tenant = self._get_tenant(request)
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_admin_or_owner = getattr(user_profile, "role", "") in ("admin", "owner")
        return is_admin_or_owner and request.user.tenant_id == tenant.id

class IsBillingReadOnly(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        billing_role = getattr(request.user.profile, "role", "") if hasattr(request.user, "profile") else ""
        tenant = self._get_tenant(request)
        return billing_role == "billing" and request.user.tenant_id == tenant.id

class HasPermissionOrDenied(BasePermission):
    def __init__(self, required_permission):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        user_perms = getattr(request.user, "get_all_permissions", lambda: set())()
        return self.required_permission in user_perms

class PermissionRequiredMixin:
    required_permission = None

    def get_permission_classes(self):
        if not self.required_permission:
            return []
        return [HasPermissionOrDenied(self.required_permission)] + super().get_permission_classes()

class IsTenantManager(BasePermission, TenantContextMixin):
    def has_object_permission(self, request, view, obj):
        tenant = self._get_tenant(request)
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_manager = getattr(user_profile, "role", "") == "manager"
        belongs_to_tenant = getattr(obj, "tenant_id", None) == tenant.id
        return is_manager and belongs_to_tenant

class IsTenantMember(BasePermission, TenantContextMixin):
    def has_object_permission(self, request, view, obj):
        tenant = self._get_tenant(request)
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_member = getattr(user_profile, "role", "") == "member"
        belongs_to_tenant = getattr(obj, "tenant_id", None) == tenant.id
        return is_member and belongs_to_tenant

class IsTenantStaff(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_profile = getattr(request.user, "profile", None)
        if not user_profile:
            return False
        is_staff = getattr(user_profile, "role", "") in ("admin", "manager")
        tenant = self._get_tenant(request)
        return is_staff and request.user.tenant_id == tenant.id

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        owner = getattr(obj, "owner_id", None)
        return request.user.id == owner

class HasAnyPermissionMixin:
    required_permissions = []

    def get_permission_classes(self):
        classes = []
        for perm in self.required_permissions:
            classes.append(HasPermissionOrDenied(perm))
        return classes + super().get_permission_classes()

class IsTenantActive(BasePermission, TenantContextMixin):
    def has_permission(self, request, view):
        tenant = self._get_tenant(request)
        return getattr(tenant, "is_active", False)

class HasBillingCapability(BasePermission, TenantContextMixin):
    def has_object_permission(self, request, view, obj):
        tenant = self._get_tenant(request)
        billing_capable = getattr(tenant, "billing_enabled", False)
        user_profile = getattr(request.user, "profile", None)
        return billing_capable and (user_profile.role in ("admin", "owner"))

class IsApiConsumer(BasePermission):
    def has_permission(self, request, view):
        api_token = request.headers.get("Authorization")
        if not api_token:
            return False
        return True

class ApiKeyRequiredMixin:
    required_api_key = None

    def get_permission_classes(self):
        if not self.required_api_key:
            return []
        return [IsApiConsumer] + super().get_permission_classes()