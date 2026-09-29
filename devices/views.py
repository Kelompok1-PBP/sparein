def _filters(request):
    return {k: request.GET.get(k, "").strip() for k in ("q", "category", "brand")}
