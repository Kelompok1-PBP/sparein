from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import UserProfile
from devices.models import Device, DeviceCategory
from parts.models import PartCompatibility, PartSource, SparePart
from parts.selectors import (
    get_part_or_404,
    get_part_qs,
    get_sources_for,
    visible_part_qs,
)
from parts.templatetags.parts_tags import days_ago, rupiah


def make_user(name, role=UserProfile.Role.MEMBER):
    user = User.objects.create_user(name, password="x")
    user.profile.role = role
    user.profile.save()
    return user


def make_part(name, device=None, category="battery", prices=(), **extra):
    part = SparePart.objects.create(name=name, category=category, **extra)
    if device:
        PartCompatibility.objects.create(part=part, device=device)
    for i, price in enumerate(prices):
        PartSource.objects.create(
            part=part, vendor_name=f"Toko {name} {i}", city="Depok", price=price,
            url="https://toko.example/item", contact=f"0812-0000-{i:04d}",
        )
    return part


class ModelTests(TestCase):
    def setUp(self):
        cat = DeviceCategory.objects.create(name="Phone")
        self.device = Device.objects.create(name="iPhone 11", category=cat, brand="Apple")

    def test_slug_from_name_and_suffix_on_duplicate(self):
        a = make_part("Baterai iPhone 11")
        b = make_part("Baterai iPhone 11")
        self.assertEqual((a.slug, b.slug), ("baterai-iphone-11", "baterai-iphone-11-2"))

    def test_slug_kept_on_rename(self):
        part = make_part("Layar iPhone 11", category="screen")
        part.name = "Layar iPhone 11 OLED"
        part.save()
        self.assertEqual(part.slug, "layar-iphone-11")

    def test_same_device_twice_rejected(self):
        part = make_part("Baterai iPhone 11", device=self.device)
        with self.assertRaises(IntegrityError):
            PartCompatibility.objects.create(part=part, device=self.device)

    def test_device_with_parts_is_protected(self):
        make_part("Baterai iPhone 11", device=self.device)
        with self.assertRaises(ProtectedError):
            self.device.delete()

    def test_deleting_part_removes_sources_and_compatibility(self):
        make_part("Baterai iPhone 11", device=self.device, prices=[185000]).delete()
        self.assertFalse(PartSource.objects.exists())
        self.assertFalse(PartCompatibility.objects.exists())


class SelectorTests(TestCase):
    def setUp(self):
        cat = DeviceCategory.objects.create(name="Phone")
        self.iphone = Device.objects.create(name="iPhone 11", category=cat, brand="Apple")
        galaxy = Device.objects.create(name="Galaxy A52", category=cat, brand="Samsung")
        make_part(
            "Baterai iPhone 11", self.iphone, prices=[185000, 320000], part_number="616-00644"
        )
        make_part("Layar iPhone 11", self.iphone, category="screen", prices=[900000])
        make_part("Baterai Galaxy A52", galaxy)

    def names(self, qs):
        return sorted(p.name for p in qs)

    def test_no_filter_returns_all(self):
        self.assertEqual(get_part_qs().count(), 3)

    def test_q_matches_name_or_part_number(self):
        self.assertEqual(self.names(get_part_qs(q="galaxy")), ["Baterai Galaxy A52"])
        self.assertEqual(self.names(get_part_qs(q="616-006")), ["Baterai iPhone 11"])

    def test_device_slug_and_category_combine(self):
        names = self.names(get_part_qs(device="iphone-11", category="battery"))
        self.assertEqual(names, ["Baterai iPhone 11"])

    def test_category_accepts_list(self):
        self.assertEqual(get_part_qs(category=["battery", "screen"]).count(), 3)

    def test_max_price_keeps_part_with_any_cheap_source_once(self):
        self.assertEqual(self.names(get_part_qs(max_price=200000)), ["Baterai iPhone 11"])

    def test_get_or_404(self):
        self.assertEqual(get_part_or_404("layar-iphone-11").category, "screen")
        with self.assertRaises(Http404):
            get_part_or_404("nope")

    def test_visitor_qs_ignores_max_price_and_has_no_price(self):
        qs = visible_part_qs(AnonymousUser(), max_price=200000)
        self.assertEqual(qs.count(), 3)
        self.assertNotIn("lowest_price", qs.query.annotations)

    def test_member_qs_filters_and_annotates_price(self):
        qs = visible_part_qs(make_user("m"), max_price=200000)
        part = qs.get()
        self.assertEqual((part.lowest_price, part.highest_price), (185000, 320000))
        self.assertEqual(part.source_count, 2)

    def test_visitor_sources_hide_price_and_contact(self):
        part = SparePart.objects.get(slug="baterai-iphone-11")
        rows = list(get_sources_for(part, AnonymousUser()))
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertNotIn("price", row)
            self.assertNotIn("contact", row)

    def test_member_sources_sorted_by_price(self):
        part = SparePart.objects.get(slug="baterai-iphone-11")
        prices = [row["price"] for row in get_sources_for(part, make_user("m"))]
        self.assertEqual(prices, [185000, 320000])


class DeviceDeleteTests(TestCase):
    def test_admin_sees_message_when_device_still_has_parts(self):
        cat = DeviceCategory.objects.create(name="Phone")
        device = Device.objects.create(name="iPhone 11", category=cat, brand="Apple")
        make_part("Baterai iPhone 11", device=device)
        self.client.force_login(make_user("a", UserProfile.Role.ADMIN))
        resp = self.client.post(reverse("devices:delete", args=[device.slug]))
        self.assertContains(resp, "masih dipakai")
        self.assertTrue(Device.objects.filter(pk=device.pk).exists())


