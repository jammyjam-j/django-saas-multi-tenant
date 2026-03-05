from django.db import connections
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from tenants.models import Tenant
from billing.models import Plan, Subscription
from core.utils import get_tenant_connection_name


@receiver(post_save, sender=Tenant)
def initialize_tenant(sender, instance: Tenant, created: bool, **kwargs):
    if not created:
        return
    connection_name = get_tenant_connection_name(instance.id)
    try:
        with connections[connection_name].cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS tenant_{} CASCADE".format(connection_name))
        default_plan, _ = Plan.objects.get_or_create(
            name="Basic",
            defaults={"price_cents": 999, "interval_months": 1},
        )
        Subscription.objects.create(tenant=instance, plan=default_plan, active=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialize tenant {instance.id}") from exc


@receiver(pre_delete, sender=Tenant)
def cleanup_tenant(sender, instance: Tenant, **kwargs):
    connection_name = get_tenant_connection_name(instance.id)
    try:
        with connections[connection_name].cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS tenant_{} CASCADE".format(connection_name))
    except Exception as exc:
        raise RuntimeError(f"Failed to cleanup tenant {instance.id}") from exc