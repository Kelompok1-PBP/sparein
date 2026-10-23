from django.core.management.base import BaseCommand

from devices.models import DeviceCategory
from journal.models import CategoryImpactProfile

# Perkiraan kasar, boleh diubah lewat admin. (kata kunci nama kategori, kg, rupiah)
RULES = [
    ("laptop", "1.30", 14_000_000),
    ("tablet", "0.50", 4_000_000),
    ("console", "0.40", 4_500_000),
    ("phone", "0.20", 3_500_000),
]


class Command(BaseCommand):
    help = "Isi profil dampak untuk kategori perangkat induk (tanpa parent)."

    def handle(self, *args, **options):
        created = 0
        for category in DeviceCategory.objects.filter(parent__isnull=True):
            name = category.name.lower()
            for keyword, mass, cost in RULES:
                if keyword in name:
                    _, was_new = CategoryImpactProfile.objects.get_or_create(
                        category=category,
                        defaults={"avg_mass_kg": mass, "replacement_cost": cost},
                    )
                    created += was_new
                    break
        self.stdout.write(self.style.SUCCESS(f"{created} profil dampak dibuat."))
