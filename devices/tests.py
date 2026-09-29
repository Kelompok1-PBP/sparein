from django.http import Http404
from django.test import TestCase

from devices.ifixit import upsert_family
from devices.models import Device, DeviceCategory
from devices.selectors import get_device_or_404, get_device_qs


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


class SelectorTests(TestCase):
    def setUp(self):
        phone = DeviceCategory.objects.create(name="Phone")
        laptop = DeviceCategory.objects.create(name="Laptop")
        Device.objects.create(name="iPhone 12", category=phone, brand="Apple")
        Device.objects.create(name="Galaxy S21", category=phone, brand="Samsung")
        Device.objects.create(name="MacBook Air M1", category=laptop, brand="Apple")

    def test_no_filter_returns_all(self):
        self.assertEqual(get_device_qs().count(), 3)

    def test_q_matches_name_case_insensitive(self):
        self.assertEqual([d.name for d in get_device_qs(q="galaxy")], ["Galaxy S21"])

    def test_category_and_brand_combine(self):
        names = [d.name for d in get_device_qs(category="phone", brand="apple")]
        self.assertEqual(names, ["iPhone 12"])

    def test_get_or_404(self):
        self.assertEqual(get_device_or_404("iphone-12").brand, "Apple")
        with self.assertRaises(Http404):
            get_device_or_404("nope")


SAMPLE = {
    "wikiid": 1,
    "display_title": "iPhone",
    "ancestors": [{"wikiid": 437, "display_title": "Phone"}],
    "children": [
        {
            "wikiid": 10,
            "display_title": "iPhone 12",
            "summary": "2020 phone.",
            "image": {"standard": "https://img.example/12.standard"},
        },
        {"wikiid": 11, "display_title": "iPhone 13", "summary": "", "image": None},
    ],
}


class IfixitTests(TestCase):
    def test_family_mapped_under_parent(self):
        self.assertEqual(upsert_family(SAMPLE, "Apple"), 2)
        d = Device.objects.get(ifixit_wikiid=10)
        self.assertEqual(
            (d.brand, d.category.name, d.category.parent.name), ("Apple", "iPhone", "Phone")
        )
        self.assertEqual(Device.objects.get(ifixit_wikiid=11).image_url, "")
