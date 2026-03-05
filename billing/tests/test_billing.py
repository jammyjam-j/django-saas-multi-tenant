import json
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from tenants.models import Tenant
from billing.models import Invoice, Subscription, Payment


@pytest.fixture
def tenant(db):
    user = User.objects.create_user(username="tenantuser", password="pass")
    return Tenant.objects.create(name="TestTenant", owner=user)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def subscription(tenant):
    return Subscription.objects.create(
        tenant=tenant,
        plan_name="Pro",
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=30),
        active=True,
    )


@pytest.fixture
def invoice(subscription):
    return Invoice.objects.create(
        subscription=subscription,
        amount=99.99,
        status="pending",
        due_date=timezone.now().date() + timedelta(days=15),
    )


@pytest.mark.django_db
def test_create_invoice(client, tenant, subscription):
    url = reverse("invoice-list")
    data = {
        "subscription": subscription.id,
        "amount": 49.99,
        "due_date": (timezone.now().date() + timedelta(days=10)).isoformat(),
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    payload = response.json()
    assert payload["subscription"] == subscription.id
    assert float(payload["amount"]) == 49.99
    invoice = Invoice.objects.get(id=payload["id"])
    assert invoice.amount == 49.99
    assert invoice.due_date.isoformat() == data["due_date"]


@pytest.mark.django_db
def test_invoice_status_transition(client, invoice):
    url = reverse("invoice-detail", args=[invoice.id])
    response = client.patch(url, {"status": "paid"}, format="json")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "paid"
    invoice.refresh_from_db()
    assert invoice.status == "paid"


@pytest.mark.django_db
def test_subscription_activation(client, tenant):
    url = reverse("subscription-list")
    data = {
        "tenant": tenant.id,
        "plan_name": "Basic",
        "start_date": timezone.now().date().isoformat(),
        "end_date": (timezone.now().date() + timedelta(days=30)).isoformat(),
        "active": True,
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    payload = response.json()
    subscription = Subscription.objects.get(id=payload["id"])
    assert subscription.plan_name == "Basic"
    assert subscription.active is True


@pytest.mark.django_db
def test_overdue_invoices(client, invoice):
    url = reverse("invoice-overdue-list")
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload]
    if invoice.status == "pending" and invoice.due_date < timezone.now().date():
        assert invoice.id in ids
    else:
        assert invoice.id not in ids


@pytest.mark.django_db
def test_payment_processing(client, invoice):
    url = reverse("payment-list")
    data = {
        "invoice": invoice.id,
        "amount": invoice.amount,
        "method": "card",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 201
    payload = response.json()
    payment = Payment.objects.get(id=payload["id"])
    assert payment.invoice_id == invoice.id
    assert float(payment.amount) == invoice.amount
    invoice.refresh_from_db()
    assert invoice.status == "paid"


@pytest.mark.django_db
def test_invalid_invoice_amount(client, subscription):
    url = reverse("invoice-list")
    data = {
        "subscription": subscription.id,
        "amount": -10.00,
        "due_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 400
    assert "amount" in response.json()


@pytest.mark.django_db
def test_subscription_expiry(client, tenant):
    subscription = Subscription.objects.create(
        tenant=tenant,
        plan_name="Trial",
        start_date=timezone.now().date() - timedelta(days=40),
        end_date=timezone.now().date() - timedelta(days=10),
        active=True,
    )
    url = reverse("subscription-detail", args=[subscription.id])
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert payload["active"] is False


@pytest.mark.django_db
def test_invoice_detail(client, invoice):
    url = reverse("invoice-detail", args=[invoice.id])
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == invoice.id
    assert float(payload["amount"]) == invoice.amount


@pytest.mark.django_db
def test_subscription_list(client, tenant):
    Subscription.objects.create(
        tenant=tenant,
        plan_name="Standard",
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=30),
        active=True,
    )
    url = reverse("subscription-list")
    response = client.get(url)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1


@pytest.mark.django_db
def test_payment_cannot_exceed_invoice(client, invoice):
    url = reverse("payment-list")
    data = {
        "invoice": invoice.id,
        "amount": invoice.amount + 100.00,
        "method": "card",
    }
    response = client.post(url, data, format="json")
    assert response.status_code == 400
    assert "amount" in response.json()