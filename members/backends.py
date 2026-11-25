"""Lets members log in with their email address or their username."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        User = get_user_model()
        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            matches = User.objects.filter(email__iexact=username)
            user = matches.first() if matches.count() == 1 else None
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
