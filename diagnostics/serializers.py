from rest_framework import serializers

from diagnostics.models import Symptom


class SymptomSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)
    severity_label = serializers.CharField(source="get_severity_display", read_only=True)

    class Meta:
        model = Symptom
        fields = [
            "id", "title", "slug", "description", "severity", "severity_label",
            "device", "device_name",
        ]


class DiagnosisResultSerializer(serializers.Serializer):
    """Satu baris hasil dari `rank_causes`. Bukan model, karena hasil tidak disimpan."""

    title = serializers.CharField(source="cause.title")
    likelihood = serializers.CharField()
    likelihood_label = serializers.CharField()
    note = serializers.CharField(allow_blank=True)
