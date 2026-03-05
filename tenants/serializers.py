from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tenant

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Tenant
        fields = ("id", "name", "domain", "created_at", "owner", "owner_username")
        read_only_fields = ("id", "created_at", "owner_username")

    def validate_domain(self, value):
        if Tenant.objects.filter(domain=value).exclude(id=getattr(self.instance, "id", None)).exists():
            raise serializers.ValidationError("Domain must be unique.")
        return value


class TenantCreateSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True)

    class Meta:
        model = Tenant
        fields = ("name", "domain", "owner_email")

    def validate_domain(self, value):
        if Tenant.objects.filter(domain=value).exists():
            raise serializers.ValidationError("Domain must be unique.")
        return value

    def create(self, validated_data):
        owner_email = validated_data.pop("owner_email")
        try:
            owner = User.objects.get(email=owner_email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"owner_email": "User with this email does not exist."})
        tenant = Tenant.objects.create(owner=owner, **validated_data)
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("name", "domain")

    def validate_domain(self, value):
        if Tenant.objects.filter(domain=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Domain must be unique.")
        return value

    def update(self, instance, validated_data):
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance