from rest_framework.routers import DefaultRouter

from api.views import TenantViewSet, BillingViewSet
from api.schemas import TenantSchema, BillingSchema

api_router = DefaultRouter()
api_router.register(r"tenants", TenantViewSet, basename="tenant")
api_router.register(r"billing", BillingViewSet, basename="billing")

__all__ = [
    "api_router",
    "TenantViewSet",
    "BillingViewSet",
    "TenantSchema",
    "BillingSchema",
]