"""Import on demand. Normal page views use the local database, never the API."""

import math
from html import unescape
from uuid import uuid4

import requests
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils.html import strip_tags
from django.utils.text import slugify

from .models import GuideStep, RepairGuide, SafetyWarning


class ImportFailure(ValueError):
    pass


def plain(value):
    return unescape(strip_tags(str(value or ""))).strip()


def fetch_guide(guide_id):
    key = f"ifixit-guide-{guide_id}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        response = requests.get(
            f"https://www.ifixit.com/api/2.0/guides/{int(guide_id)}", timeout=20
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ImportFailure(
            "iFixit tidak dapat diakses. Coba lagi nanti; panduan tersimpan tetap tersedia."
        ) from exc
    if not isinstance(data, dict) or data.get("guideid") != int(guide_id):
        raise ImportFailure("Respons iFixit tidak valid.")
    cache.set(key, data, 3600)
    return data


def safe_image(step):
    media = step.get("media") or {}
    images = media.get("data") if media.get("type") == "image" else []
    if not isinstance(images, list) or not images:
        return ""
    url = images[0].get("standard", "")
    try:
        URLValidator(schemes=["https"])(url)
    except ValidationError:
        return ""
    return url if len(url) <= 200 else ""


@transaction.atomic
def import_guide(data, *, device, author, minutes=None):
    guide_id = data.get("guideid")
    if not isinstance(guide_id, int) or guide_id <= 0:
        raise ImportFailure("ID panduan tidak valid.")
    if RepairGuide.objects.filter(ifixit_guideid=guide_id).exists():
        raise ImportFailure("Panduan ini sudah diimpor. Edit panduan yang sudah ada.")
    difficulty = data.get("difficulty")
    if difficulty not in dict(RepairGuide.DIFFICULTIES):
        raise ImportFailure("Tingkat kesulitan sumber belum didukung.")
    seconds = data.get("time_required_max") or data.get("time_required_min")
    if minutes is None and isinstance(seconds, (int, float)) and seconds > 0:
        minutes = math.ceil(seconds / 60)
    if not minutes:
        raise ImportFailure(
            "Sumber tidak punya durasi. Isi estimasi menit sebelum impor."
        )
    title = plain(data.get("title"))
    steps = data.get("steps")
    if not title or not isinstance(steps, list) or not steps or len(steps) > 100:
        raise ImportFailure(
            "Judul/langkah sumber kosong atau jumlah langkah melebihi 100."
        )
    guide = RepairGuide.objects.create(
        device=device,
        author=author,
        title=title[:200],
        slug=(slugify(title)[:180] or "panduan") + "-" + uuid4().hex[:10],
        summary=plain(data.get("summary") or data.get("introduction_rendered"))
        or title,
        difficulty=difficulty,
        time_required_minutes=minutes,
        tools="\n".join(plain(t.get("text")) for t in data.get("tools", [])),
        ifixit_guideid=guide_id,
        source_author=plain((data.get("author") or {}).get("username"))[:200],
        published=False,
    )
    SafetyWarning.objects.create(
        guide=guide,
        level="caution",
        message="Panduan dari iFixit. Cocokkan model perangkat dan baca sumber asli beserta semua peringatannya sebelum melakukan perbaikan.",
    )
    for index, step in enumerate(steps, 1):
        lines = step.get("lines") or []
        detail = "\n".join(
            plain(line.get("text_rendered") or line.get("text_raw")) for line in lines
        )
        if not detail:
            raise ImportFailure(
                f"Langkah {index} tidak memiliki teks; impor dibatalkan."
            )
        GuideStep.objects.create(
            guide=guide,
            order=index,
            title=plain(step.get("title") or f"Langkah {index}")[:200],
            detail=detail,
            image_url=safe_image(step),
        )
        for line in lines:
            if line.get("bullet") in {"caution", "warning", "note"}:
                SafetyWarning.objects.create(
                    guide=guide,
                    level="info" if line["bullet"] == "note" else "caution",
                    message=f"Langkah {index}: {plain(line.get('text_rendered') or line.get('text_raw'))}",
                )
    return guide
