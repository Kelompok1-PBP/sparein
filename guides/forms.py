from django import forms
from django.forms import inlineformset_factory

from core.forms import InputStyleMixin
from devices.selectors import get_device_qs

from .models import GuideStep, RepairGuide, SafetyWarning


class GuideForm(InputStyleMixin, forms.ModelForm):
    class Meta:
        model = RepairGuide
        fields = [
            "device",
            "title",
            "summary",
            "difficulty",
            "time_required_minutes",
            "tools",
            "published",
        ]
        labels = {
            "device": "Perangkat",
            "title": "Judul panduan",
            "summary": "Ringkasan",
            "difficulty": "Tingkat kesulitan",
            "time_required_minutes": "Perkiraan waktu",
            "tools": "Alat yang dibutuhkan",
            "published": "Terbitkan sekarang",
        }
        help_texts = {
            "title": "Mulai dengan kata kerja.",
            "time_required_minutes": "Dalam menit.",
            "tools": "Satu alat per baris.",
        }
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3, "placeholder": "Ceritakan singkat apa yang dikerjakan."}),
            "tools": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs()


class StepForm(InputStyleMixin, forms.ModelForm):
    class Meta:
        model = GuideStep
        fields = ["order", "title", "detail", "image_url"]
        labels = {"title": "Judul langkah", "detail": "Penjelasan", "image_url": "URL gambar"}
        widgets = {"order": forms.HiddenInput, "detail": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Baris baru tanpa JS tetap dapat urutan: nomor barisnya
        index = (self.prefix or "").rsplit("-", 1)[-1]
        if index.isdigit() and not self.instance.pk:
            self.fields["order"].initial = int(index) + 1


class WarningForm(InputStyleMixin, forms.ModelForm):
    class Meta:
        model = SafetyWarning
        fields = ["level", "message"]
        labels = {"level": "Level", "message": "Pesan"}
        widgets = {"message": forms.Textarea(attrs={"rows": 3})}


StepFormSet = inlineformset_factory(
    RepairGuide,
    GuideStep,
    form=StepForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=100,
    validate_max=True,
)
WarningFormSet = inlineformset_factory(
    RepairGuide,
    SafetyWarning,
    form=WarningForm,
    extra=1,
    can_delete=True,
    max_num=50,
    validate_max=True,
)


class FilterForm(forms.Form):
    device = forms.IntegerField(required=False, min_value=1)
    difficulty = forms.ChoiceField(
        required=False, choices=[("", "Semua kesulitan")] + RepairGuide.DIFFICULTIES
    )
    max_time = forms.IntegerField(required=False, min_value=1)


class ImportGuideForm(forms.Form):
    guide_id = forms.IntegerField(min_value=1, label="ID panduan iFixit")
    device = forms.ModelChoiceField(queryset=None, label="Perangkat yang sesuai")
    minutes = forms.IntegerField(
        min_value=1,
        required=False,
        label="Durasi (menit), jika tidak tersedia di sumber",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs()
