"""Format tampilan angka dan tanggal sesuai desain: Rp 210.000, Rp 2,1 juta, 0,2 kg, 20 Sep 2026."""

from decimal import ROUND_HALF_UP, Decimal

from django.utils import formats


def _dots(number):
    return f"{int(number):,}".replace(",", ".")


def _comma(decimal):
    """Desimal dengan koma, tanpa nol di belakang: 2.10 menjadi '2,1', 3.00 menjadi '3'."""
    text = format(decimal.normalize(), "f")
    return text.replace(".", ",")


def rupiah(value):
    """Nilai utuh: Rp 210.000."""
    return f"Rp {_dots(value or 0)}"


def rupiah_short(value):
    """Di bawah satu juta ditulis utuh, di atasnya ringkas: Rp 2,1 juta, Rp 1,2 miliar."""
    number = int(value or 0)
    if number < 1_000_000:
        return rupiah(number)
    millions = (Decimal(number) / 1_000_000).quantize(Decimal("0.1"), ROUND_HALF_UP)
    if millions < 1000:
        return f"Rp {_comma(millions)} juta"
    billions = (Decimal(number) / 1_000_000_000).quantize(Decimal("0.1"), ROUND_HALF_UP)
    return f"Rp {_comma(billions)} miliar"


def kg(value):
    """Berat dengan koma desimal dan paling banyak dua angka di belakang koma: 0,2 kg."""
    amount = Decimal(value or 0).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return f"{_comma(amount)} kg"


def short_date(value):
    """20 Sep 2026. Kosong kalau tanggalnya tidak ada."""
    if not value:
        return ""
    return formats.date_format(value, "j M Y")
