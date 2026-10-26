from django.contrib import admin

from parts.models import PartCompatibility, PartSource, SparePart


class PartCompatibilityInline(admin.TabularInline):
    model = PartCompatibility
    autocomplete_fields = ("device",)
    extra = 0


class PartSourceInline(admin.TabularInline):
    model = PartSource
    extra = 0


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "part_number", "created_by")
    list_filter = ("category",)
    search_fields = ("name", "part_number")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (PartCompatibilityInline, PartSourceInline)
