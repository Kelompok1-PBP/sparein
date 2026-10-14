from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from core.permissions import is_member
from devices.selectors import get_device_qs
from parts.models import SparePart
from parts.selectors import get_part_or_404, get_sources_for, visible_part_qs

STALE_DAYS = 30


def _price(value):
    try:
        price = int(value)
    except ValueError:
        return None
    # dibatasi biar angka kepanjangan ga bikin query error
    return min(price, 1_000_000_000) if price > 0 else None


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
    parts = list(visible_part_qs(request.user, **filters)[:60])  # tanpa pagination dulu
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
        "empty_message": None if parts else _empty_message(filters, device),
        "show_reset": any(filters.values()),
    })


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
    })
