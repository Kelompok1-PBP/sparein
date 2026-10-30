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
        labels = {
            "name": "Nama perangkat",
            "category": "Kategori",
            "brand": "Merek",
            "release_year": "Tahun rilis",
            "image_url": "URL gambar",
            "summary": "Ringkasan",
            "repairability_score": "Skor kemudahan perbaikan",
        }
        help_texts = {
            "name": "Tulis lengkap dengan modelnya.",
            "brand": "Contoh Apple, Samsung, Miyako.",
            "release_year": "Antara 1970 sampai tahun depan.",
            "image_url": "Tempel link gambar.",
            "repairability_score": "0 artinya susah banget, 10 artinya gampang banget.",
        }
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4, "placeholder": "Jelaskan singkat perangkat ini."}),
        }

    def clean_release_year(self):
        year = self.cleaned_data["release_year"]
        if year and not 1970 <= year <= timezone.now().year + 1:
            raise forms.ValidationError("Tahun rilis tidak masuk akal.")
        return year
