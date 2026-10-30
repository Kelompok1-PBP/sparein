from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.permissions import is_admin, is_contributor, is_member
from devices.selectors import get_device_qs
from parts.forms import MAX_PRICE, CompatibilityFormSet, SourceFormSet, SparePartForm
from parts.mock_api import SyncFailure, fetch_parts, upsert_parts
from parts.models import PartCompatibility, SparePart
from parts.selectors import (
    get_part_or_404,
    get_sources_for,
    get_sources_for_parts,
    visible_part_qs,
)

STALE_DAYS = 30
LIMIT = 60  # tanpa pagination dulu
QUICK_PRICES = (50_000, 100_000, 250_000, 500_000)


def wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def _deny(request):
    """Visitor diarahin ke halaman masuk, yang udah login tapi ga punya izin dapet 403."""
    if wants_json(request):
        status = 403 if request.user.is_authenticated else 401
        return JsonResponse({"error": "Akses ditolak."}, status=status)
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    raise PermissionDenied


def _can_edit(user, part):
    return is_admin(user) or (is_contributor(user) and part.created_by_id == user.id)


def _price(value):
    try:
        price = int(value)
    except ValueError:
        return None
    # dibatasi biar angka kepanjangan ga bikin query error
    return min(price, MAX_PRICE) if price > 0 else None


def _filters(request, *, with_price):
    """Filter dari query string, nilai yang ga valid dibuang aja."""
    categories = request.GET.getlist("category")
    return {
        "q": request.GET.get("q", "").strip(),
        "device": request.GET.get("device", "").strip(),
        "category": [c for c in categories if c in SparePart.Category.values],
        "max_price": _price(request.GET.get("max_price", "")) if with_price else None,
    }


def _empty_message(filters, device):
    if device and not (filters["q"] or filters["category"] or filters["max_price"]):
        return f"Belum ada suku cadang terdaftar buat {device.name}."
    if any(filters.values()):
        return "Belum ada suku cadang yang cocok."
    return "Belum ada suku cadang terdaftar."


def part_list(request):
    show_price = is_member(request.user)
    filters = _filters(request, with_price=show_price)
    parts = list(visible_part_qs(request.user, **filters)[:LIMIT])
    # dropdown cuma perangkat yang udah punya suku cadang, plus yang lagi dipilih
    devices = list(
        get_device_qs()
        .filter(Q(part_compatibilities__isnull=False) | Q(slug=filters["device"]))
        .distinct()
        .order_by("name")
    )
    device = next((d for d in devices if d.slug == filters["device"]), None)
    return render(request, "parts/part_list.html", {
        "parts": parts,
        "devices": devices,
        "categories": SparePart.Category.choices,
        "filters": filters,
        "show_price": show_price,
        "quick_prices": QUICK_PRICES,
        "empty_message": None if parts else _empty_message(filters, device),
        "show_reset": any(filters.values()),
        "can_create": is_contributor(request.user),
        "can_sync": is_admin(request.user),
    })


@require_http_methods(["GET"])
def part_api(request):
    """Data direktori buat filter AJAX di list.js.

    Visitor ga dapet kunci harga sama sekali, toko-tokonya juga tanpa price dan contact
    """
    show_price = is_member(request.user)
    parts = list(visible_part_qs(request.user, **_filters(request, with_price=show_price))[:LIMIT])
    sources = get_sources_for_parts(parts, request.user)
    results = []
    for part in parts:
        item = {
            "id": part.pk,
            "name": part.name,
            "slug": part.slug,
            "part_number": part.part_number,
            "category": part.category,
            "category_label": part.get_category_display(),
            "image_url": part.image_url,
            "url": reverse("parts:detail", args=[part.slug]),
            "source_count": part.source_count,
        }
        if show_price:
            item["lowest_price"] = part.lowest_price
            item["highest_price"] = part.highest_price
        item["sources"] = sources.get(part.pk, [])
        results.append(item)
    return JsonResponse({"results": results, "limit": LIMIT})


