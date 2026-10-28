from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from devices.models import Device, DeviceCategory
from guides.models import RepairGuide

from .impact import DEFAULT_MASS_KG, DEFAULT_REPLACEMENT_COST
from .models import CategoryImpactProfile, ImpactEstimate, RepairLog
from .selectors import logs_for, site_impact_totals, user_impact_summary

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


class SelectorTests(JournalBase):
    def test_logs_for_returns_only_own_records(self):
        mine = self.make_log()
        self.make_log(user=self.other, title="Punya orang lain")
        self.assertEqual(list(logs_for(self.user)), [mine])

    def test_user_summary_counts_only_own_successes(self):
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(status=Status.FAILED)
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        summary = user_impact_summary(self.user)
        self.assertEqual(summary["repairs"], 1)
        self.assertEqual(summary["waste_avoided_kg"], Decimal("0.20"))

    def test_site_totals_span_all_users_and_default_to_zero(self):
        self.assertEqual(site_impact_totals()["repairs"], 0)
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        totals = site_impact_totals()
        self.assertEqual(totals["repairs"], 2)
        self.assertEqual(totals["cost_avoided"], 6_000_000)


class SeedCommandTests(TestCase): # f
    def test_seed_creates_profiles_for_root_categories_only(self):
        root = DeviceCategory.objects.create(name="Mac Laptop")
        DeviceCategory.objects.create(name="MacBook Air", parent=root)
        out = StringIO()
        call_command("seed_impact_profiles", stdout=out)
        call_command("seed_impact_profiles", stdout=out)  # aman dijalankan ulang
        self.assertEqual(CategoryImpactProfile.objects.count(), 1)
        self.assertEqual(CategoryImpactProfile.objects.get().category, root)


class ViewBase(JournalBase):
    password = "test-pass-123"

    def setUp(self):
        super().setUp()
        self.client.login(username="mars", password=self.password)
        self.foreign = self.make_log(user=self.other, title="Rahasia orang lain")

    def payload(self, **overrides):
        data = {
            "title": "Ganti layar",
            "device": self.device.pk,
            "guide": "",
            "status": Status.SUCCEEDED,
            "cost_spent": 500_000,
            "repaired_at": "2026-10-01",
            "notes": "Selesai dalam sehari",
        }
        data.update(overrides)
        return data


class AccessTests(ViewBase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_visitor_sees_only_site_counter_on_list(self):
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["visitor"])
        self.assertEqual(response.context["site"]["repairs"], 1)
        self.assertNotContains(response, "Rahasia orang lain")
        self.assertNotIn("logs", response.context)

    def test_visitor_is_redirected_to_login_on_every_other_page(self):
        pk = self.foreign.pk
        for name, args in [
            ("journal:create", []),
            ("journal:detail", [pk]),
            ("journal:edit", [pk]),
            ("journal:delete", [pk]),
        ]:
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn("/accounts/login/", response["Location"])

    def test_visitor_cannot_create_or_change_anything(self):
        before = RepairLog.objects.count()
        self.client.post(reverse("journal:create"), self.payload())
        self.client.post(reverse("journal:delete", args=[self.foreign.pk]))
        self.assertEqual(RepairLog.objects.count(), before)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.title, "Rahasia orang lain")


