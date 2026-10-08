from django.http import Http404
from django.test import TestCase

from devices.models import Device, DeviceCategory
from diagnostics.models import Cause, Symptom
from diagnostics.selectors import (
    get_symptom_or_404,
    get_symptom_qs,
    get_symptoms_for_device,
)
from diagnostics.services import rank_causes


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

    def test_result_carries_note(self):
        self.assertEqual(self.rank(self.s1, self.s2)[0]["note"], "Umum")
