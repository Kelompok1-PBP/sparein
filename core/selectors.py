from django.db.models import Count, Q

from devices.models import Device, DeviceCategory
from guides.selectors import get_guide_qs


def top_categories(limit=8):
    """Kategori yang punya perangkat, paling banyak dulu. Buat kisi kategori di beranda."""
    return (
        DeviceCategory.objects.select_related("parent")
        .annotate(total=Count("devices"))
        .filter(total__gt=0)
        .order_by("-total", "name")[:limit]
    )


def latest_guides(limit=3):
    """Panduan terbit terbaru plus jumlah langkahnya."""
    return (
        get_guide_qs()
        .filter(published=True)
        .annotate(step_total=Count("steps"))
        .order_by("-pk")[:limit]
    )


def popular_devices(limit=4):
    """Perangkat dengan panduan terbit terbanyak, buat chip pencarian di hero."""
    return (
        Device.objects.annotate(
            guide_total=Count("repair_guides", filter=Q(repair_guides__published=True))
        )
        .filter(guide_total__gt=0)
        .order_by("-guide_total", "name")[:limit]
    )
