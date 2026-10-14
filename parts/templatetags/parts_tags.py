from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def rupiah(value):
    """185000 jadi "Rp 185.000"."""
    if value in (None, ""):
        return ""
    return f"Rp {int(value):,}".replace(",", ".")


@register.filter
def days_ago(value):
    """Tanggal jadi "hari ini", "kemarin", atau "12 hari lalu"."""
    days = (timezone.localdate() - value).days
    if days <= 0:
        return "hari ini"
    if days == 1:
        return "kemarin"
    return f"{days} hari lalu"
