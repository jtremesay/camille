from django.test import TestCase

from .models import Profile, User


class ProfileModelTest(TestCase):
    def test_profile_creation(self):
        assert User.objects.count() == 0
        assert Profile.objects.count() == 0

        user = User.objects.create_user(username="testuser", password="testpassword")
        Profile.objects.get(user=user)
        assert User.objects.count() == 1
        assert Profile.objects.count() == 1
