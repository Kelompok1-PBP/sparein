from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from core.permissions import is_admin, is_contributor
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
    device = get_device_or_404(slug)
    return render(request, "devices/detail.html", {
        "device": device,
        "can_edit": _can_edit(request.user, device),
        "can_delete": is_admin(request.user),
    })


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


def _can_edit(user, device):
    return is_admin(user) or (is_contributor(user) and device.created_by_id == user.id)


@login_required
def device_edit(request, slug):
    device = get_device_or_404(slug)
    if not _can_edit(request.user, device):
        raise PermissionDenied
    form = DeviceForm(request.POST or None, instance=device)
    if form.is_valid():
        form.save()
        return redirect("devices:detail", slug=device.slug)
    return render(request, "devices/form.html", {"form": form})


@login_required
def device_delete(request, slug):
    device = get_device_or_404(slug)
    if not is_admin(request.user):
        raise PermissionDenied
    if request.method == "POST":
        device.delete()
        return redirect("devices:list")
    return render(request, "devices/confirm_delete.html", {"device": device})
