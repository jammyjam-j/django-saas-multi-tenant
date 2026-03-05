from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from tenants.models import Tenant
from billing.models import Subscription, Invoice
from api.serializers import (
    TenantSerializer,
    SubscriptionSerializer,
    InvoiceSerializer,
)
from api.permissions import IsAdminOrReadOnly, IsTenantOwnerOrReadOnly
from api.pagination import StandardResultsSetPagination


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        if tenant.is_active:
            return Response(
                {"detail": "Tenant already active."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.is_active = True
        tenant.save(update_fields=["is_active"])
        return Response({"status": "activated"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        if not tenant.is_active:
            return Response(
                {"detail": "Tenant already inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.is_active = False
        tenant.save(update_fields=["is_active"])
        return Response({"status": "deactivated"}, status=status.HTTP_200_OK)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related("tenant", "plan")
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminOrReadOnly, IsTenantOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(tenant__owner=user)

    def perform_create(self, serializer):
        tenant_id = self.kwargs.get("tenant_pk")
        tenant = get_object_or_404(Tenant, pk=tenant_id)
        serializer.save(tenant=tenant, created_by=self.request.user)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.select_related("subscription", "subscription__tenant")
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminOrReadOnly, IsTenantOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(subscription__tenant__owner=user)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        invoice = self.get_object()
        if invoice.paid_at is not None:
            return Response(
                {"detail": "Invoice already paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invoice.mark_as_paid(user=request.user)
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def recent(self, request):
        invoices = self.get_queryset().order_by("-created_at")[:10]
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)