from django import forms

# Widget yang dipakai gaya sendiri, jadi ga dikasih class .input
_OWN_STYLE = (forms.CheckboxInput, forms.RadioSelect, forms.HiddenInput)


class InputStyleMixin:
    """Kasih class .input ke widget dan aria-invalid ke isian yang error, biar tampil sama dengan form lain."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, _OWN_STYLE):
                field.widget.attrs.setdefault("class", "input")

    def add_error(self, field, error):
        super().add_error(field, error)
        if field in self.fields:
            self.fields[field].widget.attrs["aria-invalid"] = "true"
