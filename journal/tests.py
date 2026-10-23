from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from devices.models import Device, DeviceCategory
from guides.models import RepairGuide

from .impact import DEFAULT_MASS_KG, DEFAULT_REPLACEMENT_COST
from .models import CategoryImpactProfile, ImpactEstimate, RepairLog

Status = RepairLog.Status


class JournalBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("mars", password="test-pass-123")
        self.other = User.objects.create_user("other", password="test-pass-123")
        self.phone = DeviceCategory.objects.create(name="Phone")
        self.iphone_cat = DeviceCategory.objects.create(name="Apple iPhone", parent=self.phone)
        self.device = Device.objects.create(name="iPhone 12", category=self.iphone_cat)
        CategoryImpactProfile.objects.create(
            category=self.phone, avg_mass_kg=Decimal("0.20"), replacement_cost=3_000_000
        )

    def make_log(self, **kwargs):
        data = {"user": self.user, "title": "Ganti baterai", "device": self.device}
        data.update(kwargs)
        return RepairLog.objects.create(**data)


class ImpactTests(JournalBase):
    def test_only_succeeded_log_gets_estimate(self):
        for status in (Status.PLANNED, Status.IN_PROGRESS, Status.FAILED):
            log = self.make_log(status=status)
            self.assertFalse(ImpactEstimate.objects.filter(log=log).exists())
        log = self.make_log(status=Status.SUCCEEDED, cost_spent=500_000)
        self.assertEqual(log.impact.waste_avoided_kg, Decimal("0.20"))
        self.assertEqual(log.impact.cost_avoided, 2_500_000)

    def test_profile_found_through_parent_category(self):
        log = self.make_log(status=Status.SUCCEEDED)
        self.assertEqual(log.impact.cost_avoided, 3_000_000)

    def test_default_values_when_no_profile(self):
        CategoryImpactProfile.objects.all().delete()
        log = self.make_log(status=Status.SUCCEEDED)
        self.assertEqual(log.impact.waste_avoided_kg, DEFAULT_MASS_KG)
        self.assertEqual(log.impact.cost_avoided, DEFAULT_REPLACEMENT_COST)

    def test_cost_avoided_never_negative(self):
        log = self.make_log(status=Status.SUCCEEDED, cost_spent=9_000_000)
        self.assertEqual(log.impact.cost_avoided, 0)

    def test_device_taken_from_guide_when_log_has_none(self):
        guide = RepairGuide.objects.create(
            device=self.device, author=self.user, title="G", slug="g",
            summary="s", difficulty="Easy", time_required_minutes=5, published=True,
        )
        log = self.make_log(device=None, guide=guide, status=Status.SUCCEEDED)
        self.assertEqual(log.impact.waste_avoided_kg, Decimal("0.20"))

    def test_no_device_and_no_guide_means_no_estimate(self):
        log = self.make_log(device=None, status=Status.SUCCEEDED)
        self.assertFalse(ImpactEstimate.objects.filter(log=log).exists())

    def test_estimate_follows_status_changes(self):
        log = self.make_log(status=Status.SUCCEEDED)
        self.assertEqual(ImpactEstimate.objects.count(), 1)
        log.status = Status.FAILED
        log.save()
        self.assertEqual(ImpactEstimate.objects.count(), 0)
        log.status = Status.SUCCEEDED
        log.save()
        self.assertEqual(ImpactEstimate.objects.count(), 1)

    def test_deleting_guide_keeps_the_log(self):
        guide = RepairGuide.objects.create(
            device=self.device, author=self.user, title="G", slug="g",
            summary="s", difficulty="Easy", time_required_minutes=5,
        )
        log = self.make_log(guide=guide)
        guide.delete()
        log.refresh_from_db()
        self.assertIsNone(log.guide)
