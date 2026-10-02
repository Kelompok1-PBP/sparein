from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class RepairGuide(models.Model):
    DIFFICULTIES = [
        (v, v) for v in ["Very easy", "Easy", "Moderate", "Difficult", "Very difficult"]
    ]
    device = models.ForeignKey(
        "devices.Device", on_delete=models.PROTECT, related_name="repair_guides"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    summary = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTIES)
    time_required_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    tools = models.TextField(blank=True, help_text="Satu alat per baris.")
    ifixit_guideid = models.PositiveIntegerField(null=True, blank=True, unique=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="repair_guides"
    )
    source_author = models.CharField(max_length=200, blank=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ["title", "pk"]

    def __str__(self):
        return self.title


class GuideStep(models.Model):
    guide = models.ForeignKey(
        RepairGuide, on_delete=models.CASCADE, related_name="steps"
    )
    order = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=200)
    detail = models.TextField()
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ["order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["guide", "order"], name="unique_guide_step_order"
            )
        ]


class SafetyWarning(models.Model):
    guide = models.ForeignKey(
        RepairGuide, on_delete=models.CASCADE, related_name="warnings"
    )
    level = models.CharField(
        max_length=10,
        choices=[("info", "Info"), ("caution", "Perhatian"), ("danger", "Bahaya")],
    )
    message = models.TextField()
