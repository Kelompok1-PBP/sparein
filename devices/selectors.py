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
