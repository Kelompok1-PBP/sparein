"""Sync dari Sparein Mock API. Halaman tetap baca database, API cuma dipanggil waktu sync."""

import json
from pathlib import Path

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from devices.selectors import get_device_qs
from parts.forms import SourceForm, SparePartForm
from parts.models import PartCompatibility

CACHE_KEY = "parts-mock-api"
CACHE_SECONDS = 3600
SNAPSHOT = Path(__file__).resolve().parent / "data" / "parts_snapshot.json"


class SyncFailure(ValueError):
    pass


class ApiSourceForm(SourceForm):
    # beda sama form manual, toko dari API bawa mata uang dan tanggal cek sendiri
    class Meta(SourceForm.Meta):
        fields = [*SourceForm.Meta.fields, "currency", "last_checked"]


def fetch_parts(*, fresh=False):
    """JSON dari mock API, di-cache sejam biar tombol sync ga nembak API terus."""
    data = None if fresh else cache.get(CACHE_KEY)
    if data is not None:
        return data
    try:
        response = requests.get(settings.PARTS_API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise SyncFailure(
            "Mock API tidak dapat diakses. Data yang tersimpan tetap dipakai."
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("parts"), list):
        raise SyncFailure("Respons Mock API tidak valid. Data yang tersimpan tetap dipakai.")
    cache.set(CACHE_KEY, data, CACHE_SECONDS)
    return data


def load_snapshot():
    """Salinan lokal v1/parts.json, dipakai sync_parts kalau API mati."""
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def _save(form_class, row, **extra):
    """Simpan satu baris by external_id, None kalau ditolak.

    Divalidasi pakai form yang sama kayak input manual, jadi link http atau
    harga ngawur dari API ga bisa masuk
    """
    external_id = str(row["id"])
    if not external_id or len(external_id) > 50:
        return None
    model = form_class._meta.model
    instance = model.objects.filter(external_id=external_id).first()
    form = form_class(row, instance=instance or model(external_id=external_id))
    if not form.is_valid():
        return None
    obj = form.save(commit=False)
    for field, value in extra.items():
        setattr(obj, field, value)
    obj.save()
    return obj


@transaction.atomic
def upsert_parts(data):
    """Upsert semua suku cadang dari API, aman dijalankan berulang.

    Baris yang isinya ga valid di-skip dan dihitung, tapi kalau strukturnya
    rusak semuanya di-rollback. Data manual (tanpa external_id) ga disentuh
    """
    counts = {"parts": 0, "sources": 0, "skipped": 0}
    try:
        rows = data["parts"]
        slugs = {item["slug"] for row in rows for item in row["compatible_devices"]}
        devices = {d.slug: d for d in get_device_qs().filter(slug__in=slugs)}
        for row in rows:
            part = _save(SparePartForm, row)
            if part is None:
                counts["skipped"] += 1
                continue
            counts["parts"] += 1
            for item in row["compatible_devices"]:
                device = devices.get(item["slug"])
                if device is None:
                    counts["skipped"] += 1
                    continue
                PartCompatibility.objects.update_or_create(
                    part=part, device=device, defaults={"note": (item.get("note") or "")[:200]}
                )
            for item in row["sources"]:
                saved = _save(ApiSourceForm, item, part=part)
                counts["sources" if saved else "skipped"] += 1
    except (AttributeError, KeyError, TypeError) as exc:
        cache.delete(CACHE_KEY)  # biar data rusak ga nyangkut sejam di cache
        raise SyncFailure("Format data Mock API tidak sesuai.") from exc
    return counts
