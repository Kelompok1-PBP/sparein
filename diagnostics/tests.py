from django.contrib.auth.models import User
from django.http import Http404
from django.test import TestCase
from django.urls import reverse

from core.models import UserProfile
from devices.models import Device, DeviceCategory
from diagnostics.models import Cause, DiagnosisSession, Symptom
from diagnostics.selectors import (
    get_symptom_or_404,
    get_symptom_qs,
    get_symptoms_for_device,
)
from diagnostics.services import rank_causes, save_session


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


class SelectorTests(TestCase):
    def setUp(self):
        self.d1 = make_device("iPhone 11")
        self.d2 = make_device("iPhone 12")
        Symptom.objects.create(device=self.d1, title="Panas", severity="low")
        Symptom.objects.create(device=self.d1, title="Mati total", severity="high")
        Symptom.objects.create(device=self.d2, title="Speaker pecah")

    def test_symptoms_for_device(self):
        titles = [s.title for s in get_symptoms_for_device(self.d1.pk)]
        self.assertEqual(titles, ["Mati total", "Panas"])

    def test_qs_filters_by_device_slug_and_severity(self):
        self.assertEqual(get_symptom_qs().count(), 3)
        self.assertEqual(get_symptom_qs(device="iphone-12").count(), 1)
        self.assertEqual(get_symptom_qs(device=self.d1.slug, severity="high").count(), 1)

    def test_get_or_404(self):
        self.assertEqual(get_symptom_or_404("panas").title, "Panas")
        with self.assertRaises(Http404):
            get_symptom_or_404("nope")


class RankCausesTests(TestCase):
    def setUp(self):
        self.device = make_device()
        self.s1, self.s2, self.s3, self.s4 = (
            Symptom.objects.create(device=self.device, title=t) for t in ("a", "b", "c", "d")
        )
        self.aus = Cause.objects.create(device=self.device, title="Baterai aus", note="Umum")
        self.aus.symptoms.add(self.s1, self.s2)
        self.boros = Cause.objects.create(device=self.device, title="Aplikasi boros")
        self.boros.symptoms.add(self.s2, self.s3, self.s4)

    def rank(self, *symptoms, device=None):
        return rank_causes((device or self.device).pk, [s.pk for s in symptoms])

    def test_nothing_ticked_returns_nothing(self):
        self.assertEqual(self.rank(), [])

    def test_full_match_ranks_first_as_high(self):
        ranked = self.rank(self.s1, self.s2)
        self.assertEqual([(r["cause"], r["likelihood"]) for r in ranked],
                         [(self.aus, "high"), (self.boros, "medium")])

    def test_one_of_three_is_medium_and_one_of_four_is_low(self):
        self.boros.symptoms.add(Symptom.objects.create(device=self.device, title="e"))
        ranked = self.rank(self.s3)
        self.assertEqual([r["likelihood"] for r in ranked], ["low"])

    def test_cause_without_match_is_left_out(self):
        self.assertEqual([r["cause"] for r in self.rank(self.s1)], [self.aus])

    def test_ties_break_by_matched_count_then_title(self):
        ranked = self.rank(self.s2, self.s3, self.s4)
        self.assertEqual(ranked[0]["cause"], self.boros)

    def test_other_device_causes_are_ignored(self):
        other = make_device("iPhone 12")
        self.assertEqual(self.rank(self.s1, device=other), [])

    def test_result_carries_label(self):
        self.assertEqual(self.rank(self.s1, self.s2)[0]["likelihood_label"], "Tinggi")

    def test_result_carries_note(self):
        self.assertEqual(self.rank(self.s1, self.s2)[0]["note"], "Umum")


def make_user(name, role=UserProfile.Role.MEMBER):
    user = User.objects.create_user(name, password="Sparein!2026")
    user.profile.role = role
    user.profile.save()
    return user


class DiagnoseSetup(TestCase):
    def setUp(self):
        self.device = make_device()
        self.panas = Symptom.objects.create(device=self.device, title="HP panas", severity="low")
        self.boros = Symptom.objects.create(device=self.device, title="Baterai boros")
        self.aus = Cause.objects.create(device=self.device, title="Baterai sudah aus", note="Umum")
        self.aus.symptoms.add(self.boros)


