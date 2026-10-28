from decimal import ROUND_HALF_UP, Decimal

from django.utils import formats


def _dots(number):
    return f"{int(number):,}".replace(",", ".")


def _comma(decimal):
    text = format(decimal.normalize(), "f")
    return text.replace(".", ",")


def rupiah(value):
    return f"Rp {_dots(value or 0)}"


def rupiah_short(value):
    number = int(value or 0)
    if number < 1_000_000:
        return rupiah(number)
    millions = (Decimal(number) / 1_000_000).quantize(Decimal("0.1"), ROUND_HALF_UP)
    if millions < 1000:
        return f"Rp {_comma(millions)} juta"
    billions = (Decimal(number) / 1_000_000_000).quantize(Decimal("0.1"), ROUND_HALF_UP)
    return f"Rp {_comma(billions)} miliar"


def kg(value):
    amount = Decimal(value or 0).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return f"{_comma(amount)} kg"


def short_date(value):
    if not value:
        return ""
    return formats.date_format(value, "j M Y")
