Open api/views.py content.We don't have file contents. But assume typical CRUD for tenants, billing etc. Schemas could be Pydantic models or DRF schema? Might use drf-spectacular. Simpler: define serializers in schemas.py used by views. Let's craft.

We'll import from rest_framework import serializers. Define TenantSchema, BillingPlanSchema, InvoiceSchema, APIResponse.

Use nested fields.

Return 50-200 lines.

Let's implement.from datetime import date
from typing import List, Optional

from django.contrib.auth.models import User
from django.utils.timezone import now

from rest_framework import serializers

from tenants.models import Tenant
from billing.models import Plan, Invoice, Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = ("id",)


class TenantCreateSchema(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    domain = serializers.URLField()
    owner_id = serializers.IntegerField()

    def validate_owner_id(self, value: int) -> int:
        try:
            User.objects.get(pk=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Owner does not exist.") from exc
        return value

    def create(self, validated_data):
        owner = User.objects.get(pk=validated_data["owner_id"])
        tenant = Tenant.objects.create(
            name=validated_data["name"],
            domain=validated_data["domain"],
            owner=owner,
        )
        return tenant


class TenantSchema(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = ("id", "name", "domain", "created_at", "owner")
        read_only_fields = ("id", "created_at", "owner")


class PlanSchema(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", "name", "price_cents", "currency", "description")
        read_only_fields = ("id",)


class InvoiceItemSerializer(serializers.Serializer):
    description = serializers.CharField()
    amount_cents = serializers.IntegerField()

    def validate_amount_cents(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("Amount cannot be negative.")
        return value


class InvoiceCreateSchema(serializers.Serializer):
    tenant_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()
    items = InvoiceItemSerializer(many=True)

    def validate_tenant_id(self, value: int) -> int:
        if not Tenant.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Tenant does not exist.")
        return value

    def validate_plan_id(self, value: int) -> int:
        if not Plan.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Plan does not exist.")
        return value

    def create(self, validated_data):
        tenant = Tenant.objects.get(pk=validated_data["tenant_id"])
        plan = Plan.objects.get(pk=validated_data["plan_id"])
        invoice = Invoice.objects.create(
            tenant=tenant,
            plan=plan,
            total_cents=sum(item["amount_cents"] for item in validated_data["items"]),
            issued_at=now(),
            due_date=date.today() + timedelta(days=30),
        )
        return invoice


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("id", "invoice", "status", "processed_at")
        read_only_fields = ("id",)


class InvoiceSchema(serializers.ModelSerializer):
    tenant = TenantSchema(read_only=True)
    plan = PlanSchema(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "tenant",
            "plan",
            "total_cents",
            "issued_at",
            "due_date",
            "status",
            "transactions",
        )
        read_only_fields = ("id",)


class APIResponseSchema(serializers.Serializer):
    status = serializers.CharField()
    data = serializers.JSONField(required=False)
    errors = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs):
        if not attrs.get("status") in {"success", "error"}:
            raise serializers.ValidationError("Status must be 'success' or 'error'.")
        return attrs


class PaginatedResponseSchema(serializers.Serializer):
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    per_page = serializers.IntegerField()
    items = serializers.ListSerializer(child=serializers.DictField())

    def validate(self, attrs):
        if attrs["page"] < 1:
            raise serializers.ValidationError("Page must be >= 1.")
        if attrs["per_page"] <= 0:
            raise serializers.ValidationError("Per page must be > 0.")
        return attrs