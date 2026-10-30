from django import template

from .. import labels

register = template.Library()

register.filter("difficulty_label", labels.difficulty_label)
register.filter("difficulty_tone", labels.difficulty_tone)
register.filter("duration_label", labels.duration_label)
