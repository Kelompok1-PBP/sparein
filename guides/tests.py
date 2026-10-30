from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from requests import Timeout

from core.models import UserProfile
from devices.models import Device, DeviceCategory

from .ifixit import ImportFailure, fetch_guide, import_guide
from .labels import difficulty_label, difficulty_tone, duration_label
from .models import GuideStep, RepairGuide, SafetyWarning


class GuideTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            "writer", password="test-pass-123"
        )
        self.author.profile.role = UserProfile.Role.CONTRIBUTOR
        self.author.profile.save()
        self.other = get_user_model().objects.create_user("other")
        self.category = DeviceCategory.objects.create(name="Laptop")
        self.device = Device.objects.create(name="Test laptop", category=self.category)
        self.guide = RepairGuide.objects.create(
            device=self.device,
            author=self.author,
            title="Test repair",
            slug="test-repair",
            summary="Summary",
            difficulty="Easy",
            time_required_minutes=10,
            published=True,
        )
        self.step = GuideStep.objects.create(
            guide=self.guide, order=1, title="Step", detail="PRIVATE STEP TEXT"
        )
        SafetyWarning.objects.create(
            guide=self.guide, level="danger", message="PUBLIC WARNING"
        )

    def payload(self):
        return {
            "device": self.device.pk,
            "title": "New repair",
            "summary": "Summary",
            "difficulty": "Easy",
            "time_required_minutes": 15,
            "tools": "Cloth",
            "published": "on",
            "steps-TOTAL_FORMS": 1,
            "steps-INITIAL_FORMS": 0,
            "steps-0-order": 1,
            "steps-0-title": "Start",
            "steps-0-detail": "Do it",
            "warnings-TOTAL_FORMS": 0,
            "warnings-INITIAL_FORMS": 0,
        }

    def test_visitor_html_and_json_hide_detail_keep_warnings(self):
        response = self.client.get("/guides/test-repair/")
        self.assertContains(response, "PUBLIC WARNING")
        self.assertNotContains(response, "PRIVATE STEP TEXT")
        response = self.client.get("/api/guides/")
        self.assertNotContains(response, "PRIVATE STEP TEXT")
        self.assertNotIn("detail", response.json()["results"][0]["steps"][0])
        self.assertContains(response, "PUBLIC WARNING")

    def test_visitor_queries_exclude_step_detail(self):
        for url in ("/guides/test-repair/", "/api/guides/"):
            with self.subTest(url=url):
                with CaptureQueriesContext(connection) as queries:
                    response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                step_queries = [
                    query["sql"]
                    for query in queries.captured_queries
                    if GuideStep._meta.db_table in query["sql"]
                    and query["sql"].lstrip().upper().startswith("SELECT")
                ]
                # Require a real step read so an empty response cannot pass.
                self.assertTrue(step_queries, "Expected a query for guide steps")
                for sql in step_queries:
                    projection = sql.upper().split(" FROM ", 1)[0]
                    self.assertNotIn('"DETAIL"', projection, sql)
                    self.assertNotIn("*", projection, sql)

    def test_member_reads_but_cannot_write(self):
        self.client.force_login(self.other)
        self.assertContains(
            self.client.get("/guides/test-repair/"), "PRIVATE STEP TEXT"
        )
        self.assertEqual(
            self.client.post("/guides/create/", self.payload()).status_code, 403
        )
        self.assertEqual(
            self.client.post("/guides/test-repair/edit/", self.payload()).status_code,
            403,
        )
        self.assertEqual(
            self.client.post("/guides/test-repair/delete/").status_code, 403
        )

    def test_create_edit_delete_json(self):
        self.client.force_login(self.author)
        response = self.client.post(
            "/guides/create/", self.payload(), HTTP_ACCEPT="application/json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        guide = RepairGuide.objects.get(pk=response.json()["id"])
        payload = self.payload()
        payload.update(
            {
                "title": "Changed",
                "steps-INITIAL_FORMS": 1,
                "steps-0-id": guide.steps.get().pk,
            }
        )
        self.assertEqual(
            self.client.post(
                f"/guides/{guide.slug}/edit/", payload, HTTP_ACCEPT="application/json"
            ).status_code,
            200,
        )
        guide.refresh_from_db()
        self.assertEqual(guide.title, "Changed")
        self.assertEqual(guide.steps.count(), 1)
        self.assertEqual(
            self.client.get(f"/guides/{guide.slug}/delete/").status_code, 200
        )
        self.assertTrue(RepairGuide.objects.filter(pk=guide.pk).exists())
        self.assertEqual(
            self.client.post(
                f"/guides/{guide.slug}/delete/", HTTP_ACCEPT="application/json"
            ).status_code,
            200,
        )
        self.assertFalse(RepairGuide.objects.filter(pk=guide.pk).exists())

    def test_invalid_input_atomic(self):
        self.client.force_login(self.author)
        payload = self.payload()
        payload["steps-0-detail"] = ""
        self.assertEqual(self.client.post("/guides/create/", payload).status_code, 400)
        self.assertEqual(RepairGuide.objects.count(), 1)

    def test_draft_visibility_and_filters(self):
        self.assertEqual(
            len(self.client.get("/api/guides/?max_time=5").json()["results"]), 0
        )
        self.assertEqual(self.client.get("/api/guides/?device=bad").status_code, 400)
        self.guide.published = False
        self.guide.save()
        self.assertEqual(self.client.get("/guides/test-repair/").status_code, 404)
        self.assertEqual(self.client.get("/api/guides/").json()["results"], [])
        self.client.force_login(self.author)
        self.assertEqual(self.client.get("/guides/test-repair/").status_code, 200)

    def test_admin_can_manage_other_author(self):
        self.other.profile.role = UserProfile.Role.ADMIN
        self.other.profile.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/guides/test-repair/edit/").status_code, 200)
        self.assertEqual(
            self.client.post("/guides/test-repair/delete/").status_code, 302
        )

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.author)
        self.assertEqual(client.post("/guides/test-repair/delete/").status_code, 403)

    def test_contributor_cannot_edit_others(self):
        self.other.profile.role = UserProfile.Role.CONTRIBUTOR
        self.other.profile.save()
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post("/guides/test-repair/edit/", self.payload()).status_code,
            403,
        )

    def source(self):
        return {
            "guideid": 345,
            "title": "External guide",
            "difficulty": "Moderate",
            "time_required_max": 1800,
            "summary": "<p>Summary</p>",
            "author": {"username": "Source Author"},
            "steps": [
                {
                    "title": "Start",
                    "lines": [{"text_rendered": "<b>Warning</b>", "bullet": "caution"}],
                }
            ],
            "tools": [{"text": "Cloth"}],
        }

    def test_import_draft_attribution_and_duplicate(self):
        guide = import_guide(self.source(), device=self.device, author=self.author)
        self.assertFalse(guide.published)
        self.assertEqual(guide.source_author, "Source Author")
        self.assertEqual(guide.time_required_minutes, 30)
        self.assertEqual(guide.steps.get().detail, "Warning")
        self.assertEqual(guide.warnings.count(), 2)
        with self.assertRaises(ImportFailure):
            import_guide(self.source(), device=self.device, author=self.author)

    def test_failed_import_rolls_back(self):
        source = self.source()
        source["steps"][0]["lines"] = []
        with self.assertRaises(ImportFailure):
            import_guide(source, device=self.device, author=self.author)
        self.assertEqual(RepairGuide.objects.count(), 1)

    @patch("guides.ifixit.requests.get")
    def test_api_cache_and_failure(self, get):
        cache.clear()
        get.return_value.json.return_value = self.source()
        self.assertEqual(fetch_guide(345)["guideid"], 345)
        fetch_guide(345)
        self.assertEqual(get.call_count, 1)
        cache.clear()
        get.side_effect = Timeout()
        with self.assertRaises(ImportFailure):
            fetch_guide(345)

    @patch("guides.ifixit.fetch_guide")
    def test_import_view(self, fetch):
        fetch.return_value = self.source()
        self.assertEqual(self.client.post("/guides/import/").status_code, 403)
        self.client.force_login(self.author)
        self.assertEqual(self.client.get("/guides/import/").status_code, 200)
        response = self.client.post(
            "/guides/import/", {"guide_id": 345, "device": self.device.pk}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RepairGuide.objects.count(), 2)


