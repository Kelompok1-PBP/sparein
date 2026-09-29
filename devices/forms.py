from django import forms

from devices.models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            "name", "category", "brand", "release_year",
            "image_url", "summary", "repairability_score",
        ]
