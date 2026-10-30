from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from core.permissions import is_admin, is_contributor
from core.selectors import latest_guides, popular_devices, top_categories
from diagnostics.selectors import get_sessions_for_user
from journal.selectors import logs_for, site_impact_totals

# Kata kunci nama kategori (atau induknya) ke nama ikon di static/core/icons. Urutan penting.
CATEGORY_ICONS = (
    ("tab", "tablet"),
    ("phone", "smartphone"),
    ("laptop", "laptop"),
    ("mac", "laptop"),
    ("game", "gamepad"),
    ("switch", "gamepad"),
    ("audio", "headphones"),
    ("headphone", "headphones"),
    ("camera", "camera"),
)


def _category_icon(category):
    names = [category.name.lower()]
    if category.parent:
        names.append(category.parent.name.lower())
    for name in names:
        for keyword, icon in CATEGORY_ICONS:
            if keyword in name:
                return icon
    return "package"


def home(request):
    categories = list(top_categories())
    for category in categories:
        category.icon = _category_icon(category)
    return render(request, "core/home.html", {
        "popular": popular_devices(),
        "categories": categories,
        "guides": latest_guides(),
        "impact": site_impact_totals(),
    })


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("core:home")
    return render(request, "core/register.html", {"form": form})


@login_required
def profile(request):
    role = "admin" if is_admin(request.user) else "contributor" if is_contributor(request.user) else "member"
    return render(request, "core/profile.html", {
        "role": role,
        "journal_total": logs_for(request.user).count(),
        "session_total": get_sessions_for_user(request.user).count(),
    })
