from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from core.permissions import is_contributor
from devices.forms import DeviceForm
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
        "can_create": is_contributor(request.user),
    })


def device_detail(request, slug):
    return render(request, "devices/detail.html", {"device": get_device_or_404(slug)})


@login_required
def device_create(request):
    if not is_contributor(request.user):
        raise PermissionDenied
    form = DeviceForm(request.POST or None)
    if form.is_valid():
        device = form.save(commit=False)
        device.created_by = request.user
        device.save()
        return redirect("devices:detail", slug=device.slug)
    return render(request, "devices/form.html", {"form": form})
