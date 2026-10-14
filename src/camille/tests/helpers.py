from django.contrib.auth.models import User


def make_user(username: str = "alice") -> User:
    return User.objects.create_user(username=username, password="password")
