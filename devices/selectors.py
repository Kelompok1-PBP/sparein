from django.shortcuts import get_object_or_404

from devices.models import Device


def get_device_qs(*, q=None, category=None, brand=None):
    """Queryset device buat dipakai modul lain.

    Filter kosong di-skip dan brand case-insensitive
    """
    qs = Device.objects.select_related("category")
    if q:
        qs = qs.filter(name__icontains=q)
    if category:
        qs = qs.filter(category__slug=category)
    if brand:
        qs = qs.filter(brand__iexact=brand)
    return qs


def get_device_or_404(slug):
    """Ambil device by slug kalau ga ada 404."""
    return get_object_or_404(Device.objects.select_related("category"), slug=slug)
