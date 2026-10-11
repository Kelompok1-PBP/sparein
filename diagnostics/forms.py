from django import forms

from devices.selectors import get_device_qs
from diagnostics.models import Symptom

SEVERITY_HINTS = {
    "low": "Masih bisa dipakai normal.",
    "medium": "Mengganggu, tapi masih bisa dipakai.",
    "high": "Tidak bisa dipakai atau berbahaya.",
}


class SymptomForm(forms.ModelForm):
    class Meta:
        model = Symptom
        fields = ["device", "title", "description", "severity"]
        labels = {
            "device": "Perangkat",
            "title": "Judul gejala",
            "description": "Deskripsi",
            "severity": "Tingkat keparahan",
        }
        help_texts = {
            "title": "Tulis dari sudut pandang pengguna, contoh Baterai cepat habis.",
            "description": "Kapan gejalanya muncul? Seberapa sering?",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "severity": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs()
        self.fields["description"].required = True
        self.fields["severity"].choices = [
            (value, f"{label}. {SEVERITY_HINTS[value]}")
            for value, label in Symptom.Severity.choices
        ]
        self.fields["severity"].initial = Symptom.Severity.MEDIUM
