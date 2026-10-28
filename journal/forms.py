from django import forms
from django.core.validators import MaxLengthValidator
from django.templatetags.static import static
from django.utils import timezone

from devices.selectors import get_device_qs
from guides.selectors import visible_guides

from .models import RepairLog

TITLE_MAX = 120
NOTES_MAX = 2000

STATUS_ICONS = {
    RepairLog.Status.PLANNED: "journal/icons/calendar-muted.svg",
    RepairLog.Status.IN_PROGRESS: "journal/icons/wrench-blue.svg",
    RepairLog.Status.SUCCEEDED: "core/icons/circle-check-success.svg",
    RepairLog.Status.FAILED: "journal/icons/circle-x-danger.svg",
}


class StatusCards(forms.RadioSelect):
    template_name = "journal/widgets/status_cards.html"
    option_template_name = "journal/widgets/status_card_option.html"

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        icon = STATUS_ICONS.get(option["value"])
        option["icon"] = static(icon) if icon else ""
        return option


class GuideSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-device"] = instance.device_id
        return option


class RepairLogForm(forms.ModelForm):
    class Meta:
        model = RepairLog
        fields = [
            "title",
            "status",
            "guide",
            "device",
            "repaired_at",
            "cost_spent",
            "notes",
        ]
        labels = {
            "title": "Judul",
            "status": "Status",
            "guide": "Panduan yang dipakai",
            "device": "Perangkat",
            "repaired_at": "Tanggal perbaikan",
            "cost_spent": "Biaya yang dikeluarkan",
            "notes": "Catatan",
        }
        help_texts = {
            "title": "Contoh: Ganti baterai HP adik.",
            "guide": "Kosongkan kalau tidak pakai panduan Sparein.",
            "device": "Terisi otomatis dari panduan.",
            "cost_spent": "Total beli suku cadang dan alat. Isi 0 kalau gratis.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"maxlength": TITLE_MAX}),
            "status": StatusCards,
            "guide": GuideSelect,
            "repaired_at": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "cost_spent": forms.NumberInput(attrs={"min": 0, "inputmode": "numeric"}),
            "notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": NOTES_MAX,
                    "placeholder": "Apa yang berhasil, apa yang susah, tips buat diri sendiri nanti.",
                }
            ),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs()
        # Panduan draf milik orang lain tidak boleh bisa dipilih.
        self.fields["guide"].queryset = visible_guides(user)
        self.fields["device"].empty_label = "Pilih perangkat"
        self.fields["guide"].empty_label = "Tanpa panduan"
        self.fields["repaired_at"].required = True
        for name, field in self.fields.items():
            if name != "status":
                field.widget.attrs.setdefault("class", "input")
        self._set_messages()

    def _set_messages(self):
        fields = self.fields
        fields["title"].error_messages["required"] = "Judul wajib diisi."
        fields["title"].validators.append(
            MaxLengthValidator(TITLE_MAX, "Judul maksimal 120 karakter.")
        )
        fields["status"].error_messages["required"] = "Pilih salah satu status."
        fields["status"].error_messages["invalid_choice"] = "Pilih salah satu status."
        fields["guide"].error_messages["invalid_choice"] = "Panduan tidak ditemukan."
        fields["device"].error_messages["invalid_choice"] = "Perangkat tidak ditemukan."
        fields["repaired_at"].error_messages["required"] = "Tanggal perbaikan wajib diisi."
        fields["repaired_at"].error_messages["invalid"] = "Format tanggal tidak valid."
        fields["cost_spent"].error_messages["required"] = "Isi biaya, atau 0 kalau gratis."
        fields["cost_spent"].error_messages["invalid"] = "Biaya harus berupa angka."
        fields["cost_spent"].error_messages["min_value"] = "Biaya tidak bisa minus."
        for validator in fields["cost_spent"].validators:
            if getattr(validator, "code", "") == "min_value":
                validator.message = "Biaya tidak bisa minus."
        fields["notes"].validators.append(
            MaxLengthValidator(NOTES_MAX, "Catatan maksimal 2000 karakter.")
        )

    def clean(self):
        data = super().clean()
        device, guide = data.get("device"), data.get("guide")
        if not device and not guide and "device" not in self.errors:
            self.add_error("device", "Isi panduan atau perangkat biar dampaknya bisa dihitung.")
        elif device and guide and guide.device_id != device.pk:
            self.add_error("guide", "Panduan ini untuk perangkat yang berbeda.")
        repaired_at = data.get("repaired_at")
        if (
            data.get("status") == RepairLog.Status.SUCCEEDED
            and repaired_at
            and repaired_at > timezone.localdate()
        ):
            self.add_error(
                "repaired_at", "Tanggal perbaikan yang berhasil tidak bisa di masa depan."
            )
        return data


class StatusFilterForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Semua status"), *RepairLog.Status.choices],
        label="Status",
        widget=forms.Select(attrs={"class": "input"}),
    )
