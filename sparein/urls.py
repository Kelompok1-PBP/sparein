from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from devices.api import DeviceViewSet
from guides.views import guide_api
from journal.views import journal_summary_api

router = DefaultRouter()
router.register("devices", DeviceViewSet, basename="device")

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("guides/", include("guides.urls")),
    path("journal/", include("journal.urls")),
    path("api/guides/", guide_api, name="guide-api"),
    path("api/journal/summary/", journal_summary_api, name="journal-summary-api"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("devices.urls")),
    path("", include("diagnostics.urls")),
    path("", include("parts.urls")),
    path("", include("core.urls")),
]
