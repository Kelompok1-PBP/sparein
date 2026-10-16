from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, inlineformset_factory

from devices.selectors import get_device_qs
from parts.models import PartSource, SparePart

MAX_PRICE = 1_000_000_000


def _style(form):
    """Semua isian pakai class .input dari base.css."""
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "input")


class SparePartForm(forms.ModelForm):
    image_url = forms.URLField(label="URL gambar", required=False, assume_scheme="https")

    class Meta:
        model = SparePart
        fields = ["name", "part_number", "category", "description", "image_url"]
        labels = {
            "name": "Nama suku cadang",
            "part_number": "Nomor part",
            "category": "Kategori",
            "description": "Deskripsi",
        }
        help_texts = {
            "name": "Contoh Baterai iPhone 11.",
            "part_number": "Kode resmi dari pabrik kalau ada.",
        }
        widgets = {
            "part_number": forms.TextInput(attrs={"class": "input parts-mono"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [("", "Pilih kategori"), *SparePart.Category.choices]
        _style(self)


class CompatibilityForm(forms.Form):
    device = forms.ModelChoiceField(
        queryset=None,
        label="Perangkat",
        empty_label="Pilih perangkat",
        error_messages={"required": "Pilih perangkatnya."},
    )
    note = forms.CharField(
        label="Catatan", max_length=200, required=False, help_text="Contoh Cuma versi global."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = get_device_qs().order_by("name")
        _style(self)


class BaseCompatibilityFormSet(forms.BaseFormSet):
    default_error_messages = {"too_many_forms": "Maksimal 20 perangkat."}

    def clean(self):
        if any(self.errors):
            return
        seen = set()
        for form in self.forms:
            device = form.cleaned_data.get("device")
            if not device or self._should_delete_form(form):
                continue
            if device in seen:
                form.add_error("device", "Perangkat ini sudah ada di daftar.")
            seen.add(device)
        # cek minimal sendiri, validate_min bawaan dobel sama error "Pilih perangkatnya." di baris
        if not seen:
            raise ValidationError("Pilih minimal satu perangkat.", code="too_few_forms")

    def rows(self):
        """Baris yang diisi dan ga dicentang hapus."""
        return [
            {"device": f.cleaned_data["device"], "note": f.cleaned_data["note"]}
            for f in self.forms
            if f.cleaned_data.get("device") and not self._should_delete_form(f)
        ]


# formset biasa (bukan inline) soalnya baris kecocokan dibikin ulang tiap simpan,
# jadi tuker atau hapus lalu tambah perangkat yang sama ga nabrak unique constraint
CompatibilityFormSet = formset_factory(
    CompatibilityForm,
    formset=BaseCompatibilityFormSet,
    extra=0,
    min_num=1,
    max_num=20,
    validate_max=True,
    can_delete=True,
)


def https_only(value):
    # URLValidator(schemes=...) pesannya ketimpa "Masukkan URL yang valid." dari URLField
    if not value.lower().startswith("https://"):
        raise ValidationError("Link toko harus pakai https://.", code="https")


class SourceForm(forms.ModelForm):
    price = forms.IntegerField(
        label="Harga (Rp)",
        min_value=1,
        max_value=MAX_PRICE,
        widget=forms.NumberInput(attrs={"inputmode": "numeric", "placeholder": "185000"}),
        error_messages={"min_value": "Harga minimal Rp 1."},
    )
    url = forms.URLField(
        label="Link toko",
        max_length=200,
        assume_scheme="https",
        validators=[https_only],
    )

    class Meta:
        model = PartSource
        fields = ["vendor_name", "city", "price", "url", "contact"]
        labels = {"vendor_name": "Nama toko", "city": "Kota", "contact": "Kontak"}
        help_texts = {"contact": "Nomor WhatsApp atau akun toko."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


# external_id ga ada di form, jadi toko hasil sync tetap kebawa waktu diedit
SourceFormSet = inlineformset_factory(
    SparePart,
    PartSource,
    form=SourceForm,
    extra=0,
    max_num=30,
    validate_max=True,
    can_delete=True,
)
