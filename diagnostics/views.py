from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from core.permissions import is_admin, is_contributor
from devices.selectors import get_device_or_404, get_device_qs
from diagnostics.forms import SymptomForm
from diagnostics.selectors import (
    get_symptom_or_404,
    get_symptom_qs,
    get_symptoms_for_device,
)
from diagnostics.services import rank_causes


def _ticked(request):
    """Id gejala dari ?symptom=, nilai yang bukan angka dibuang."""
    return [int(v) for v in request.GET.getlist("symptom") if v.isdigit()]


def _can_edit(user, symptom):
    return is_admin(user) or (is_contributor(user) and symptom.created_by_id == user.id)


def _guides_url(device):
    return f"{reverse('guides:list')}?device={device.pk}"


def diagnose(request):
    slug = request.GET.get("device", "").strip()
    if not slug:
        return render(request, "diagnostics/diagnose.html", {"api_devices": reverse("devices:api")})
    device = get_device_or_404(slug)
    ticked = _ticked(request)
    results = rank_causes(device.pk, ticked)
    return render(request, "diagnostics/diagnose.html", {
        "device": device,
        "symptoms": get_symptoms_for_device(device.pk),
        "ticked": ticked,
        "results": results,
        "guides_url": _guides_url(device),
        "can_create": is_contributor(request.user),
        "api_diagnose": reverse("diagnostics:api-diagnose"),
    })


def symptom_detail(request, slug):
    symptom = get_symptom_or_404(slug)
    return render(request, "diagnostics/symptom_detail.html", {
        "symptom": symptom,
        "guides_url": _guides_url(symptom.device),
        "can_edit": _can_edit(request.user, symptom),
        "can_delete": is_admin(request.user),
    })


@login_required
def symptom_create(request):
    if not is_contributor(request.user):
        raise PermissionDenied
    initial = {"device": get_device_qs().filter(slug=request.GET.get("device", "")).first()}
    form = SymptomForm(request.POST or None, initial=initial)
    if form.is_valid():
        symptom = form.save(commit=False)
        symptom.created_by = request.user
        symptom.save()
        messages.success(request, "Gejala berhasil disimpan.")
        return redirect("diagnostics:detail", slug=symptom.slug)
    return render(request, "diagnostics/symptom_form.html", {"form": form})


@login_required
def symptom_edit(request, slug):
    symptom = get_symptom_or_404(slug)
    if not _can_edit(request.user, symptom):
        raise PermissionDenied
    form = SymptomForm(request.POST or None, instance=symptom)
    if form.is_valid():
        form.save()
        messages.success(request, "Gejala berhasil disimpan.")
        return redirect("diagnostics:detail", slug=symptom.slug)
    return render(request, "diagnostics/symptom_form.html", {"form": form})


@login_required
def symptom_delete(request, slug):
    symptom = get_symptom_or_404(slug)
    if not is_admin(request.user):
        raise PermissionDenied
    if request.method == "POST":
        symptom.delete()
        messages.success(request, "Gejala berhasil dihapus.")
        return redirect("diagnostics:list")
    return render(request, "diagnostics/confirm_delete.html", {"symptom": symptom})


def api_symptoms(request):
    qs = get_symptom_qs(
        device=request.GET.get("device", "").strip(),
        severity=request.GET.get("severity", "").strip(),
    )
    results = [
        {
            "id": s.pk,
            "title": s.title,
            "slug": s.slug,
            "description": s.description,
            "severity": s.severity,
            "device": s.device.slug,
            "url": reverse("diagnostics:detail", args=[s.slug]),
        }
        for s in qs
    ]
    return JsonResponse({"results": results})


def api_diagnose(request):
    """Hitung ranking tanpa menulis ke database, dipakai AJAX centang gejala."""
    device = get_device_or_404(request.GET.get("device", "").strip())
    results = [
        {
            "title": r["cause"].title,
            "likelihood": r["likelihood"],
            "likelihood_label": r["likelihood_label"],
            "note": r["note"],
        }
        for r in rank_causes(device.pk, _ticked(request))
    ]
    return JsonResponse({"count": len(results), "results": results, "guides_url": _guides_url(device)})
