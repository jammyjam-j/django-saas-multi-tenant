from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from tenants.models import Tenant


class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "subdomain", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("name", "subdomain")
    readonly_fields = ("created_at", "updated_at")

    actions = ["deactivate_tenants"]

    def deactivate_tenants(self, request, queryset):
        updated_count = queryset.update(is_active=False)
        self.message_user(
            request,
            _("Deactivated %(count)d tenant(s).") % {"count": updated_count},
            messages.SUCCESS,
        )

    deactivate_tenants.short_description = _("Deactivate selected tenants")


admin.site.register(Tenant, TenantAdmin)