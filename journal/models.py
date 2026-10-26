from django.conf import settings
from django.db import models


class CategoryImpactProfile(models.Model):
    category = models.OneToOneField(
        "devices.DeviceCategory",
        on_delete=models.CASCADE,
        related_name="impact_profile",
    )
    avg_mass_kg = models.DecimalField(max_digits=6, decimal_places=2)
    replacement_cost = models.PositiveBigIntegerField(
        help_text="Total biaya yang diperlukan untuk mengganti perangkat dengan yang baru (Rp)"
    )

    class Meta:
        ordering = ["category__name"]

    def __str__(self):
        return f"{self.category} ({self.avg_mass_kg} kg)"

    
class RepairLog(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Direncanakan"
        IN_PROGRESS = "in_progress", "Sedang dikerjakan"
        SUCCEEDED = "succeeded", "Berhasil"
        FAILED = "failed", "Gagal"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="repair_logs"
    )

    guide = models.ForeignKey(
        "guides.RepairGuide",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="repair_logs",
    )

    device = models.ForeignKey(
        "devices.Device",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="repair_logs",
    )

    title = models.CharField(max_length=200)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)
    cost_spent = models.PositiveBigIntegerField(default=0, help_text="Total biaya yang dikeluarkan selama perbaikan (Rp)")
    notes = models.TextField(blank=True)
    repaired_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-repaired_at", "-pk"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
            from .impact import sync_impact
    
            sync_impact(self)


class ImpactEstimate(models.Model):
    log = models.OneToOneField(RepairLog, on_delete=models.CASCADE, related_name="impact")
    waste_avoided_kg = models.DecimalField(max_digits=8, decimal_places=2)
    cost_avoided = models.PositiveBigIntegerField()
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.log}: {self.waste_avoided_kg} kg"
