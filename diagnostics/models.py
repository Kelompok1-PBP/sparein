from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Symptom(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", "Ringan"
        MEDIUM = "medium", "Sedang"
        HIGH = "high", "Parah"

    device = models.ForeignKey(
        "devices.Device", on_delete=models.PROTECT, related_name="symptoms"
    )
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(max_length=1000, blank=True)
    severity = models.CharField(max_length=6, choices=Severity.choices, default=Severity.MEDIUM)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._new_slug()
        super().save(*args, **kwargs)

    def _new_slug(self):
        base = slugify(self.title)[:120] or "gejala"
        slug, n = base, 2
        while Symptom.objects.filter(slug=slug).exists():
            slug, n = f"{base}-{n}", n + 1
        return slug


class Cause(models.Model):
    """Kemungkinan penyebab. Diranking dari gejala yang cocok."""

    device = models.ForeignKey(
        "devices.Device", on_delete=models.PROTECT, related_name="causes"
    )
    title = models.CharField(max_length=120)
    note = models.CharField(max_length=255, blank=True)
    symptoms = models.ManyToManyField(Symptom, related_name="causes")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class DiagnosisSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    device = models.ForeignKey("devices.Device", on_delete=models.PROTECT)
    symptoms = models.ManyToManyField(Symptom)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class DiagnosisResult(models.Model):
    class Likelihood(models.TextChoices):
        HIGH = "high", "Tinggi"
        MEDIUM = "medium", "Sedang"
        LOW = "low", "Rendah"

    session = models.ForeignKey(DiagnosisSession, on_delete=models.CASCADE, related_name="results")
    cause = models.ForeignKey(Cause, on_delete=models.CASCADE)
    likelihood = models.CharField(max_length=6, choices=Likelihood.choices)
    note = models.CharField(max_length=255, blank=True)
