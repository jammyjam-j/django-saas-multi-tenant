import os
import django
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saas.settings')
django.setup()

Tenant = None
Plan = None
Subscription = None
try:
    from tenants.models import Tenant as TenantModel
    Tenant = TenantModel
except Exception:
    pass
try:
    from billing.models import Plan as PlanModel, Subscription as SubModel
    Plan = PlanModel
    Subscription = SubModel
except Exception:
    pass

def create_superuser(username='admin', email='admin@example.com', password='adminpass'):
    User = get_user_model()
    user_qs = User.objects.filter(username=username)
    if not user_qs.exists():
        try:
            user = User.objects.create_superuser(username, email, password)
            return user
        except IntegrityError:
            pass
    return user_qs.first()

def create_default_tenant(name='Demo', domain='demo.example.com'):
    tenant_qs = Tenant.objects.filter(domain=domain)
    if not tenant_qs.exists():
        try:
            tenant = Tenant.objects.create(name=name, domain=domain)
            return tenant
        except IntegrityError:
            pass
    return tenant_qs.first()

def create_default_plan(name='Basic', price_cents=1000):
    plan_qs = Plan.objects.filter(name=name)
    if not plan_qs.exists():
        try:
            plan = Plan.objects.create(name=name, price_cents=price_cents)
            return plan
        except IntegrityError:
            pass
    return plan_qs.first()

def create_subscription(tenant, user, plan):
    sub_qs = Subscription.objects.filter(tenant=tenant, user=user)
    if not sub_qs.exists():
        try:
            sub = Subscription.objects.create(
                tenant=tenant,
                user=user,
                plan=plan,
                status='active'
            )
            return sub
        except IntegrityError:
            pass
    return sub_qs.first()

def main():
    with transaction.atomic():
        admin_user = create_superuser()
        demo_tenant = create_default_tenant()
        basic_plan = create_default_plan()
        if demo_tenant and admin_user and basic_plan:
            create_subscription(demo_tenant, admin_user, basic_plan)

if __name__ == '__main__':
    main()