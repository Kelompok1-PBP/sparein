from django.contrib import admin

from .models import CategoryImpactProfile, ImpactEstimate, RepairLog


@admin.register(CategoryImpactProfile)
class CategoryImpactProfileAdmin(admin.ModelAdmin):
    list_display = ("category", "avg_mass_kg", "replacement_cost")


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "repaired_at")
    list_filter = ("status",)
    search_fields = ("title", "user__username")


@admin.register(ImpactEstimate)
class ImpactEstimateAdmin(admin.ModelAdmin):
    list_display = ("log", "waste_avoided_kg", "cost_avoided", "computed_at")