class DiagnosePageTests(DiagnoseSetup):
    url = reverse("diagnostics:list")

    def test_without_device_asks_to_pick_one(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "Perangkat apa yang bermasalah?")
        self.assertContains(resp, reverse("devices:api"))

    def test_with_device_lists_its_symptoms(self):
        resp = self.client.get(self.url, {"device": self.device.slug})
        self.assertContains(resp, "HP panas")
        self.assertContains(resp, "Baterai boros")
        self.assertContains(resp, "Centang gejala")

    def test_unknown_device_is_404(self):
        self.assertEqual(self.client.get(self.url, {"device": "nope"}).status_code, 404)

    def test_device_without_symptoms_shows_empty_state(self):
        other = make_device("iPhone 12")
        resp = self.client.get(self.url, {"device": other.slug})
        self.assertContains(resp, "Belum ada gejala yang dicatat buat iPhone 12.")

    def test_ticked_symptom_renders_ranked_result_without_js(self):
        resp = self.client.get(self.url, {"device": self.device.slug, "symptom": [self.boros.pk]})
        self.assertContains(resp, "Baterai sudah aus")
        self.assertContains(resp, "1 kemungkinan ditemukan")
        self.assertContains(resp, "Kemungkinan tinggi")
        self.assertContains(resp, "checked")

    def test_page_wires_script_and_save_button(self):
        resp = self.client.get(self.url, {"device": self.device.slug})
        self.assertContains(resp, "diagnostics/diagnostics.js")
        self.assertContains(resp, f'data-api="{reverse("diagnostics:save")}"')
        self.assertContains(resp, "csrfmiddlewaretoken")

    def test_picker_state_also_loads_script(self):
        self.assertContains(self.client.get(self.url), "diagnostics/diagnostics.js")

    def test_garbage_symptom_param_is_ignored(self):
        resp = self.client.get(self.url, {"device": self.device.slug, "symptom": ["abc", ""]})
        self.assertEqual(resp.status_code, 200)

    def test_add_symptom_link_only_for_contributor(self):
        params = {"device": self.device.slug}
        self.assertNotContains(self.client.get(self.url, params), "Tambah gejala")
        self.client.force_login(make_user("c", UserProfile.Role.CONTRIBUTOR))
        self.assertContains(self.client.get(self.url, params), "Tambah gejala")


class SymptomDetailTests(DiagnoseSetup):
    def test_visitor_reads_detail(self):
        resp = self.client.get(reverse("diagnostics:detail", args=[self.panas.slug]))
        self.assertContains(resp, "HP panas")
        self.assertContains(resp, "Ringan")
        self.assertContains(resp, self.device.name)

    def test_unknown_slug_is_404(self):
        self.assertEqual(self.client.get(reverse("diagnostics:detail", args=["nope"])).status_code, 404)


class ApiTests(DiagnoseSetup):
    def test_symptoms_result_shape(self):
        item = self.client.get(reverse("diagnostics:api-symptoms")).json()["results"][0]
        self.assertEqual(set(item), {"id", "title", "slug", "description", "severity", "device", "url"})

    def test_symptoms_filter_by_severity(self):
        data = self.client.get(reverse("diagnostics:api-symptoms"), {"severity": "low"}).json()
        self.assertEqual([r["title"] for r in data["results"]], ["HP panas"])

    def test_symptoms_filter_by_device(self):
        other = make_device("iPhone 12")
        Symptom.objects.create(device=other, title="Speaker pecah")
        data = self.client.get(reverse("diagnostics:api-symptoms"), {"device": other.slug}).json()
        self.assertEqual([r["title"] for r in data["results"]], ["Speaker pecah"])

    def test_diagnose_returns_ranked_results_without_saving(self):
        resp = self.client.get(reverse("diagnostics:api-diagnose"),
                               {"device": self.device.slug, "symptom": [self.boros.pk]})
        data = resp.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["title"], "Baterai sudah aus")
        self.assertEqual(data["results"][0]["likelihood"], "high")
        self.assertEqual(data["results"][0]["likelihood_label"], "Tinggi")
        self.assertFalse(DiagnosisSession.objects.exists())

    def test_diagnose_unknown_device_is_404(self):
        self.assertEqual(self.client.get(reverse("diagnostics:api-diagnose"), {"device": "x"}).status_code, 404)


