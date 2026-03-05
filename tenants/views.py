Let's view tenants/models.py.Cannot fetch file, but assume typical tenant model with fields name, domain, etc. We'll implement ListCreateAPIView and RetrieveUpdateDestroyAPIView using DRF. Use serializers imported. Provide permission classes maybe from api.permissions. Also handle errors. Let's write.from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from tenants.models import Tenant
from tenants.serializers import TenantSerializer
from api.permissions import IsAuthenticatedAndAdminOrReadOnly


class TenantListCreateView(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticatedAndAdminOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            TenantSerializer(tenant).data, status=status.HTTP_201_CREATED, headers=headers
        )


class TenantRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticatedAndAdminOrReadOnly]
    lookup_field = "pk"

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=bool(request.method == "PATCH"))
        if not serializer.is_valid():
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant = serializer.save()
        return Response(TenantSerializer(tenant).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)