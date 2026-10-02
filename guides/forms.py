from django import forms
from django.forms import inlineformset_factory

from devices.selectors import get_device_qs

from .models import GuideStep, RepairGuide, SafetyWarning


class GuideForm(forms.ModelForm):
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
            "difficulty": "Kesulitan",
            "time_required_minutes": "Durasi (menit)",
            "tools": "Alat yang dibutuhkan",
            "published": "Terbitkan panduan",
        }
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "tools": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs()


StepFormSet = inlineformset_factory(
    RepairGuide,
    GuideStep,
    fields=["order", "title", "detail", "image_url"],
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=100,
    validate_max=True,
    widgets={"detail": forms.Textarea(attrs={"rows": 3})},
)
WarningFormSet = inlineformset_factory(
    RepairGuide,
    SafetyWarning,
    fields=["level", "message"],
    extra=1,
    can_delete=True,
    max_num=50,
    validate_max=True,
    widgets={"message": forms.Textarea(attrs={"rows": 2})},
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
