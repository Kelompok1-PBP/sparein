from django.contrib import admin
from django.urls import include, path

from guides.views import guide_api
from journal.views import journal_summary_api

urlpatterns = [
    path("guides/", include("guides.urls")),
    path("journal/", include("journal.urls")),
    path("api/guides/", guide_api, name="guide-api"),
    path("api/journal/summary/", journal_summary_api, name="journal-summary-api"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("devices.urls")),
    path("", include("core.urls")),
]
