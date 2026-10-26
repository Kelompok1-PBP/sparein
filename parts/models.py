from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


def unique_slug(value):
    base = slugify(value)[:200] or "suku-cadang"
    slug, n = base, 2
    while SparePart.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class SparePart(models.Model):
    class Category(models.TextChoices):
        BATTERY = "battery", "Baterai"
        SCREEN = "screen", "Layar"
        CHARGER = "charger", "Charger"
        CABLE = "cable", "Kabel"
        MOTOR = "motor", "Motor"
        OTHER = "other", "Lainnya"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    part_number = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    # id dari mock API biar sync ulang ga bikin duplikat, kosong kalau diisi manual
    external_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self.name)
        super().save(*args, **kwargs)


class PartCompatibility(models.Model):
    part = models.ForeignKey(
        SparePart, on_delete=models.CASCADE, related_name="compatibilities"
    )
    # PROTECT biar device yang masih punya suku cadang ga ke-delete diam-diam
    device = models.ForeignKey(
        "devices.Device", on_delete=models.PROTECT, related_name="part_compatibilities"
    )
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "part compatibilities"
        constraints = [
            models.UniqueConstraint(fields=["part", "device"], name="unique_part_device")
        ]

    def __str__(self):
        return f"{self.part} → {self.device}"


class PartSource(models.Model):
    part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name="sources")
    vendor_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    currency = models.CharField(max_length=3, default="IDR")
    url = models.URLField()
    contact = models.CharField(max_length=100, blank=True)
    last_checked = models.DateField(default=timezone.localdate)
    external_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["vendor_name"]

    def __str__(self):
        return f"{self.vendor_name} ({self.part})"
