from django.core.management import BaseCommand

from parts import mock_api


class Command(BaseCommand):
    help = "Sync suku cadang dari mock API, kalau gagal pakai snapshot lokal"

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true", help="Lewati cache")

    def handle(self, *args, fresh, **opts):
        try:
            counts = mock_api.upsert_parts(mock_api.fetch_parts(fresh=fresh))
        except mock_api.SyncFailure as exc:
            self.stderr.write(f"Mock API unavailable ({exc}), loading snapshot")
            counts = mock_api.upsert_parts(mock_api.load_snapshot())
        self.stdout.write(
            f"Synced {counts['parts']} parts, {counts['sources']} sources, "
            f"{counts['skipped']} skipped"
        )
