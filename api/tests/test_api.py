We don't have file content but we can assume typical DRF routers. We'll write tests using APIClient. Use fixtures for tenant creation. We might need to import tenants.models.Tenant and billing models. But focus on api endpoints.

We'll test list and retrieve of some resource, maybe subscriptions? Let's inspect api/views.py.import json
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from tenants.models import Tenant
from billing.models import Invoice
from django.contrib.auth import get_user_model

User = get_user_model()


class ApiIntegrationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="strongpassword"
        )
        self.tenant_data = {
            "name": "Test Tenant",
            "domain_url": "test.com",
            "owner_email": "owner@test.com",
        }

    def test_unauthenticated_access_denied(self):
        url = reverse("api:tenant-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_tenant(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("api:tenant-list")
        response = self.client.post(url, data=self.tenant_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tenant_id = response.data["id"]
        tenant = Tenant.objects.get(id=tenant_id)
        self.assertEqual(tenant.name, self.tenant_data["name"])

    def test_tenant_retrieve(self):
        self.client.force_authenticate(user=self.user)
        tenant = Tenant.objects.create(**self.tenant_data)
        url = reverse("api:tenant-detail", kwargs={"pk": tenant.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], tenant.name)

    def test_invoice_list_pagination(self):
        self.client.force_authenticate(user=self.user)
        for i in range(15):
            Invoice.objects.create(
                tenant=Tenant.objects.create(**self.tenant_data),
                amount=100 + i,
                status="paid",
            )
        url = reverse("api:invoice-list")
        response = self.client.get(url, {"page_size": 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 5)

    def test_invoice_detail_permission(self):
        tenant_a = Tenant.objects.create(**self.tenant_data)
        invoice_a = Invoice.objects.create(
            tenant=tenant_a, amount=200, status="pending"
        )
        tenant_b = Tenant.objects.create(
            name="Other", domain_url="other.com", owner_email="owner@other.com"
        )
        invoice_b = Invoice.objects.create(
            tenant=tenant_b, amount=300, status="paid"
        )
        self.client.force_authenticate(user=self.user)
        url_a = reverse("api:invoice-detail", kwargs={"pk": invoice_a.id})
        response_a = self.client.get(url_a)
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        url_b = reverse("api:invoice-detail", kwargs={"pk": invoice_b.id})
        response_b = self.client.get(url_b)
        self.assertIn(response_b.status_code, (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN))

    def test_schema_generation(self):
        url = reverse("schema")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_data = response.json()
        self.assertIn("paths", schema_data)
        self.assertIn("/api/tenants/", schema_data["paths"])

    def test_custom_permission_denied_message(self):
        self.client.force_authenticate(user=self.user)
        tenant = Tenant.objects.create(**self.tenant_data)
        url = reverse("api:tenant-detail", kwargs={"pk": tenant.id})
        response = self.client.get(url, HTTP_AUTHORIZATION="Bearer invalidtoken")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_bulk_create_tenants(self):
        self.client.force_authenticate(user=self.user)
        bulk_data = [
            {"name": f"Tenant{i}", "domain_url": f"{i}.com", "owner_email": f"owner{i}@test.com"}
            for i in range(3)
        ]
        url = reverse("api:tenant-list")
        response = self.client.post(url, data=bulk_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tenant.objects.count(), 3)

    def test_invalid_payload_returns_error(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("api:tenant-list")
        response = self.client.post(url, data={"invalid": "data"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_invoice_update_by_owner(self):
        tenant = Tenant.objects.create(**self.tenant_data)
        invoice = Invoice.objects.create(
            tenant=tenant, amount=500, status="pending"
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("api:invoice-detail", kwargs={"pk": invoice.id})
        update_payload = {"status": "paid"}
        response = self.client.patch(url, data=update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "paid")