def part_detail(request, slug):
    part = get_part_or_404(slug)
    sources = list(get_sources_for(part, request.user))
    today = timezone.localdate()
    for source in sources:
        source["stale"] = (today - source["last_checked"]).days > STALE_DAYS
    prices = [s["price"] for s in sources if "price" in s]
    return render(request, "parts/part_detail.html", {
        "part": part,
        "compatibilities": part.compatibilities.select_related("device").order_by("device__name"),
        "sources": sources,
        "show_price": is_member(request.user),
        "lowest_price": min(prices, default=None),
        "highest_price": max(prices, default=None),
        "can_edit": _can_edit(request.user, part),
        "can_delete": is_admin(request.user),
    })


def _editor(request, part=None):
    """Form tambah dan edit, isinya suku cadang + perangkat yang cocok + toko."""
    creating = part is None
    # judul diambil sebelum validasi, soalnya form ngubah part.name waktu is_valid()
    title = "Tambah suku cadang" if creating else f"Edit {part.name}"
    cancel_url = reverse("parts:list") if creating else reverse("parts:detail", args=[part.slug])
    data = request.POST if request.method == "POST" else None
    form = SparePartForm(data, instance=part)
    initial = [
        {"device": c.device_id, "note": c.note}
        for c in (part.compatibilities.order_by("device__name") if part else [])
    ]
    compat = CompatibilityFormSet(data, initial=initial, prefix="compat")
    sources = SourceFormSet(data, instance=form.instance, prefix="sources")

    if data is not None and all([form.is_valid(), compat.is_valid(), sources.is_valid()]):
        with transaction.atomic():
            part = form.save(commit=False)
            if creating:
                part.created_by = request.user
            part.save()
            part.compatibilities.all().delete()
            PartCompatibility.objects.bulk_create(
                PartCompatibility(part=part, **row) for row in compat.rows()
            )
            today = timezone.localdate()
            for row in sources.forms:
                if row.has_changed():
                    row.instance.last_checked = today  # baru diisi orang, anggap baru dicek
            sources.save()
        if wants_json(request):
            return JsonResponse(
                {"id": part.pk, "slug": part.slug, "url": reverse("parts:detail", args=[part.slug])},
                status=201 if creating else 200,
            )
        messages.success(request, "Suku cadang tersimpan.")
        return redirect("parts:detail", slug=part.slug)

    if data is not None and wants_json(request):
        return JsonResponse({"errors": {
            "part": form.errors.get_json_data(),
            "compat": [f.errors.get_json_data() for f in compat.forms],
            "compat_errors": compat.non_form_errors().get_json_data(),
            "sources": [f.errors.get_json_data() for f in sources.forms],
            "source_errors": sources.non_form_errors().get_json_data(),
        }}, status=400)
    return render(request, "parts/part_form.html", {
        "form": form,
        "compat": compat,
        "sources": sources,
        "title": title,
        "cancel_url": cancel_url,
    }, status=400 if data is not None else 200)


@require_http_methods(["GET", "POST"])
def part_create(request):
    if not is_contributor(request.user):
        return _deny(request)
    return _editor(request)


@require_http_methods(["GET", "POST"])
def part_edit(request, slug):
    part = get_part_or_404(slug)
    if not _can_edit(request.user, part):
        return _deny(request)
    return _editor(request, part)


@require_http_methods(["GET", "POST"])
def part_delete(request, slug):
    part = get_part_or_404(slug)
    if not is_admin(request.user):
        return _deny(request)
    if request.method == "POST":
        part.delete()  # toko dan kecocokan ikut kehapus (CASCADE)
        if wants_json(request):
            return JsonResponse({"deleted": True})
        messages.success(request, "Suku cadang dihapus.")
        return redirect("parts:list")
    return render(request, "parts/part_confirm_delete.html", {"part": part})


@require_http_methods(["POST"])
def part_sync(request):
    """Tombol sync buat admin, soalnya di PWS ga ada shell buat jalanin sync_parts."""
    if not is_admin(request.user):
        return _deny(request)
    try:
        counts = upsert_parts(fetch_parts())
    except SyncFailure as exc:
        if wants_json(request):
            return JsonResponse({"error": str(exc)}, status=502)
        messages.error(request, str(exc))
        return redirect("parts:list")
    if wants_json(request):
        return JsonResponse(counts)
    messages.success(
        request,
        f"Sinkronisasi selesai: {counts['parts']} suku cadang, {counts['sources']} toko, "
        f"{counts['skipped']} dilewati.",
    )
    return redirect("parts:list")
