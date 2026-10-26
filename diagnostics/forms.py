from django import forms

from devices.selectors import get_device_qs
from diagnostics.models import Symptom

SEVERITY_HINTS = {
    "low": "Masih bisa dipakai normal.",
    "medium": "Mengganggu, tapi masih bisa dipakai.",
    "high": "Tidak bisa dipakai atau berbahaya.",
}


class SeverityRadio(forms.RadioSelect):
    """Radio keparahan yang tampil sebagai kartu: judul plus penjelasan singkat."""

    template_name = "diagnostics/widgets/severity.html"
    option_template_name = "diagnostics/widgets/severity_option.html"

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option["hint"] = SEVERITY_HINTS.get(option["value"], "")
        return option


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
            "severity": SeverityRadio,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("device", "title", "description"):
            self.fields[name].widget.attrs["class"] = "input"
        self.fields["device"].queryset = get_device_qs()
        self.fields["description"].required = True
        self.fields["severity"].initial = Symptom.Severity.MEDIUM

    def add_error(self, field, error):
        super().add_error(field, error)
        if field in self.fields:
            self.fields[field].widget.attrs["aria-invalid"] = "true"
