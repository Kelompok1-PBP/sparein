from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from core.models import UserProfile
from core.permissions import is_contributor, is_member


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
