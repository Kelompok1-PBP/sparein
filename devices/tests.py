from django.test import TestCase

from devices.models import DeviceCategory


class ModelTests(TestCase):
    def setUp(self):
        self.phone = DeviceCategory.objects.create(name="Phone")

    def test_category_slug_from_name(self):
        self.assertEqual(self.phone.slug, "phone")
