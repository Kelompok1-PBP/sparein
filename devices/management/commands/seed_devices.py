from django.core.management import BaseCommand, call_command
from django.db import transaction

from devices import ifixit

# family iFixit yang anaknya langsung device dan umum di Indonesia
FAMILIES = (
    "iPhone:Apple,Samsung Galaxy A:Samsung,Xiaomi Redmi:Xiaomi,OPPO Phone:Oppo,"
    "Samsung Galaxy Tab:Samsung,MacBook Air:Apple,Nintendo Switch Family:Nintendo"
)


class Command(BaseCommand):
    help = "Seed device dari iFixit kalau gagal load fixture"

    def add_arguments(self, parser):
        parser.add_argument("--families", default=FAMILIES)

    def handle(self, *args, families, **opts):
        total = 0
        try:
            with transaction.atomic():
                for pair in families.split(","):
                    title, brand = pair.split(":")
                    total += ifixit.upsert_family(ifixit.fetch_family(title), brand)
        except (OSError, ValueError) as exc:  # error requests turunan OSError
            self.stderr.write(f"iFixit unavailable ({exc}), loading fixture")
            call_command("loaddata", "seed_devices", stdout=self.stdout)
            return
        self.stdout.write(f"Seeded {total} devices")
