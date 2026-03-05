# django‑saas‑multi‑tenant

A lightweight, fully‑featured multi‑tenant SaaS platform built on Django, providing tenant isolation, billing integration and a RESTful API.

---

## Overview

`django-saas-multi-tenant` is designed for developers who need to spin up a secure, scalable SaaS application with minimal friction.  
It isolates each customer (tenant) at the database level, handles subscription billing via Stripe, and exposes CRUD APIs that respect tenant boundaries. The project comes bundled with Docker, CI/CD pipelines, and automated tests.

---

## Features

- **Tenant isolation** – separate schemas per tenant using `django-tenants`.
- **Row‑level security** – automatic filtering of data to the current tenant.
- **Billing & subscription management** – Stripe integration with webhooks and usage metering.
- **REST API** – versioned endpoints, pagination, custom permissions.
- **Admin UI** – per‑tenant dashboards and billing panels.
- **Docker & Docker Compose** – reproducible development environment.
- **CI/CD** – GitHub Actions workflow for linting, testing, and building images.
- **Testing suite** – unit tests for models, views, API endpoints, and billing logic.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Web framework | Django 5.x |
| Database | PostgreSQL (schema‑based multi‑tenancy) |
| ORM & migrations | django‑tenants, South |
| Billing | Stripe SDK |
| API | Django REST Framework |
| Asynchronous support | ASGI + Channels |
| Frontend | HTMX + Tailwind CSS (via static files) |
| Containerization | Docker, docker‑compose |
| CI | GitHub Actions |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/jammyjam-j/django-saas-multi-tenant

cd django-saas-multi-tenant

# Build and start containers
docker compose up -d --build

# Run migrations
docker compose exec web python manage.py migrate
```

The application will be accessible at `http://localhost:8000`.

---

## Usage Examples

### Creating a Tenant

```bash
curl -X POST http://localhost:8000/api/tenants/ \
     -H "Content-Type: application/json" \
     -d '{"domain":"acme.example.com","name":"Acme Corp"}'
```

The response includes the tenant ID and schema name.

### Subscribing to a Plan

```bash
curl -X POST http://localhost:8000/api/billing/subscribe/ \
     -H "Content-Type: application/json" \
     -d '{"tenant_id":1,"plan":"pro","stripe_token":"tok_visa"}'
```

### Accessing Tenant Dashboard

Navigate to `http://localhost:8000/dashboard/acme.example.com/` to view the tenant‑specific interface.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/tenants/` | Create a new tenant |
| GET | `/api/tenants/{id}/` | Retrieve tenant details |
| POST | `/api/billing/subscribe/` | Subscribe a tenant to a plan |
| POST | `/api/billing/cancel/` | Cancel an active subscription |
| GET | `/api/dashboard/` | List tenants for the current user |

All endpoints are versioned under `/api/v1/`. Refer to `api/schemas.py` for detailed schemas.

---

## References and Resources

- [Building a multi‑tenant SaaS on Django](https://brigita.co/blog/application-development-adems/building-multi-tenant-saas-on-django-tenant-schemas-row-level-security-billing/)
- [GitHub – ychtsa/django_multitenant_saas](https://github.com/ychtsa/django_multitenant_saas)
- [2026 Django SaaS Starter Kit](https://medium.com/@yogeshkrishnanseeniraj/2026-django-saas-starter-kit-async-views-htmx-frontend-stripe-and-multi-tenancy-included-aad3d507b456)
- [Create a Tenant with Django – Part 2](https://www.youtube.com/watch?v=zr2eWCkXjyo)
- [Field‑Ready Complete Guide to Multi‑Tenant SaaS](https://blog.greeden.me/en/2025/12/24/field-ready-complete-guide-designing-a-multi-tenant-saas-in-laravel-tenant-isolation-db-schema-row-domain-url-strategy-billing-authorization-auditing-performance-and-an-access/)
- [How to Build a Multi‑Tenant SaaS Application with Django](https://readmedium.com/how-to-build-a-multi-tenant-saas-application-with-django-fe2d0325bb67)
- [DjangoTenants – Multi‑Tenant SaaS Development](https://codingeasypeasy.com/blog/django-tenants-multi-tenant-saas-application-development-with-django/)
- [Unveiling the Power of Multi‑Tenancy: An Abstract Understanding](https://www.linkedin.com/pulse/building-scalable-multi-tenant-systems-django-ankit-kundariya)
- [Show HN – ReadyKit – Superfast SaaS Starter with Multi‑Tenant](https://news.ycombinator.com/item?id=46094552)
- [Laravel vs Django and Rails for SaaS Development](https://www.vincentschmalbach.com/laravel-vs-django-and-rails-for-saas-development/)

---

## Contributing

Please read the contribution guidelines in the repository.  
Issues and pull requests are welcome: https://github.com/jammyjam-j/django-saas-multi-tenant/issues.

---

## License

MIT © 2026