from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from core.permissions import is_admin, is_contributor


def home(request):
    return render(request, "core/home.html")


def register(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        login(request, form.save())
        return redirect("core:home")
    return render(request, "core/register.html", {"form": form})


@login_required
def profile(request):
    role = "admin" if is_admin(request.user) else "contributor" if is_contributor(request.user) else "member"
    return render(request, "core/profile.html", {"role": role})