class SymptomWriteTests(DiagnoseSetup):
    def payload(self, **extra):
        data = {"device": self.device.pk, "title": "Speaker pecah",
                "description": "Suara kecil", "severity": "low"}
        return {**data, **extra}

    def test_visitor_is_sent_to_login(self):
        resp = self.client.get(reverse("diagnostics:create"))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('diagnostics:create')}")

    def test_member_gets_403(self):
        self.client.force_login(make_user("m"))
        self.assertEqual(self.client.get(reverse("diagnostics:create")).status_code, 403)

    def test_contributor_creates_and_becomes_owner(self):
        user = make_user("c", UserProfile.Role.CONTRIBUTOR)
        self.client.force_login(user)
        resp = self.client.post(reverse("diagnostics:create"), self.payload())
        symptom = Symptom.objects.get(title="Speaker pecah")
        self.assertRedirects(resp, reverse("diagnostics:detail", args=[symptom.slug]))
        self.assertEqual(symptom.created_by, user)

    def test_create_form_preselects_device_from_query(self):
        self.client.force_login(make_user("c", UserProfile.Role.CONTRIBUTOR))
        resp = self.client.get(reverse("diagnostics:create"), {"device": self.device.slug})
        self.assertEqual(resp.context["form"].initial["device"], self.device)

    def test_invalid_post_shows_errors_and_saves_nothing(self):
        self.client.force_login(make_user("c", UserProfile.Role.CONTRIBUTOR))
        resp = self.client.post(reverse("diagnostics:create"), self.payload(title=""))
        self.assertContains(resp, "field__msg--error")
        self.assertEqual(Symptom.objects.count(), 2)

    def test_invalid_post_shows_error_summary_and_marks_field(self):
        self.client.force_login(make_user("c", UserProfile.Role.CONTRIBUTOR))
        resp = self.client.post(reverse("diagnostics:create"), self.payload(title=""))
        self.assertContains(resp, "Ada 1 isian yang perlu dibenerin.")
        self.assertContains(resp, 'aria-invalid="true"')

    def test_form_has_breadcrumb_back_to_diagnose(self):
        self.client.force_login(make_user("c", UserProfile.Role.CONTRIBUTOR))
        resp = self.client.get(reverse("diagnostics:create"))
        self.assertContains(resp, 'aria-label="Breadcrumb"')

    def test_owner_edits_and_slug_stays(self):
        owner = make_user("owner", UserProfile.Role.CONTRIBUTOR)
        self.panas.created_by = owner
        self.panas.save()
        self.client.force_login(owner)
        url = reverse("diagnostics:edit", args=[self.panas.slug])
        self.client.post(url, self.payload(title="HP terlalu panas"))
        self.panas.refresh_from_db()
        self.assertEqual((self.panas.title, self.panas.slug), ("HP terlalu panas", "hp-panas"))

    def test_other_contributor_cannot_edit_but_admin_can(self):
        url = reverse("diagnostics:edit", args=[self.panas.slug])
        self.client.force_login(make_user("other", UserProfile.Role.CONTRIBUTOR))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(make_user("adm", UserProfile.Role.ADMIN))
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_delete_is_admin_only_and_post_only(self):
        url = reverse("diagnostics:delete", args=[self.panas.slug])
        owner = make_user("owner", UserProfile.Role.CONTRIBUTOR)
        self.panas.created_by = owner
        self.panas.save()
        self.client.force_login(owner)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(make_user("adm", UserProfile.Role.ADMIN))
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Symptom.objects.filter(pk=self.panas.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("diagnostics:list"))
        self.assertFalse(Symptom.objects.filter(pk=self.panas.pk).exists())

    def test_detail_buttons_follow_role(self):
        url = reverse("diagnostics:detail", args=[self.panas.slug])
        self.assertNotContains(self.client.get(url), "Ubah")
        owner = make_user("owner", UserProfile.Role.CONTRIBUTOR)
        self.panas.created_by = owner
        self.panas.save()
        self.client.force_login(owner)
        resp = self.client.get(url)
        self.assertContains(resp, "Ubah")
        self.assertNotContains(resp, "Hapus")
        self.client.force_login(make_user("adm", UserProfile.Role.ADMIN))
        self.assertContains(self.client.get(url), "Hapus")


class SaveSessionTests(DiagnoseSetup):
    url = reverse("diagnostics:save")

    def post(self, **extra):
        data = {"device": self.device.slug, "symptom": [self.boros.pk], **extra}
        return self.client.post(self.url, data)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_anonymous_session_is_saved_with_results(self):
        resp = self.post()
        session = DiagnosisSession.objects.get()
        self.assertEqual(resp.json(), {"saved": True, "id": session.pk})
        self.assertIsNone(session.user)
        self.assertEqual(list(session.symptoms.all()), [self.boros])
        result = session.results.get()
        self.assertEqual((result.cause, result.likelihood, result.note), (self.aus, "high", "Umum"))

    def test_member_session_belongs_to_user(self):
        user = make_user("m")
        self.client.force_login(user)
        self.post()
        self.assertEqual(DiagnosisSession.objects.get().user, user)

    def test_without_symptoms_is_rejected(self):
        resp = self.client.post(self.url, {"device": self.device.slug})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(DiagnosisSession.objects.exists())

    def test_symptoms_of_other_device_are_ignored(self):
        foreign = Symptom.objects.create(device=make_device("iPhone 12"), title="Asing")
        resp = self.client.post(self.url, {"device": self.device.slug, "symptom": [foreign.pk]})
        self.assertEqual(resp.status_code, 400)

    def test_unknown_device_is_404(self):
        self.assertEqual(self.client.post(self.url, {"device": "nope", "symptom": [1]}).status_code, 404)


