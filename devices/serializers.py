from rest_framework import serializers

from devices.models import Device


class DeviceSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Device
        fields = [
            "name", "slug", "brand", "category", "category_name",
            "release_year", "image_url", "summary", "repairability_score",
        ]
