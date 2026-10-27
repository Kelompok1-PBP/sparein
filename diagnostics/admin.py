from django.contrib import admin

from diagnostics.models import Cause, DiagnosisSession, Symptom


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ("title", "device", "severity")
    list_filter = ("severity",)
    search_fields = ("title", "device__name")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Cause)
class CauseAdmin(admin.ModelAdmin):
    list_display = ("title", "device")
    search_fields = ("title", "device__name")
    filter_horizontal = ("symptoms",)


@admin.register(DiagnosisSession)
class DiagnosisSessionAdmin(admin.ModelAdmin):
    list_display = ("device", "user", "created_at")
