from rest_framework import serializers

from .impact import log_device
from .models import ImpactEstimate, RepairLog


class ImpactSerializer(serializers.ModelSerializer):
    # float, bukan string desimal bawaan DRF, supaya sama dengan `serialize_impact` di views
    waste_avoided_kg = serializers.FloatField()

    class Meta:
        model = ImpactEstimate
        fields = ["waste_avoided_kg", "cost_avoided"]


class RepairLogSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    device = serializers.SerializerMethodField()
    device_name = serializers.SerializerMethodField()
    guide = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    guide_title = serializers.CharField(source="guide.title", read_only=True, default=None)
    impact = ImpactSerializer(read_only=True, allow_null=True)

    class Meta:
        model = RepairLog
        fields = [
            "id", "title", "status", "status_label", "cost_spent", "notes", "repaired_at",
            "device", "device_name", "guide", "guide_title", "impact",
        ]

    def get_device(self, log):
        device = log_device(log)
        return device.slug if device else None

    def get_device_name(self, log):
        device = log_device(log)
        return device.name if device else None
