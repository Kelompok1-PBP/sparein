from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        MEMBER = "MEMBER", "Member"
        CONTRIBUTOR = "CONTRIBUTOR", "Contributor"
        ADMIN = "ADMIN", "Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.MEMBER)

    def __str__(self):
        return f"{self.user} ({self.role})"
