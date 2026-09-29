from django.db import models
from django.utils.text import slugify


def unique_slug(model, value):
    base = slugify(value)[:200] or "item"
    slug, n = base, 2
    while model.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class DeviceCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "device categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(DeviceCategory, self.name)
        super().save(*args, **kwargs)
