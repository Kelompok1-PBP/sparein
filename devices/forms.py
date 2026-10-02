from django import forms
from django.utils import timezone

from devices.models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            "name", "category", "brand", "release_year",
            "image_url", "summary", "repairability_score",
        ]

    def clean_release_year(self):
        year = self.cleaned_data["release_year"]
        if year and not 1970 <= year <= timezone.now().year + 1:
            raise forms.ValidationError("Tahun rilis tidak masuk akal.")
        return year
