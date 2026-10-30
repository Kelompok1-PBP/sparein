from django.db.models import Count, Exists, Max, Min, OuterRef, Q
from django.shortcuts import get_object_or_404

from core.permissions import is_member
from parts.models import PartSource, SparePart

PUBLIC_SOURCE_FIELDS = ("vendor_name", "city", "url", "last_checked")
MEMBER_SOURCE_FIELDS = (*PUBLIC_SOURCE_FIELDS, "price", "currency", "contact")


def get_part_qs(*, q=None, device=None, category=None, max_price=None):
    """Queryset suku cadang buat dipakai modul lain.

    Filter kosong di-skip, device pakai slug perangkat,
    category boleh satu nilai atau list
    """
    qs = SparePart.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(part_number__icontains=q))
    if device:
        qs = qs.filter(compatibilities__device__slug=device)
    if category:
        qs = qs.filter(category__in=[category] if isinstance(category, str) else category)
    if max_price:
        # Exists biar ga dobel baris kalau tokonya banyak
        cheap = PartSource.objects.filter(part=OuterRef("pk"), price__lte=max_price)
        qs = qs.filter(Exists(cheap))
    return qs


def get_part_or_404(slug):
    """Ambil suku cadang by slug kalau ga ada 404."""
    return get_object_or_404(SparePart, slug=slug)


def visible_part_qs(user, **filters):
    """Queryset buat halaman dan API, auth filter harga ada di sini.

    Visitor ga dapet anotasi harga dan max_price di-drop,
    soalnya filter harga bisa dipakai buat nebak harganya
    """
    if not is_member(user):
        filters.pop("max_price", None)
        return get_part_qs(**filters).annotate(source_count=Count("sources"))
    return get_part_qs(**filters).annotate(
        source_count=Count("sources"),
        lowest_price=Min("sources__price"),
        highest_price=Max("sources__price"),
    )


def _visible_sources(qs, user, *extra):
    if is_member(user):
        return qs.order_by("price", "vendor_name").values(*extra, *MEMBER_SOURCE_FIELDS)
    return qs.order_by("vendor_name").values(*extra, *PUBLIC_SOURCE_FIELDS)


def get_sources_for(part, user):
    """Toko penjual satu suku cadang.

    price, currency, contact cuma di-select buat member. Visitor diurutin
    by nama toko biar urutannya ga bocorin toko mana yang paling murah
    """
    return _visible_sources(part.sources.all(), user)


def get_sources_for_parts(parts, user):
    """Sama kayak get_sources_for tapi buat banyak suku cadang dalam satu query.

    Hasilnya dict part_id -> list toko, dipakai API biar ga N+1
    """
    grouped = {}
    for row in _visible_sources(PartSource.objects.filter(part__in=parts), user, "part_id"):
        grouped.setdefault(row.pop("part_id"), []).append(row)
    return grouped
