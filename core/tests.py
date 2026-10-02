from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from core.models import UserProfile
from core.permissions import is_admin, is_contributor, is_member


class ProfileTests(TestCase):
    def test_new_user_gets_member_profile(self):
        user = User.objects.create_user("budi", password="x")
        self.assertEqual(user.profile.role, UserProfile.Role.MEMBER)


class PermissionTests(TestCase):
    def make(self, role):
        user = User.objects.create_user(role.lower(), password="x")
        user.profile.role = role
        user.profile.save()
        return user

    def test_anonymous_is_not_member(self):
        self.assertFalse(is_member(AnonymousUser()))

    def test_logged_in_is_member(self):
        self.assertTrue(is_member(self.make(UserProfile.Role.MEMBER)))

    def test_member_is_not_contributor(self):
        self.assertFalse(is_contributor(self.make(UserProfile.Role.MEMBER)))

    def test_contributor_passes(self):
        self.assertTrue(is_contributor(self.make(UserProfile.Role.CONTRIBUTOR)))

    def test_admin_passes_every_check(self):
        user = self.make(UserProfile.Role.ADMIN)
        self.assertTrue(is_member(user) and is_contributor(user) and is_admin(user))

    def test_superuser_counts_as_admin(self):
        self.assertTrue(is_admin(User.objects.create_superuser("root", password="x")))

    def test_contributor_is_not_admin(self):
        self.assertFalse(is_admin(self.make(UserProfile.Role.CONTRIBUTOR)))


class PageTests(TestCase):
    def test_home_renders(self):
        self.assertContains(self.client.get(reverse("core:home")), "Sparein")

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_logout_rejects_get(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

    def test_register_creates_member_and_logs_in(self):
        resp = self.client.post(reverse("core:register"), {
            "username": "sari", "password1": "Sparein!2026", "password2": "Sparein!2026"})
        self.assertRedirects(resp, reverse("core:home"))
        self.assertEqual(User.objects.get(username="sari").profile.role, UserProfile.Role.MEMBER)
