from django.shortcuts import get_object_or_404

from diagnostics.models import Symptom


def get_symptoms_for_device(device_id):
    """Gejala milik satu perangkat, dipakai modul lain."""
    return Symptom.objects.filter(device_id=device_id)


def get_symptom_qs(*, device=None, severity=None):
    """Filter kosong di-skip. device berupa slug perangkat."""
    qs = Symptom.objects.select_related("device", "created_by")
    if device:
        qs = qs.filter(device__slug=device)
    if severity:
        qs = qs.filter(severity=severity)
    return qs


def get_symptom_or_404(slug):
    return get_object_or_404(get_symptom_qs(), slug=slug)
