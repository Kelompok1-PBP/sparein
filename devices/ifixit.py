import requests

from devices.models import Device, DeviceCategory

BASE = "https://www.ifixit.com/api/2.0"


def fetch_family(title):
    """Raw JSON wiki iFixit buat satu family device."""
    resp = requests.get(f"{BASE}/wikis/CATEGORY/{title}", timeout=15)
    resp.raise_for_status()
    return resp.json()


def upsert_family(family, brand):
    """Upsert family + children by ifixit_wikiid jadi seed ulang ga duplikat."""
    parent = None
    if family.get("ancestors"):
        parent, _ = DeviceCategory.objects.get_or_create(
            name=family["ancestors"][0]["display_title"]
        )
    category, _ = DeviceCategory.objects.get_or_create(
        name=family["display_title"], defaults={"parent": parent}
    )
    children = family.get("children", [])
    for child in children:
        Device.objects.update_or_create(
            ifixit_wikiid=child["wikiid"],
            defaults={
                "name": child["display_title"],
                "category": category,
                "brand": brand,
                "summary": child.get("summary") or "",
                "image_url": (child.get("image") or {}).get("standard", ""),
            },
        )
    return len(children)