class FilterTagTests(TestCase):
    def test_rupiah(self):
        self.assertEqual(rupiah(1850000), "Rp 1.850.000")
        self.assertEqual(rupiah(None), "")

    def test_days_ago(self):
        today = timezone.localdate()
        self.assertEqual(days_ago(today), "hari ini")
        self.assertEqual(days_ago(today - timedelta(days=1)), "kemarin")
        self.assertEqual(days_ago(today - timedelta(days=12)), "12 hari lalu")


class ListPageTests(TestCase):
    def setUp(self):
        cat = DeviceCategory.objects.create(name="Phone")
        self.iphone = Device.objects.create(name="iPhone 11", category=cat, brand="Apple")
        self.pixel = Device.objects.create(name="Pixel 7", category=cat, brand="Google")
        make_part("Baterai iPhone 11", self.iphone, prices=[185000, 320000])
        make_part("Layar iPhone 11", self.iphone, category="screen", prices=[900000])
        make_part("Kabel USB-C", category="cable")
        self.url = reverse("parts:list")

    def test_visitor_sees_parts_without_price(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "Baterai iPhone 11")
        self.assertContains(resp, "Masuk untuk lihat harga")
        self.assertNotContains(resp, "185.000")
        self.assertNotContains(resp, 'name="max_price"')

    def test_member_sees_lowest_price_and_price_filter(self):
        self.client.force_login(make_user("m"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Rp 185.000")
        self.assertContains(resp, 'name="max_price"')
        self.assertNotContains(resp, "Masuk untuk lihat harga")

    def test_part_without_source_says_price_unavailable(self):
        self.assertContains(self.client.get(self.url, {"q": "kabel"}), "Harga belum tersedia")

    def test_filter_by_device_and_category(self):
        resp = self.client.get(self.url, {"device": "iphone-11", "category": "screen"})
        self.assertContains(resp, "Layar iPhone 11")
        self.assertNotContains(resp, "Baterai iPhone 11")

    def test_visitor_max_price_is_ignored(self):
        resp = self.client.get(self.url, {"max_price": "1"})
        self.assertEqual(len(resp.context["parts"]), 3)

    def test_member_max_price_filters(self):
        self.client.force_login(make_user("m"))
        resp = self.client.get(self.url, {"max_price": "200000"})
        self.assertEqual([p.name for p in resp.context["parts"]], ["Baterai iPhone 11"])

    def test_bad_filter_values_are_dropped(self):
        self.client.force_login(make_user("m"))
        resp = self.client.get(self.url, {"max_price": "abc", "category": "nope"})
        self.assertEqual(len(resp.context["parts"]), 3)

    def test_empty_result_offers_reset(self):
        resp = self.client.get(self.url, {"q": "galaxy"})
        self.assertContains(resp, "Belum ada suku cadang yang cocok.")
        self.assertContains(resp, "Reset filter")

    def test_device_without_parts_has_own_message(self):
        resp = self.client.get(self.url, {"device": "pixel-7"})
        self.assertContains(resp, "Belum ada suku cadang terdaftar buat Pixel 7.")

    def test_device_dropdown_only_lists_devices_with_parts(self):
        devices = self.client.get(self.url).context["devices"]
        self.assertEqual([d.slug for d in devices], ["iphone-11"])


class DetailPageTests(TestCase):
    def setUp(self):
        cat = DeviceCategory.objects.create(name="Phone")
        self.device = Device.objects.create(name="iPhone 11", category=cat, brand="Apple")
        self.part = make_part(
            "Baterai iPhone 11", self.device, prices=[320000, 185000], part_number="616-00644"
        )
        self.url = reverse("parts:detail", args=[self.part.slug])

    def test_visitor_sees_shops_but_not_price_or_contact(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "Toko Baterai iPhone 11 0")
        self.assertContains(resp, "https://toko.example/item")
        self.assertContains(resp, "Harga dan kontak penjual cuma buat member.")
        self.assertNotContains(resp, "185.000")
        self.assertNotContains(resp, "0812-0000-")

    def test_member_sees_price_range_and_contact(self):
        self.client.force_login(make_user("m"))
        resp = self.client.get(self.url)
        self.assertContains(resp, "Kisaran Rp 185.000 sampai Rp 320.000 dari 2 toko")
        self.assertContains(resp, "0812-0000-0001")
        self.assertNotContains(resp, "cuma buat member")

    def test_lists_compatible_device_with_link(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, reverse("devices:detail", args=[self.device.slug]))
        self.assertContains(resp, "616-00644")

    def test_old_source_is_flagged(self):
        PartSource.objects.update(last_checked=timezone.localdate() - timedelta(days=40))
        self.assertContains(self.client.get(self.url), "Data lebih dari 30 hari")

    def test_part_without_source_shows_empty_state(self):
        part = make_part("Kabel USB-C", category="cable")
        resp = self.client.get(reverse("parts:detail", args=[part.slug]))
        self.assertContains(resp, "Belum ada toko yang terdaftar buat suku cadang ini.")

    def test_missing_slug_is_404(self):
        self.assertEqual(self.client.get(reverse("parts:detail", args=["nope"])).status_code, 404)
