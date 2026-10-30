from django.db.models import Q
from django.shortcuts import get_object_or_404

from core.permissions import is_admin

from .models import RepairGuide


def get_guide_qs(*, device=None, difficulty=None, max_time=None):
    qs = RepairGuide.objects.select_related("device", "author")
    if device:
        qs = qs.filter(device_id=device)
    if difficulty:
        qs = qs.filter(difficulty=difficulty)
    if max_time:
        qs = qs.filter(time_required_minutes__lte=max_time)
    return qs


def get_guide_or_404(slug: str) -> RepairGuide:
    return get_object_or_404(get_guide_qs(), slug=slug)


def visible_guides(user):
    qs = get_guide_qs()
    if is_admin(user):
        return qs
    if user.is_authenticated:
        return qs.filter(Q(published=True) | Q(author=user))
    return qs.filter(published=True)