class SeedFixtureTests(TestCase):
    fixtures = ["seed_devices", "seed_diagnostics"]

    def test_seed_gives_a_working_diagnosis(self):
        device = Device.objects.get(pk=8)
        ids = list(get_symptoms_for_device(device.pk).values_list("pk", flat=True)[:1])
        self.assertTrue(rank_causes(device.pk, ids))


class CategoryTilesTests(TestCase):
    def setUp(self):
        phone = DeviceCategory.objects.create(name="Phone")
        laptop = DeviceCategory.objects.create(name="Laptop")
        for name in ("iPhone 11", "iPhone 12"):
            Device.objects.create(name=name, category=phone)
        Device.objects.create(name="MacBook", category=laptop)

    def test_picker_lists_categories_with_device_count(self):
        resp = self.client.get(reverse("diagnostics:list"))
        self.assertContains(resp, "Atau pilih dari kategori")
        self.assertContains(resp, "2 perangkat")
        self.assertContains(resp, "1 perangkat")
        self.assertContains(resp, f'{reverse("devices:list")}?category=phone')

    def test_tiles_hidden_once_device_is_chosen(self):
        resp = self.client.get(reverse("diagnostics:list"), {"device": "iphone-11"})
        self.assertNotContains(resp, "Atau pilih dari kategori")


class DeviceSelectFilterTests(DiagnoseSetup):
    def test_form_has_search_box_for_device_select_and_script(self):
        self.client.force_login(make_user("c", UserProfile.Role.CONTRIBUTOR))
        resp = self.client.get(reverse("diagnostics:create"))
        self.assertContains(resp, 'data-filter-for="id_device"')
        self.assertContains(resp, "diagnostics/diagnostics.js")


class ResultBarTests(DiagnoseSetup):
    url = reverse("diagnostics:list")

    def test_bar_shows_count_when_something_is_ticked(self):
        resp = self.client.get(self.url, {"device": self.device.slug, "symptom": [self.boros.pk]})
        self.assertContains(resp, '<a class="result-bar" href="#results-title">1 kemungkinan ditemukan')

    def test_bar_hidden_when_nothing_is_ticked(self):
        resp = self.client.get(self.url, {"device": self.device.slug})
        self.assertContains(resp, 'class="result-bar" href="#results-title" hidden')


class HistoryTests(DiagnoseSetup):
    url = reverse("diagnostics:history")

    def save_for(self, user):
        return save_session(user, self.device, [self.boros.pk])

    def test_visitor_is_sent_to_login(self):
        self.assertRedirects(self.client.get(self.url), f"{reverse('login')}?next={self.url}")

    def test_member_sees_only_own_sessions(self):
        me, other = make_user("me"), make_user("other")
        self.save_for(me)
        Cause.objects.create(device=self.device, title="Rahasia orang lain").symptoms.add(self.panas)
        save_session(other, self.device, [self.panas.pk])
        self.client.force_login(me)
        resp = self.client.get(self.url)
        self.assertContains(resp, "Baterai sudah aus")
        self.assertContains(resp, "Baterai boros")
        self.assertNotContains(resp, "Rahasia orang lain")

    def test_rerun_link_restores_ticked_symptoms(self):
        me = make_user("me")
        self.save_for(me)
        self.client.force_login(me)
        resp = self.client.get(self.url)
        self.assertContains(resp, f"?device={self.device.slug}&amp;symptom={self.boros.pk}")

    def test_empty_state(self):
        self.client.force_login(make_user("me"))
        self.assertContains(self.client.get(self.url), "Belum ada riwayat diagnosa.")

    def test_diagnose_page_links_to_history_only_when_logged_in(self):
        page = reverse("diagnostics:list")
        self.assertNotContains(self.client.get(page), "Riwayat diagnosa")
        self.client.force_login(make_user("me"))
        self.assertContains(self.client.get(page), "Riwayat diagnosa")
