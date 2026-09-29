from django.contrib.auth.models import User
from django.test import TestCase

from core.models import UserProfile


class ProfileTests(TestCase):
    def test_new_user_gets_member_profile(self):
        user = User.objects.create_user("budi", password="x")
        self.assertEqual(user.profile.role, UserProfile.Role.MEMBER)
