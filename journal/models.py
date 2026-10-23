from django.conf import settings
from django.db import models


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
