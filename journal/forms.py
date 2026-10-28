from datetime import date

from django import forms

from devices.selectors import get_device_qs  # daftar perangkat
from guides.selectors import visible_guides  # panduan yang boleh dilihat user

from .models import RepairLog


class RepairLogForm(forms.ModelForm):
    class Meta:
        model = RepairLog
        fields = [
            "title",  
            "device", 
            "guide",  
            "status", 
            "cost_spent",  
            "repaired_at", 
            "notes",       
        ]
        labels = {
            "title": "Judul perbaikan",
            "device": "Perangkat",
            "guide": "Panduan yang diikuti",
            "status": "Status",
            "cost_spent": "Biaya yang dikeluarkan (Rp)",
            "repaired_at": "Tanggal perbaikan",
            "notes": "Catatan",
        }
        widgets = { # cara field digambar menjadi HTML
            "repaired_at": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user, **kwargs): # penyesuaikan form untuk user yang sedang membuka
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs()
        # Panduan draf milik orang lain tidak boleh bisa dipilih, jadi keseluruhan ini intinya menentukan pilihan apa yang boleh muncul dan boleh diterima 
        self.fields["guide"].queryset = visible_guides(user)
        self.fields["device"].empty_label = "Pilih perangkat (opsional)"
        self.fields["guide"].empty_label = "Tanpa panduan"
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")

    def clean(self):
        data = super().clean()
        device, guide = data.get("device"), data.get("guide")
        if device and guide and guide.device_id != device.pk:
            self.add_error("guide", "Panduan ini untuk perangkat yang berbeda.")
        if (
            data.get("status") in (RepairLog.Status.SUCCEEDED, RepairLog.Status.FAILED)
            and not data.get("repaired_at")
        ):
            data["repaired_at"] = date.today()
        return data


class StatusFilterForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[("", "Semua status"), *RepairLog.Status.choices],
        label="Status",
        widget=forms.Select(attrs={"class": "input"}),
    )
