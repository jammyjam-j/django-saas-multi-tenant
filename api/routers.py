from rest_framework import routers
from api.views import (
    TenantViewSet,
    BillingPlanViewSet,
    SubscriptionViewSet,
    InvoiceViewSet,
    UsageRecordViewSet,
)

class APIRootRouter(routers.DefaultRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, trailing_slash=False, **kwargs)
        self.routes[0].url = r'(?P<format>\.json|\.api)?$'
        self.routes[1].url = r'(?P<format>\.json|\.api)?/$'

router = APIRootRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'plans', BillingPlanViewSet, basename='plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'usages', UsageRecordViewSet, basename='usage')

urlpatterns = router.urls

---