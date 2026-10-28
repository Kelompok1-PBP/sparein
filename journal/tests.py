from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from devices.models import Device, DeviceCategory
from guides.models import RepairGuide

from .formatting import kg, rupiah, rupiah_short, short_date
from .impact import (
    DEFAULT_MASS_KG,
    DEFAULT_REPLACEMENT_COST,
    impact_basis,
    log_device,
)
from .models import CategoryImpactProfile, ImpactEstimate, RepairLog
from .selectors import (
    logs_for,
    site_impact_totals,
    status_counts,
    user_impact_summary,
)

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


class StatusCountsTests(JournalBase):
    def test_counts_every_status_and_the_total(self):
        self.make_log(status=Status.PLANNED)
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(status=Status.SUCCEEDED)
        counts = status_counts(self.user)
        self.assertEqual(counts["planned"], 1)
        self.assertEqual(counts["succeeded"], 2)
        self.assertEqual(counts["in_progress"], 0)
        self.assertEqual(counts["failed"], 0)
        self.assertEqual(counts["all"], 3)

    def test_counts_ignore_other_users(self):
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        self.assertEqual(status_counts(self.user)["all"], 0)


class ImpactBasisTests(JournalBase):
    def test_basis_is_the_category_that_holds_the_profile(self):
        self.assertEqual(impact_basis(self.device), "Phone")

    def test_basis_is_none_without_any_profile(self):
        CategoryImpactProfile.objects.all().delete()
        self.assertIsNone(impact_basis(self.device))
        self.assertIsNone(impact_basis(None))

    def test_log_device_falls_back_to_the_guide_device(self):
        guide = RepairGuide.objects.create(
            device=self.device, author=self.user, title="G", slug="g",
            summary="s", difficulty="Easy", time_required_minutes=5, published=True,
        )
        log = self.make_log(device=None, guide=guide)
        self.assertEqual(log_device(log), self.device)
        self.assertIsNone(log_device(self.make_log(device=None)))


class FormattingTests(TestCase):
    def test_rupiah_is_written_in_full_with_dots(self):
        self.assertEqual(rupiah(210_000), "Rp 210.000")
        self.assertEqual(rupiah(0), "Rp 0")
        self.assertEqual(rupiah(None), "Rp 0")

    def test_short_rupiah_switches_to_juta_and_miliar(self):
        self.assertEqual(rupiah_short(210_000), "Rp 210.000")
        self.assertEqual(rupiah_short(2_100_000), "Rp 2,1 juta")
        self.assertEqual(rupiah_short(3_500_000), "Rp 3,5 juta")
        self.assertEqual(rupiah_short(2_000_000), "Rp 2 juta")
        self.assertEqual(rupiah_short(1_250_000_000), "Rp 1,3 miliar")

    def test_kg_uses_comma_and_drops_trailing_zeros(self):
        self.assertEqual(kg(Decimal("0.20")), "0,2 kg")
        self.assertEqual(kg(Decimal("0.25")), "0,25 kg")
        self.assertEqual(kg(Decimal(12)), "12 kg")
        self.assertEqual(kg(0), "0 kg")

    def test_short_date_uses_indonesian_month_abbreviation(self):
        self.assertEqual(short_date(date(2026, 9, 20)), "20 Sep 2026")
        self.assertEqual(short_date(date(2026, 8, 3)), "3 Agu 2026")
        self.assertEqual(short_date(None), "")


