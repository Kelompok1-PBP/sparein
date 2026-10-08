from django.test import TestCase

from devices.models import Device, DeviceCategory
from diagnostics.models import Cause, Symptom


def make_device(name="iPhone 11"):
    category, _ = DeviceCategory.objects.get_or_create(name="Phone")
    return Device.objects.create(name=name, category=category, brand="Apple")


class ModelTests(TestCase):
    def setUp(self):
        self.device = make_device()

    def test_symptom_slug_from_title(self):
        s = Symptom.objects.create(device=self.device, title="Baterai cepat habis")
        self.assertEqual(s.slug, "baterai-cepat-habis")

    def test_duplicate_symptom_title_gets_suffix(self):
        a = Symptom.objects.create(device=self.device, title="Layar mati")
        b = Symptom.objects.create(device=make_device("iPhone 12"), title="Layar mati")
        self.assertEqual((a.slug, b.slug), ("layar-mati", "layar-mati-2"))

    def test_slug_kept_on_rename(self):
        s = Symptom.objects.create(device=self.device, title="Layar mati")
        s.title = "Layar mati total"
        s.save()
        self.assertEqual(s.slug, "layar-mati")

    def test_severity_defaults_to_medium(self):
        s = Symptom.objects.create(device=self.device, title="Panas")
        self.assertEqual(s.severity, Symptom.Severity.MEDIUM)

    def test_cause_links_to_many_symptoms(self):
        a = Symptom.objects.create(device=self.device, title="Panas")
        b = Symptom.objects.create(device=self.device, title="Boros")
        cause = Cause.objects.create(device=self.device, title="Baterai aus")
        cause.symptoms.add(a, b)
        self.assertEqual(cause.symptoms.count(), 2)
