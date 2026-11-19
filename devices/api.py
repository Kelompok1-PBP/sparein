from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from devices.selectors import get_device_qs
from devices.serializers import DeviceSerializer


class DevicePagination(PageNumberPagination):
    page_size = 60


class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    """List dan detail device untuk aplikasi mobile, filter sama dengan halaman web."""

    serializer_class = DeviceSerializer
    pagination_class = DevicePagination
    lookup_field = "slug"

    def get_queryset(self):
        params = self.request.query_params
        return get_device_qs(
            **{k: params.get(k, "").strip() for k in ("q", "category", "brand")}
        ).order_by("name")
