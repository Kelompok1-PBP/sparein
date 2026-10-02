from django.contrib.auth.models import AnonymousUser, User
from django.contrib.staticfiles import finders
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


class AuthPageTests(TestCase):
    def test_login_uses_auth_layout_without_site_chrome(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, "Masuk ke Sparein")
        self.assertContains(resp, "auth--login")
        self.assertNotContains(resp, "<footer")

    def test_login_with_next_shows_info_and_keeps_next(self):
        resp = self.client.get(reverse("login"), {"next": "/devices/create/"})
        self.assertContains(resp, "Masuk dulu ya buat lanjut.")
        self.assertContains(resp, 'name="next" value="/devices/create/"')

    def test_login_without_next_has_no_info(self):
        resp = self.client.get(reverse("login"))
        self.assertNotContains(resp, "Masuk dulu ya buat lanjut.")

    def test_wrong_password_shows_message_and_never_echoes_password(self):
        User.objects.create_user("sari", password="Sparein!2026")
        resp = self.client.post(reverse("login"), {"username": "sari", "password": "salah-banget"})
        self.assertContains(resp, "Username atau password salah. Coba cek lagi ya.")
        self.assertContains(resp, 'value="sari"')
        self.assertNotContains(resp, "salah-banget")

    def test_login_links_to_register(self):
        self.assertContains(self.client.get(reverse("login")), reverse("core:register"))

    def test_register_has_three_fields_and_no_email(self):
        resp = self.client.get(reverse("core:register"))
        self.assertContains(resp, "auth--register")
        for name in ("username", "password1", "password2"):
            self.assertContains(resp, f'name="{name}"')
        self.assertNotContains(resp, 'name="email"')

    def test_register_links_to_login(self):
        self.assertContains(self.client.get(reverse("core:register")), reverse("login"))

    def test_register_taken_username_marks_field_invalid(self):
        User.objects.create_user("sari", password="Sparein!2026")
        resp = self.client.post(reverse("core:register"), {
            "username": "sari", "password1": "Sparein!2026", "password2": "Sparein!2026"})
        self.assertContains(resp, 'aria-invalid="true"')
        self.assertContains(resp, "field__msg--error")

    def test_register_password_mismatch_shows_error_on_confirm_field(self):
        resp = self.client.post(reverse("core:register"), {
            "username": "budi", "password1": "Sparein!2026", "password2": "beda-sekali"})
        self.assertContains(resp, "field__msg--error")
        self.assertFalse(User.objects.filter(username="budi").exists())

    def test_register_never_echoes_passwords(self):
        resp = self.client.post(reverse("core:register"), {
            "username": "budi", "password1": "Sparein!2026", "password2": "beda-sekali"})
        self.assertNotContains(resp, "Sparein!2026")
        self.assertNotContains(resp, "beda-sekali")


class AuthIconTests(TestCase):
    ICONS = ("eye-muted", "eye-off-muted", "circle-alert-danger", "info-blue", "arrow-left-muted")

    def test_icon_files_exist(self):
        for name in self.ICONS:
            self.assertIsNotNone(finders.find(f"core/icons/{name}.svg"), name)

    def test_auth_pages_call_svg_files_instead_of_inline_svg(self):
        pages = (
            self.client.get(reverse("login"), {"next": "/devices/"}),
            self.client.post(reverse("login"), {"username": "x", "password": "y"}),
            self.client.get(reverse("core:register")),
            self.client.post(reverse("core:register"), {"username": "x"}),
        )
        for resp in pages:
            self.assertNotContains(resp, "<svg")
            self.assertContains(resp, "core/icons/")
