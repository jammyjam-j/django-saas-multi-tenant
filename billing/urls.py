from django.urls import path, include
from rest_framework.routers import DefaultRouter

from billing.views import SubscriptionViewSet, InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]