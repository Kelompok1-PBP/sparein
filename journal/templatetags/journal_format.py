from django import template

from .. import formatting

register = template.Library()

register.filter("rupiah", formatting.rupiah)
register.filter("rupiah_short", formatting.rupiah_short)
register.filter("kg", formatting.kg)
register.filter("short_date", formatting.short_date)
