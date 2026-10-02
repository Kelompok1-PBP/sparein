from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from requests import Timeout

from core.models import UserProfile
from devices.models import Device, DeviceCategory

from .ifixit import ImportFailure, fetch_guide, import_guide
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
