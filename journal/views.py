from datetime import date

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from guides.selectors import visible_guides

from .formatting import kg, rupiah_short, short_date
from .forms import RepairLogForm, StatusFilterForm
from .impact import impact_basis, log_device
from .models import RepairLog
from .permissions import can_use_journal
from .selectors import (
    logs_for,
    site_impact_totals,
    status_counts,
    user_impact_summary,
)

Status = RepairLog.Status
PAGE_SIZE = 12


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


def build_tiles(succeeded, waste, cost, total=None):
    tiles = [
        {
            "key": "succeeded",
            "icon": "core/icons/circle-check-success.svg",
            "tone": "success",
            "value": str(succeeded),
            "label": "perbaikan berhasil",
        },
        {
            "key": "waste",
            "icon": "journal/icons/leaf-success.svg",
            "tone": "success",
            "value": kg(waste),
            "label": "limbah elektronik terhindar",
        },
        {
            "key": "cost",
            "icon": "journal/icons/wallet-blue.svg",
            "tone": "blue",
            "value": rupiah_short(cost),
            "label": "biaya ganti baru yang dihemat",
        },
    ]
    if total is not None:
        tiles.append(
            {
                "key": "total",
                "icon": "core/icons/notebook-pen-muted.svg",
                "tone": "muted",
                "value": str(total),
                "label": "total catatan",
            }
        )
    return tiles


def user_tiles(user, counts):
    summary = user_impact_summary(user)
    return build_tiles(
        counts["succeeded"],
        summary["waste_avoided_kg"],
        summary["cost_avoided"],
        counts["all"],
    )


def build_tabs(counts, active):
    tabs = [{"value": "", "key": "all", "label": "Semua"}]
    tabs += [{"value": v, "key": v, "label": label} for v, label in Status.choices]
    for tab in tabs:
        tab["count"] = counts[tab["key"]]
        tab["active"] = tab["value"] == active
    return tabs


def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@require_http_methods(["GET"])
def journal_list(request):
    if not can_use_journal(request.user):
        # Visitor hanya boleh melihat angka agregat seluruh situs.
        site = site_impact_totals()
        tiles = build_tiles(site["repairs"], site["waste_avoided_kg"], site["cost_avoided"])
        return render(request, "journal/list.html", {"visitor": True, "tiles": tiles})
    filters = StatusFilterForm(request.GET)
    status = filters.cleaned_data["status"] if filters.is_valid() else ""
    logs = logs_for(request.user)
    if status:
        logs = logs.filter(status=status)
    counts = status_counts(request.user)
    context = {
        "visitor": False,
        "page": Paginator(logs, PAGE_SIZE).get_page(request.GET.get("page")),
        "status": status,
        "counts": counts,
        "total": counts["all"],
        "tabs": build_tabs(counts, status),
        "tiles": user_tiles(request.user, counts),
        "statuses": Status.choices,
    }
    if is_ajax(request):
        return render(request, "journal/_list_results.html", context)
    return render(request, "journal/list.html", context)


def detail_context(log):
    device = log_device(log)
    impact = getattr(log, "impact", None)
    return {
        "log": log,
        "device": device,
        "impact": impact,
        "basis": impact_basis(device) if impact else None,
    }


@require_http_methods(["GET"])
def journal_detail(request, pk):
    if not can_use_journal(request.user):
        return denied(request)
    log = get_object_or_404(logs_for(request.user), pk=pk)
    return render(request, "journal/detail.html", detail_context(log))


def saved_message(log):
    text = "Catatan tersimpan."
    impact = getattr(log, "impact", None)
    if impact:
        text += f" Kamu baru saja menyelamatkan {kg(impact.waste_avoided_kg)} limbah!"
    return text


def editor(request, log=None, initial=None, from_guide=None):
    form = RepairLogForm(
        request.POST or None, instance=log, user=request.user, initial=initial
    )
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, saved_message(obj))
        return redirect("journal:detail", pk=obj.pk)
    return render(
        request,
        "journal/form.html",
        {
            "form": form,
            "editing": log is not None,
            "log": log,
            "from_guide": from_guide,
        },
        status=400 if request.method == "POST" else 200,
    )


def guide_from_query(request):
    slug = request.GET.get("guide", "")
    if not slug:
        return None
    return visible_guides(request.user).filter(slug=slug).select_related("device").first()


@require_http_methods(["GET", "POST"])
def journal_create(request):
    if not can_use_journal(request.user):
        return denied(request)
    guide = guide_from_query(request)
    initial = {"repaired_at": timezone.localdate()}
    if guide:
        initial.update(
            guide=guide.pk,
            device=guide.device_id,
            title=f"Perbaikan: {guide.title}"[:120],
            status=Status.IN_PROGRESS,
        )
    return editor(request, initial=initial, from_guide=guide)


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
        messages.success(request, "Catatan dihapus.")
        return redirect("journal:list")
    return render(request, "journal/confirm_delete.html", {"log": log})


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
    counts = status_counts(request.user)
    impact = serialize_impact(log)
    return JsonResponse(
        {
            "id": log.pk,
            "status": log.status,
            "status_label": log.get_status_display(),
            "badge_html": render_to_string(
                "journal/_status_badge.html",
                {"status": log.status, "label": log.get_status_display()},
            ),
            "impact_html": render_to_string(
                "journal/_impact_box.html", detail_context(log)
            ),
            "repaired_at": short_date(log.repaired_at),
            "card_impact": f"{kg(impact['waste_avoided_kg'])} limbah terhindar" if impact else "",
            "impact": impact,
            "summary": serialize_summary(user_impact_summary(request.user)),
            "tiles": {t["key"]: t["value"] for t in user_tiles(request.user, counts)},
            "counts": counts,
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