class CreateTests(ViewBase):
    def test_create_form_renders(self):
        response = self.client.get(reverse("journal:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catat perbaikan")

    def test_create_saves_log_for_current_user_and_computes_impact(self):
        response = self.client.post(reverse("journal:create"), self.payload())
        log = RepairLog.objects.get(title="Ganti layar")
        self.assertRedirects(response, reverse("journal:detail", args=[log.pk]))
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.impact.cost_avoided, 2_500_000)

    def test_user_field_in_post_cannot_be_spoofed(self):
        self.client.post(
            reverse("journal:create"), self.payload(user=self.other.pk)
        )
        self.assertEqual(RepairLog.objects.get(title="Ganti layar").user, self.user)

    def test_missing_title_is_rejected_without_saving(self):
        response = self.client.post(reverse("journal:create"), self.payload(title=""))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(RepairLog.objects.filter(title="").exists())

    def test_negative_cost_is_rejected(self):
        response = self.client.post(
            reverse("journal:create"), self.payload(cost_spent=-1)
        )
        self.assertEqual(response.status_code, 400)

    def test_finished_log_without_date_gets_today(self):
        self.client.post(reverse("journal:create"), self.payload(repaired_at=""))
        self.assertEqual(
            RepairLog.objects.get(title="Ganti layar").repaired_at, date.today()
        )

    def test_guide_must_match_selected_device(self):
        other_device = Device.objects.create(name="iPad", category=self.iphone_cat)
        guide = RepairGuide.objects.create(
            device=other_device, author=self.other, title="G", slug="g",
            summary="s", difficulty="Easy", time_required_minutes=5, published=True,
        )
        response = self.client.post(
            reverse("journal:create"), self.payload(guide=guide.pk)
        )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "perangkat yang berbeda", status_code=400)

    def test_draft_guide_of_someone_else_cannot_be_linked(self):
        draft = RepairGuide.objects.create(
            device=self.device, author=self.other, title="Draf", slug="draf",
            summary="s", difficulty="Easy", time_required_minutes=5, published=False,
        )
        response = self.client.post(
            reverse("journal:create"), self.payload(guide=draft.pk)
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(RepairLog.objects.filter(guide=draft).exists())

    def test_published_guide_can_be_linked(self):
        guide = RepairGuide.objects.create(
            device=self.device, author=self.other, title="Publik", slug="publik",
            summary="s", difficulty="Easy", time_required_minutes=5, published=True,
        )
        self.client.post(reverse("journal:create"), self.payload(guide=guide.pk))
        self.assertEqual(RepairLog.objects.get(title="Ganti layar").guide, guide)


class ReadTests(ViewBase):
    def test_list_shows_only_own_logs(self):
        mine = self.make_log(title="Punya saya")
        response = self.client.get(reverse("journal:list"))
        self.assertContains(response, "Punya saya")
        self.assertNotContains(response, "Rahasia orang lain")
        self.assertEqual(list(response.context["logs"]), [mine])

    def test_list_filters_by_status(self):
        self.make_log(title="Rencana", status=Status.PLANNED)
        self.make_log(title="Beres", status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:list"), {"status": "succeeded"})
        self.assertContains(response, "Beres")
        self.assertNotContains(response, "Rencana")

    def test_list_shows_personal_and_site_impact(self):
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:list"))
        self.assertEqual(response.context["summary"]["repairs"], 1)
        self.assertEqual(response.context["site"]["repairs"], 2)

    def test_empty_list_shows_empty_state(self):
        RepairLog.objects.filter(user=self.user).delete()
        self.assertContains(
            self.client.get(reverse("journal:list")), "Belum ada catatan perbaikan"
        )

    def test_detail_of_own_log(self):
        log = self.make_log(status=Status.SUCCEEDED, notes="baris satu")
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dampak perbaikan ini")

    def test_detail_of_someone_elses_log_is_404(self):
        response = self.client.get(reverse("journal:detail", args=[self.foreign.pk]))
        self.assertEqual(response.status_code, 404)

    def test_titles_are_escaped(self):
        self.make_log(title="<script>alert(1)</script>")
        response = self.client.get(reverse("journal:list"))
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")


class UpdateTests(ViewBase):
    def setUp(self):
        super().setUp()
        self.log = self.make_log(title="Awal")

    def test_edit_form_is_prefilled(self):
        response = self.client.get(reverse("journal:edit", args=[self.log.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Awal"')

    def test_owner_can_update(self):
        response = self.client.post(
            reverse("journal:edit", args=[self.log.pk]), self.payload(title="Baru")
        )
        self.assertRedirects(response, reverse("journal:detail", args=[self.log.pk]))
        self.log.refresh_from_db()
        self.assertEqual(self.log.title, "Baru")
        self.assertEqual(self.log.impact.cost_avoided, 2_500_000)

    def test_update_keeps_the_owner(self):
        self.client.post(
            reverse("journal:edit", args=[self.log.pk]),
            self.payload(user=self.other.pk),
        )
        self.log.refresh_from_db()
        self.assertEqual(self.log.user, self.user)

    def test_invalid_update_is_rejected(self):
        response = self.client.post(
            reverse("journal:edit", args=[self.log.pk]), self.payload(title="")
        )
        self.assertEqual(response.status_code, 400)
        self.log.refresh_from_db()
        self.assertEqual(self.log.title, "Awal")

    def test_cannot_edit_someone_elses_log(self):
        url = reverse("journal:edit", args=[self.foreign.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self.payload(title="Dibajak")).status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.title, "Rahasia orang lain")


class DeleteTests(ViewBase):
    def setUp(self):
        super().setUp()
        self.log = self.make_log(status=Status.SUCCEEDED)

    def test_get_shows_confirmation_and_deletes_nothing(self):
        response = self.client.get(reverse("journal:delete", args=[self.log.pk]))
        self.assertContains(response, "Hapus catatan?")
        self.assertTrue(RepairLog.objects.filter(pk=self.log.pk).exists())

    def test_owner_can_delete_and_estimate_goes_with_it(self):
        response = self.client.post(reverse("journal:delete", args=[self.log.pk]))
        self.assertRedirects(response, reverse("journal:list"))
        self.assertFalse(RepairLog.objects.filter(pk=self.log.pk).exists())
        self.assertEqual(ImpactEstimate.objects.count(), 0)

    def test_cannot_delete_someone_elses_log(self):
        url = reverse("journal:delete", args=[self.foreign.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(RepairLog.objects.filter(pk=self.foreign.pk).exists())


class AjaxAccessTests(ViewBase):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_visitor_gets_json_403_from_ajax_and_api(self):
        status = self.client.post(
            reverse("journal:status", args=[self.foreign.pk]),
            {"status": Status.FAILED},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(status.status_code, 403)
        self.assertEqual(self.client.get("/api/journal/summary/").status_code, 403)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.status, Status.PLANNED)


class StatusAjaxTests(ViewBase):
    def setUp(self):
        super().setUp()
        self.log = self.make_log()
        self.url = reverse("journal:status", args=[self.log.pk])

    def test_status_change_returns_impact_and_summary(self):
        response = self.client.post(self.url, {"status": Status.SUCCEEDED})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "succeeded")
        self.assertEqual(data["status_label"], "Berhasil")
        self.assertEqual(data["impact"]["waste_avoided_kg"], 0.2)
        self.assertEqual(data["summary"]["repairs"], 1)
        self.log.refresh_from_db()
        self.assertEqual(self.log.repaired_at, date.today())

    def test_leaving_succeeded_removes_impact(self):
        self.client.post(self.url, {"status": Status.SUCCEEDED})
        data = self.client.post(self.url, {"status": Status.FAILED}).json()
        self.assertIsNone(data["impact"])
        self.assertEqual(data["summary"]["repairs"], 0)

    def test_invalid_status_is_rejected(self):
        response = self.client.post(self.url, {"status": "hacked"})
        self.assertEqual(response.status_code, 400)
        self.log.refresh_from_db()
        self.assertEqual(self.log.status, Status.PLANNED)

    def test_only_post_is_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_cannot_change_status_of_someone_elses_log(self):
        response = self.client.post(
            reverse("journal:status", args=[self.foreign.pk]),
            {"status": Status.SUCCEEDED},
        )
        self.assertEqual(response.status_code, 404)

    def test_csrf_token_is_required(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username="mars", password=self.password)
        response = client.post(self.url, {"status": Status.SUCCEEDED})
        self.assertEqual(response.status_code, 403)


class SummaryApiTests(ViewBase):
    def test_member_gets_own_summary_and_site_totals(self):
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(status=Status.PLANNED)
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        response = self.client.get("/api/journal/summary/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["repairs"], 1)
        self.assertEqual(data["site"]["repairs"], 2)
        self.assertEqual(data["by_status"]["succeeded"], 1)
        self.assertEqual(data["by_status"]["planned"], 1)
        self.assertEqual(data["by_status"]["failed"], 0)

    def test_summary_does_not_leak_other_users_logs(self):
        data = self.client.get("/api/journal/summary/").json()
        self.assertEqual(sum(data["by_status"].values()), 0)
