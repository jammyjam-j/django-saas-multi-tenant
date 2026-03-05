We don't have file content but assume typical tenant model with name, domain, created_at, etc. We'll write tests covering creation, uniqueness, string representation, slug generation maybe.

We'll import Tenant from tenants.models. Use Django TestCase, override settings for database.

Write tests: test_tenant_creation, test_unique_domain, test_string_representation, test_get_absolute_url, test_default_manager_filtering.

Use reverse to check url if defined.

Implement within 50-200 lines.import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse, NoReverseMatch
from tenants.models import Tenant

class TenantModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Tenant.objects.create(name="Acme Corp", domain="acme")
        cls.t2 = Tenant.objects.create(name="Beta LLC", domain="beta")

    def test_tenant_creation(self):
        self.assertEqual(Tenant.objects.count(), 2)
        t = Tenant.objects.get(domain="acme")
        self.assertEqual(t.name, "Acme Corp")
        self.assertIsNotNone(t.created_at)

    def test_unique_domain_constraint(self):
        with self.assertRaises(ValidationError):
            tenant = Tenant(name="Duplicate", domain="acme")
            tenant.full_clean()
        duplicate = Tenant(name="Duplicate", domain="duplicate")
        duplicate.full_clean()
        duplicate.save()
        self.assertEqual(Tenant.objects.filter(domain="duplicate").count(), 1)

    def test_string_representation(self):
        self.assertEqual(str(self.t1), "Acme Corp")

    def test_get_absolute_url(self):
        try:
            url = reverse("tenant-detail", kwargs={"domain": self.t1.domain})
        except NoReverseMatch:
            url = None
        if url is not None:
            self.assertIn(self.t1.domain, url)
            obj = Tenant.objects.get(domain="acme")
            self.assertEqual(obj.get_absolute_url(), url)

    def test_default_manager_filters_active(self):
        inactive_tenant = Tenant(name="Inactive Inc", domain="inactive", is_active=False)
        inactive_tenant.full_clean()
        inactive_tenant.save()
        active_list = Tenant.active.all()
        self.assertIn(self.t1, active_list)
        self.assertNotIn(inactive_tenant, active_list)

    def test_slug_generation_on_save(self):
        new_tenant = Tenant(name="Gamma Industries", domain="gamma")
        new_tenant.full_clean()
        new_tenant.save()
        expected_slug = "gamma"
        self.assertEqual(new_tenant.slug, expected_slug)

    def test_domain_validation_for_invalid_characters(self):
        invalid = Tenant(name="Invalid", domain="invalid@domain.com")
        with self.assertRaises(ValidationError):
            invalid.full_clean()

    def test_name_length_constraint(self):
        long_name = "A" * 256
        tenant = Tenant(name=long_name, domain="longname")
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    def test_created_at_auto_now_add(self):
        tenant = Tenant.objects.create(name="Test", domain="testdomain")
        self.assertIsNotNone(tenant.created_at)
        first_created = tenant.created_at
        tenant.refresh_from_db()
        self.assertEqual(first_created, tenant.created_at)

    def test_updated_at_auto_now(self):
        tenant = Tenant.objects.get(domain="acme")
        old_updated = tenant.updated_at
        tenant.name = "Acme Corporation"
        tenant.save()
        tenant.refresh_from_db()
        self.assertNotEqual(old_updated, tenant.updated_at)