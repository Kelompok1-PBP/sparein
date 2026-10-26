from datetime import date

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import RepairLogForm, StatusFilterForm
from .models import RepairLog
from .permissions import can_use_journal
from .selectors import logs_for, site_impact_totals, user_impact_summary

Status = RepairLog.Status


def wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def denied(request):
    if wants_json(request) or request.headers.get("X-Requested-With"):
        return JsonResponse({"error": "Akses ditolak."}, status=403)
    return redirect_to_login(request.get_full_path())


def serialize_impact(log):
    impact = getattr(log, "impact", None)
    if impact is None:
        return None
    return {
        "waste_avoided_kg": float(impact.waste_avoided_kg),
        "cost_avoided": impact.cost_avoided,
    }


def serialize_summary(summary):
    return {
        "repairs": summary["repairs"],
        "waste_avoided_kg": float(summary["waste_avoided_kg"]),
        "cost_avoided": summary["cost_avoided"],
    }


@require_http_methods(["GET"])
def journal_list(request):
    site = site_impact_totals()
    if not can_use_journal(request.user):
        return render(request, "journal/list.html", {"visitor": True, "site": site})
    filters = StatusFilterForm(request.GET)
    logs = logs_for(request.user)
    if filters.is_valid() and filters.cleaned_data["status"]:
        logs = logs.filter(status=filters.cleaned_data["status"])
    return render(
        request,
        "journal/list.html",
        {
            "visitor": False,
            "logs": logs[:100],
            "filters": filters,
            "summary": user_impact_summary(request.user),
            "site": site,
            "statuses": Status.choices,
        },
    )


@require_http_methods(["GET"])
def journal_detail(request, pk):
    if not can_use_journal(request.user):
        return denied(request)
    log = get_object_or_404(logs_for(request.user), pk=pk)
    return render(request, "journal/detail.html", {"log": log})


def editor(request, log=None):
    form = RepairLogForm(request.POST or None, instance=log, user=request.user)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, "Catatan perbaikan berhasil disimpan.")
        return redirect("journal:detail", pk=obj.pk)
    return render(
        request,
        "journal/form.html",
        {"form": form, "editing": log is not None},
        status=400 if request.method == "POST" else 200,
    )


@require_http_methods(["GET", "POST"])
def journal_create(request):
    if not can_use_journal(request.user):
        return denied(request)
    return editor(request)


@require_http_methods(["GET", "POST"])
def journal_edit(request, pk):
    if not can_use_journal(request.user):
        return denied(request)
    log = get_object_or_404(logs_for(request.user), pk=pk)
    return editor(request, log)


@require_http_methods(["GET", "POST"])
def journal_delete(request, pk):
    if not can_use_journal(request.user):
        return denied(request)
    log = get_object_or_404(logs_for(request.user), pk=pk)
    if request.method == "POST":
        log.delete()
        messages.success(request, "Catatan perbaikan berhasil dihapus.")
        return redirect("journal:list")
    return render(request, "journal/delete.html", {"log": log})


@require_http_methods(["POST"])
def journal_status(request, pk):
    if not can_use_journal(request.user):
        return denied(request)
    log = get_object_or_404(logs_for(request.user), pk=pk)
    status = request.POST.get("status", "")
    if status not in Status.values:
        return JsonResponse({"errors": {"status": ["Status tidak valid."]}}, status=400)
    log.status = status
    if status in (Status.SUCCEEDED, Status.FAILED) and not log.repaired_at:
        log.repaired_at = date.today()
    log.save()
    log = get_object_or_404(logs_for(request.user), pk=pk)
    return JsonResponse(
        {
            "id": log.pk,
            "status": log.status,
            "status_label": log.get_status_display(),
            "impact": serialize_impact(log),
            "summary": serialize_summary(user_impact_summary(request.user)),
            "url": reverse("journal:detail", args=[log.pk]),
        }
    )


@require_http_methods(["GET"])
def journal_summary_api(request):
    if not can_use_journal(request.user):
        return JsonResponse({"error": "Akses ditolak."}, status=403)
    by_status = {value: 0 for value in Status.values}
    for log in logs_for(request.user):
        by_status[log.status] += 1
    return JsonResponse(
        {
            "summary": serialize_summary(user_impact_summary(request.user)),
            "site": serialize_summary(site_impact_totals()),
            "by_status": by_status,
        }
    )
