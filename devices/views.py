from django.shortcuts import render

from devices.models import DeviceCategory
from devices.selectors import get_device_or_404, get_device_qs


def _filters(request):
    return {k: request.GET.get(k, "").strip() for k in ("q", "category", "brand")}


def device_list(request):
    filters = _filters(request)
    return render(request, "devices/list.html", {
        "devices": get_device_qs(**filters)[:60],  # ponytail: tanpa pagination dulu
        "categories": DeviceCategory.objects.all(),
        "filters": filters,
    })


def device_detail(request, slug):
    return render(request, "devices/detail.html", {"device": get_device_or_404(slug)})