class LabelTests(TestCase):
    def test_difficulty_labels_and_tones(self):
        self.assertEqual(difficulty_label("Very easy"), "Sangat mudah")
        self.assertEqual(difficulty_tone("Very difficult"), "hard")
        self.assertEqual(difficulty_tone("Easy"), "easy")

    def test_unknown_difficulty_falls_back(self):
        self.assertEqual(difficulty_label("Aneh"), "Aneh")
        self.assertEqual(difficulty_tone("Aneh"), "moderate")

    def test_duration_label(self):
        self.assertEqual(duration_label(45), "45 menit")
        self.assertEqual(duration_label(60), "1 jam")
        self.assertEqual(duration_label(75), "1 jam 15 menit")
        self.assertEqual(duration_label(120), "2 jam")


class ApiDisplayFieldsTests(TestCase):
    def test_api_carries_display_fields_for_cards(self):
        user = get_user_model().objects.create_user("penulis", password="x")
        device = Device.objects.create(
            name="iPhone 11",
            category=DeviceCategory.objects.create(name="Phone"),
            image_url="https://example.com/a.jpg",
        )
        guide = RepairGuide.objects.create(
            title="Ganti baterai", slug="ganti-baterai", summary="x", difficulty="Moderate",
            time_required_minutes=75, device=device, author=user, published=True,
        )
        GuideStep.objects.create(guide=guide, order=1, title="Buka", detail="x")
        item = Client().get("/api/guides/").json()["results"][0]
        self.assertEqual(item["difficulty_label"], "Sedang")
        self.assertEqual(item["difficulty_tone"], "moderate")
        self.assertEqual(item["duration_label"], "1 jam 15 menit")
        self.assertEqual(item["step_total"], 1)
        self.assertEqual(item["device_image_url"], "https://example.com/a.jpg")


class ListPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user("penulis", password="x")
        cls.phone = Device.objects.create(
            name="iPhone 11", category=DeviceCategory.objects.create(name="Phone")
        )
        cls.guide = RepairGuide.objects.create(
            title="Ganti baterai", slug="ganti-baterai", summary="x", difficulty="Easy",
            time_required_minutes=45, device=cls.phone, author=user, published=True,
        )
        GuideStep.objects.create(guide=cls.guide, order=1, title="Buka", detail="x")

    def test_card_shows_label_duration_and_step_count(self):
        resp = Client().get("/guides/")
        self.assertContains(resp, "difficulty--easy")
        self.assertContains(resp, ">Mudah<")
        self.assertContains(resp, "45 menit")
        self.assertContains(resp, "1 langkah")

    def test_filters_offer_every_difficulty_and_time_preset(self):
        resp = Client().get("/guides/")
        for text in ("Sangat mudah", "Sangat sulit", "30 menit", "1 jam", "2 jam", "Reset filter"):
            self.assertContains(resp, text)

    def test_active_filters_become_removable_chips(self):
        resp = Client().get(f"/guides/?difficulty=Easy&max_time=60&device={self.phone.pk}")
        self.assertContains(resp, "Kesulitan: Mudah")
        self.assertContains(resp, "Waktu: ≤ 1 jam")
        self.assertContains(resp, "Perangkat: iPhone 11")
        self.assertContains(resp, f'href="?max_time=60&amp;device={self.phone.pk}"')

    def test_garbage_filter_values_do_not_break_chips(self):
        resp = Client().get("/guides/?max_time=abc&device=xyz")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'class="filter-chip"')

    def test_empty_result_shows_empty_state(self):
        self.assertContains(Client().get("/guides/?difficulty=Difficult"), "Belum ada panduan yang cocok")


class DetailPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user("penulis", password="x")
        cls.author.profile.role = UserProfile.Role.CONTRIBUTOR
        cls.author.profile.save()
        cls.device = Device.objects.create(
            name="iPhone 11", brand="Apple", category=DeviceCategory.objects.create(name="Phone")
        )
        cls.guide = RepairGuide.objects.create(
            title="Ganti baterai", slug="ganti-baterai", summary="Ringkas", difficulty="Moderate",
            time_required_minutes=45, device=cls.device, author=cls.author, published=True,
            tools="Obeng P2\nSpudger",
        )
        GuideStep.objects.create(guide=cls.guide, order=1, title="Buka sekrup", detail="Lepas dua sekrup")
        SafetyWarning.objects.create(guide=cls.guide, level="danger", message="Jangan tusuk baterai")
        SafetyWarning.objects.create(guide=cls.guide, level="caution", message="Cabut charger")

    def test_header_shows_meta_and_author(self):
        resp = Client().get("/guides/ganti-baterai/")
        self.assertContains(resp, "difficulty--moderate")
        self.assertContains(resp, "45 menit")
        self.assertContains(resp, "1 langkah")
        self.assertContains(resp, "oleh penulis")

    def test_warnings_use_level_classes_and_labels(self):
        resp = Client().get("/guides/ganti-baterai/")
        self.assertContains(resp, "safety--danger")
        self.assertContains(resp, "safety--caution")
        self.assertContains(resp, "Bahaya")

    def test_sidebar_lists_tools_device_and_parts_link(self):
        resp = Client().get("/guides/ganti-baterai/")
        self.assertContains(resp, "<li>Obeng P2</li>", html=True)
        self.assertContains(resp, f"/parts/?device={self.device.slug}")
        self.assertContains(resp, "Apple")

    def test_visitor_sees_step_titles_but_not_journal_button(self):
        resp = Client().get("/guides/ganti-baterai/")
        self.assertContains(resp, "Buka sekrup")
        self.assertNotContains(resp, "Lepas dua sekrup")
        self.assertNotContains(resp, "Catat perbaikan ini")

    def test_member_gets_journal_shortcut_with_guide_prefilled(self):
        client = Client()
        client.force_login(get_user_model().objects.create_user("anggota", password="x"))
        resp = client.get("/guides/ganti-baterai/")
        self.assertContains(resp, "Lepas dua sekrup")
        self.assertContains(resp, "/journal/create/?guide=ganti-baterai")

    def test_owner_sees_edit_and_delete(self):
        client = Client()
        client.force_login(self.author)
        resp = client.get("/guides/ganti-baterai/")
        self.assertContains(resp, "/guides/ganti-baterai/edit/")
        self.assertContains(resp, "/guides/ganti-baterai/delete/")


class FormPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user("penulis", password="x")
        cls.author.profile.role = UserProfile.Role.CONTRIBUTOR
        cls.author.profile.save()

    def setUp(self):
        self.client.force_login(self.author)

    def test_create_page_has_three_sections_with_indonesian_labels(self):
        resp = self.client.get("/guides/create/")
        for text in ("1. Info dasar", "2. Peringatan keselamatan", "3. Langkah-langkah",
                     "Judul panduan", "Perkiraan waktu", "Judul langkah", "Terbitkan sekarang"):
            self.assertContains(resp, text)

    def test_new_step_row_gets_its_position_as_order(self):
        resp = self.client.get("/guides/create/")
        self.assertContains(resp, 'name="steps-0-order" value="1"')

    def test_inputs_carry_shared_input_class(self):
        self.assertContains(self.client.get("/guides/create/"), 'class="input"')

    def test_invalid_post_shows_error_summary_and_marks_field(self):
        resp = self.client.post("/guides/create/", {
            "steps-TOTAL_FORMS": 1, "steps-INITIAL_FORMS": 0,
            "warnings-TOTAL_FORMS": 0, "warnings-INITIAL_FORMS": 0,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, "Ada isian yang belum benar", status_code=400)
        self.assertContains(resp, 'aria-invalid="true"', status_code=400)

    def test_edit_page_title_and_breadcrumb(self):
        device = Device.objects.create(name="iPhone", category=DeviceCategory.objects.create(name="Phone"))
        guide = RepairGuide.objects.create(
            title="Ganti", slug="ganti", summary="x", difficulty="Easy", time_required_minutes=5,
            device=device, author=self.author, published=True,
        )
        GuideStep.objects.create(guide=guide, order=1, title="Buka", detail="x")
        resp = self.client.get("/guides/ganti/edit/")
        self.assertContains(resp, "Ubah panduan")
        self.assertContains(resp, "Buka")


class DeleteAndImportPageTests(TestCase):
    def test_delete_page_uses_confirm_dialog(self):
        admin = get_user_model().objects.create_user("adm", password="x")
        admin.profile.role = UserProfile.Role.ADMIN
        admin.profile.save()
        device = Device.objects.create(name="iPhone", category=DeviceCategory.objects.create(name="Phone"))
        RepairGuide.objects.create(
            title="Ganti", slug="ganti", summary="x", difficulty="Easy", time_required_minutes=5,
            device=device, author=admin, published=True,
        )
        self.client.force_login(admin)
        resp = self.client.get("/guides/ganti/delete/")
        self.assertContains(resp, "confirm__icon")
        self.assertContains(resp, "Hapus &quot;Ganti&quot;?")

    def test_import_page_labels_and_breadcrumb(self):
        user = get_user_model().objects.create_user("penulis", password="x")
        user.profile.role = UserProfile.Role.CONTRIBUTOR
        user.profile.save()
        self.client.force_login(user)
        resp = self.client.get("/guides/import/")
        self.assertContains(resp, "ID panduan iFixit")
        self.assertContains(resp, "Impor sebagai draf")
        self.assertContains(resp, 'aria-current="page"')
