from uuid import uuid4

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from .forms import FilterForm, GuideForm, StepFormSet, WarningFormSet
from .models import GuideStep
from .permissions import can_create, can_delete, can_edit
from .selectors import visible_guides


def wants_json(request):
    return "application/json" in request.headers.get("Accept", "")


def denied(request):
    return (
        JsonResponse({"error": "Akses ditolak."}, status=403)
        if wants_json(request)
        else HttpResponseForbidden("Akses ditolak.")
    )


def filtered(request):
    form = FilterForm(request.GET)
    qs = visible_guides(request.user)
    if not form.is_valid():
        return qs.none(), form
    for name, lookup in [
        ("device", "device_id"),
        ("difficulty", "difficulty"),
        ("max_time", "time_required_minutes__lte"),
    ]:
        if form.cleaned_data[name]:
            qs = qs.filter(**{lookup: form.cleaned_data[name]})
    return qs, form


@require_http_methods(["GET"])
def guide_list(request):
    qs, filters = filtered(request)
    return render(
        request,
        "guides/list.html",
        {
            "guides": qs[:100],
            "filters": filters,
            "can_create": can_create(request.user),
            "devices": GuideForm().fields["device"].queryset,
        },
    )


@require_http_methods(["GET"])
def guide_api(request):
    qs, filters = filtered(request)
    if filters.errors:
        return JsonResponse({"errors": filters.errors.get_json_data()}, status=400)
    items = []
    for guide in qs.prefetch_related("warnings")[:100]:
        data = {
            "id": guide.pk,
            "title": guide.title,
            "slug": guide.slug,
            "summary": guide.summary,
            "device": guide.device_id,
            "device_name": str(guide.device),
            "difficulty": guide.difficulty,
            "time_required_minutes": guide.time_required_minutes,
            "url": reverse("guides:detail", args=[guide.slug]),
            "warnings": list(guide.warnings.values("level", "message")),
        }
        fields = ["order", "title", "image_url"]
        if request.user.is_authenticated:
            fields.append("detail")
        data["steps"] = list(guide.steps.values(*fields))
        items.append(data)
    return JsonResponse({"results": items, "limit": 100})


@require_http_methods(["GET"])
def guide_detail(request, slug):
    guide = get_object_or_404(visible_guides(request.user), slug=slug)
    fields = ["order", "title", "image_url"]
    if request.user.is_authenticated:
        fields.append("detail")
    return render(
        request,
        "guides/detail.html",
        {
            "guide": guide,
            "steps": guide.steps.values(*fields),
            "can_edit": can_edit(request.user, guide),
            "can_delete": can_delete(request.user, guide),
        },
    )


def editor(request, guide=None):
    form = GuideForm(request.POST or None, instance=guide)
    steps = StepFormSet(request.POST or None, instance=form.instance, prefix="steps")
    warnings = WarningFormSet(
        request.POST or None, instance=form.instance, prefix="warnings"
    )
    if request.method == "POST":
        valid = [form.is_valid(), steps.is_valid(), warnings.is_valid()]
        if all(valid):
            with transaction.atomic():
                obj = form.save(commit=False)
                if not obj.pk:
                    obj.author = request.user
                    obj.slug = (
                        (slugify(obj.title)[:180] or "panduan") + "-" + uuid4().hex[:10]
                    )
                obj.save()
                # Recreate owned child rows atomically so swapping step orders cannot violate uniqueness.
                obj.steps.all().delete()
                obj.warnings.all().delete()
                for fs, model in [(steps, GuideStep), (warnings, warnings.model)]:
                    for row in fs.forms:
                        if row.cleaned_data and not row.cleaned_data.get(
                            "DELETE", False
                        ):
                            fields = {
                                key: value
                                for key, value in row.cleaned_data.items()
                                if key not in {"id", "guide", "DELETE"}
                            }
                            model.objects.create(guide=obj, **fields)
            if wants_json(request):
                return JsonResponse(
                    {"id": obj.pk, "url": reverse("guides:detail", args=[obj.slug])},
                    status=200 if guide else 201,
                )
            messages.success(request, "Panduan berhasil disimpan.")
            return redirect("guides:detail", slug=obj.slug)
        if wants_json(request):
            return JsonResponse(
                {
                    "errors": {
                        "guide": form.errors,
                        "steps": steps.errors,
                        "step_errors": list(steps.non_form_errors()),
                        "warnings": warnings.errors,
                        "warning_errors": list(warnings.non_form_errors()),
                    }
                },
                status=400,
            )
    return render(
        request,
        "guides/form.html",
        {
            "form": form,
            "steps": steps,
            "warnings": warnings,
            "editing": guide is not None,
        },
        status=400 if request.method == "POST" else 200,
    )


@require_http_methods(["GET", "POST"])
def guide_create(request):
    if not can_create(request.user):
        return denied(request)
    return editor(request)


@require_http_methods(["GET", "POST"])
def guide_edit(request, slug):
    guide = get_object_or_404(visible_guides(request.user), slug=slug)
    if not can_edit(request.user, guide):
        return denied(request)
    return editor(request, guide)


@require_http_methods(["GET", "POST"])
def guide_delete(request, slug):
    guide = get_object_or_404(visible_guides(request.user), slug=slug)
    if not can_delete(request.user, guide):
        return denied(request)
    if request.method == "POST":
        guide.delete()
        if wants_json(request):
            return JsonResponse({"deleted": True})
        messages.success(request, "Panduan berhasil dihapus.")
        return redirect("guides:list")
    return render(request, "guides/delete.html", {"guide": guide})


@require_http_methods(["GET", "POST"])
def guide_import(request):
    from .forms import ImportGuideForm
    from .ifixit import ImportFailure, fetch_guide, import_guide

    if not can_create(request.user):
        return denied(request)
    form = ImportGuideForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            guide = import_guide(
                fetch_guide(form.cleaned_data["guide_id"]),
                device=form.cleaned_data["device"],
                author=request.user,
                minutes=form.cleaned_data["minutes"],
            )
        except ImportFailure as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request,
                "Diimpor sebagai draf. Periksa perangkat, langkah, peringatan, dan sumber sebelum menerbitkan.",
            )
            return redirect("guides:edit", slug=guide.slug)
    return render(
        request,
        "guides/import.html",
        {"form": form},
        status=400 if request.method == "POST" else 200,
    )
