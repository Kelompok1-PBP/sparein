from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from devices.selectors import get_device_qs
from guides.ifixit import ImportFailure, fetch_guide, import_guide
from guides.permissions import can_create


class Command(BaseCommand):
    help = "Impor satu panduan iFixit sebagai draf; tidak menimpa panduan yang ada."

    def add_arguments(self, parser):
        parser.add_argument("guide_id", type=int)
        parser.add_argument("--device", type=int, required=True)
        parser.add_argument("--author", required=True)
        parser.add_argument("--minutes", type=int)

    def handle(self, guide_id, device, author, minutes=None, **options):
        user = get_user_model().objects.filter(username=author).first()
        target = get_device_qs().filter(pk=device).first()
        if not user or not can_create(user) or not target:
            raise CommandError(
                "Gunakan penulis Contributor/Admin dan ID perangkat yang ada."
            )
        try:
            guide = import_guide(
                fetch_guide(guide_id), device=target, author=user, minutes=minutes
            )
        except ImportFailure as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Draf: /guides/{guide.slug}/edit/"))
