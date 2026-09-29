from django.test import TestCase

from devices.models import Device, DeviceCategory


class ModelTests(TestCase):
    def setUp(self):
        self.phone = DeviceCategory.objects.create(name="Phone")

    def test_category_slug_from_name(self):
        self.assertEqual(self.phone.slug, "phone")

    def test_duplicate_device_name_gets_suffix(self):
        a = Device.objects.create(name="iPhone 12", category=self.phone, brand="Apple")
        b = Device.objects.create(name="iPhone 12", category=self.phone, brand="Apple")
        self.assertEqual((a.slug, b.slug), ("iphone-12", "iphone-12-2"))

    def test_slug_kept_on_rename(self):
        d = Device.objects.create(name="Galaxy S21", category=self.phone, brand="Samsung")
        d.name = "Galaxy S21 FE"
        d.save()
        self.assertEqual(d.slug, "galaxy-s21")