class SeedCommandTests(TestCase):
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
        values = {t["key"]: t["value"] for t in response.context["tiles"]}
        self.assertEqual(values["succeeded"], "1")
        self.assertNotIn("total", values)
        self.assertNotContains(response, "Rahasia orang lain")
        self.assertNotIn("page", response.context)
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
        self.assertEqual(list(response.context["page"]), [mine])
    def test_list_filters_by_status(self):
        self.make_log(title="Rencana", status=Status.PLANNED)
        self.make_log(title="Beres", status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:list"), {"status": "succeeded"})
        self.assertContains(response, "Beres")
        self.assertNotContains(response, "Rencana")

    def test_list_tiles_show_personal_impact_only(self):
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(status=Status.PLANNED)
        self.make_log(user=self.other, status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:list"))
        values = {t["key"]: t["value"] for t in response.context["tiles"]}
        self.assertEqual(
            values,
            {"succeeded": "1", "waste": "0,2 kg", "cost": "Rp 3 juta", "total": "2"},
        )
    def test_empty_list_shows_empty_state_without_tabs(self):
        RepairLog.objects.filter(user=self.user).delete()
        response = self.client.get(reverse("journal:list"))
        self.assertContains(response, "Jurnalmu masih kosong")
        self.assertNotContains(response, 'data-tabs')
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


class ListPageTests(ViewBase):
    def test_tabs_show_counts_and_mark_the_active_one(self):
        self.make_log(status=Status.PLANNED)
        self.make_log(status=Status.SUCCEEDED)
        self.make_log(status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:list"), {"status": "succeeded"})
        tabs = {t["key"]: t for t in response.context["tabs"]}
        self.assertEqual(tabs["all"]["count"], 3)
        self.assertEqual(tabs["succeeded"]["count"], 2)
        self.assertEqual(tabs["failed"]["count"], 0)
        self.assertTrue(tabs["succeeded"]["active"])
        self.assertFalse(tabs["all"]["active"])

    def test_unknown_status_filter_is_ignored(self):
        self.make_log()
        response = self.client.get(reverse("journal:list"), {"status": "hacked"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status"], "")
        self.assertEqual(len(response.context["page"]), 1)

    def test_filter_without_matches_shows_message_but_keeps_tabs(self):
        self.make_log(status=Status.PLANNED)
        response = self.client.get(reverse("journal:list"), {"status": "failed"})
        self.assertContains(response, "Belum ada catatan dengan status ini.")
        self.assertContains(response, "data-tabs")

    def test_list_is_paginated_by_twelve(self):
        for i in range(13):
            self.make_log(title=f"Catatan {i}")
        first = self.client.get(reverse("journal:list"))
        self.assertEqual(len(first.context["page"]), 12)
        self.assertContains(first, "Halaman 1 dari 2")
        second = self.client.get(reverse("journal:list"), {"page": 2})
        self.assertEqual(len(second.context["page"]), 1)

    def test_page_beyond_the_end_falls_back_to_the_last_page(self):
        self.make_log()
        response = self.client.get(reverse("journal:list"), {"page": 99})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page"].number, 1)

    def test_pager_links_keep_the_status_filter(self):
        for i in range(13):
            self.make_log(title=f"Catatan {i}", status=Status.PLANNED)
        response = self.client.get(reverse("journal:list"), {"status": "planned"})
        self.assertContains(response, "?status=planned&amp;page=2")

    def test_ajax_request_gets_only_the_results_fragment(self):
        self.make_log(title="Hanya hasil")
        response = self.client.get(
            reverse("journal:list"), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertContains(response, "Hanya hasil")
        self.assertNotContains(response, "<html")
        self.assertNotContains(response, "Jurnal Perbaikan")

    def test_card_shows_device_guide_cost_date_and_impact(self):
        guide = RepairGuide.objects.create(
            device=self.device, author=self.other, title="Ganti baterai",
            slug="ganti-baterai", summary="s", difficulty="Easy",
            time_required_minutes=5, published=True,
        )
        self.make_log(
            title="Baterai adik", guide=guide, status=Status.SUCCEEDED,
            cost_spent=210_000, repaired_at=date(2026, 9, 20),
        )
        response = self.client.get(reverse("journal:list"))
        self.assertContains(response, "iPhone 12 · Ganti baterai")
        self.assertContains(response, "20 Sep 2026")
        self.assertContains(response, "Rp 210.000")
        self.assertContains(response, "0,2 kg limbah terhindar")

    def test_card_without_device_or_guide_has_fallback_texts(self):
        self.make_log(device=None)
        response = self.client.get(reverse("journal:list"))
        self.assertContains(response, "Perangkat tidak diisi · Tanpa panduan")

    def test_card_menu_has_status_options_edit_and_delete(self):
        log = self.make_log()
        response = self.client.get(reverse("journal:list"))
        self.assertContains(response, reverse("journal:edit", args=[log.pk]))
        self.assertContains(response, reverse("journal:delete", args=[log.pk]))
        self.assertContains(response, reverse("journal:status", args=[log.pk]))
        self.assertContains(response, 'data-set-status="succeeded"')
        self.assertNotContains(response, reverse("journal:edit", args=[self.foreign.pk]))

    def test_tiles_have_the_four_labels_from_the_design(self):
        response = self.client.get(reverse("journal:list"))
        for label in (
            "perbaikan berhasil",
            "limbah elektronik terhindar",
            "biaya ganti baru yang dihemat",
            "total catatan",
        ):
            self.assertContains(response, label)


class DetailPageTests(ViewBase):
    def guide(self):
        return RepairGuide.objects.create(
            device=self.device, author=self.other, title="Ganti baterai",
            slug="ganti-baterai", summary="s", difficulty="Easy",
            time_required_minutes=5, published=True,
        )

    def test_info_card_links_to_device_and_guide(self):
        guide = self.guide()
        log = self.make_log(
            guide=guide, cost_spent=210_000, repaired_at=date(2026, 9, 20)
        )
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, "20 Sep 2026")
        self.assertContains(response, "Rp 210.000")
        self.assertContains(response, reverse("devices:detail", args=[self.device.slug]))
        self.assertContains(response, reverse("guides:detail", args=[guide.slug]))

    def test_device_comes_from_the_guide_when_the_log_has_none(self):
        log = self.make_log(device=None, guide=self.guide())
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, reverse("devices:detail", args=[self.device.slug]))

    def test_empty_fields_show_fallback_texts(self):
        log = self.make_log(device=None)
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, "Tidak diisi")
        self.assertContains(response, "Tanpa panduan")
        self.assertContains(response, "Tidak ada catatan.")

    def test_notes_are_shown_and_escaped(self):
        log = self.make_log(notes="<b>tebal</b>")
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, "&lt;b&gt;tebal&lt;/b&gt;")

    def test_succeeded_log_shows_the_impact_panel(self):
        log = self.make_log(status=Status.SUCCEEDED, cost_spent=210_000)
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, "Dampak perbaikan ini")
        self.assertContains(response, "0,2 kg")
        self.assertContains(response, "Rp 2,8 juta")
        self.assertContains(response, "kategori Phone")
        self.assertContains(response, "dikurangi biaya perbaikanmu")
        self.assertNotContains(response, "Tandai berhasil")

    def test_panel_explains_when_default_values_were_used(self):
        CategoryImpactProfile.objects.all().delete()
        log = self.make_log(status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, "perkiraan standar")

    def test_succeeded_log_without_device_cannot_be_calculated(self):
        log = self.make_log(device=None, status=Status.SUCCEEDED)
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, "Dampak belum bisa dihitung")
        self.assertContains(response, reverse("journal:edit", args=[log.pk]))
        self.assertNotContains(response, "Dampak perbaikan ini")

    def test_unfinished_log_offers_to_mark_it_succeeded(self):
        for status in (Status.PLANNED, Status.IN_PROGRESS, Status.FAILED):
            log = self.make_log(status=status)
            response = self.client.get(reverse("journal:detail", args=[log.pk]))
            self.assertContains(response, "Dampak dihitung otomatis kalau status")
            self.assertContains(response, "Tandai berhasil")
            self.assertContains(response, reverse("journal:status", args=[log.pk]))

    def test_actions_point_to_edit_and_delete(self):
        log = self.make_log()
        response = self.client.get(reverse("journal:detail", args=[log.pk]))
        self.assertContains(response, reverse("journal:edit", args=[log.pk]))
        self.assertContains(response, reverse("journal:delete", args=[log.pk]))

    def test_marking_succeeded_returns_the_rendered_impact_box(self):
        log = self.make_log(cost_spent=210_000)
        data = self.client.post(
            reverse("journal:status", args=[log.pk]), {"status": Status.SUCCEEDED}
        ).json()
        self.assertIn("Dampak perbaikan ini", data["impact_html"])
        self.assertNotIn("Tandai berhasil", data["impact_html"])
        self.assertEqual(data["repaired_at"], short_date(date.today()))

    def test_leaving_succeeded_brings_the_button_back(self):
        log = self.make_log(status=Status.SUCCEEDED)
        data = self.client.post(
            reverse("journal:status", args=[log.pk]), {"status": Status.FAILED}
        ).json()
        self.assertIn("Tandai berhasil", data["impact_html"])


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

    def test_response_carries_rendered_badge_tiles_and_counts(self):
        data = self.client.post(self.url, {"status": Status.SUCCEEDED}).json()
        self.assertIn("badge-status--succeeded", data["badge_html"])
        self.assertIn("Berhasil", data["badge_html"])
        self.assertEqual(data["card_impact"], "0,2 kg limbah terhindar")
        self.assertEqual(data["tiles"]["succeeded"], "1")
        self.assertEqual(data["tiles"]["waste"], "0,2 kg")
        self.assertEqual(data["counts"]["succeeded"], 1)
        self.assertEqual(data["counts"]["all"], 1)

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
