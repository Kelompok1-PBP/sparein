from django.contrib import admin

from devices.models import Device, DeviceCategory


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "release_year")
    list_filter = ("category", "brand")
    search_fields = ("name", "brand")
