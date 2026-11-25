"""Members logging in with a temporary password must choose their own first."""
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated:
            member = getattr(user, 'club_member', None)
            allowed = (reverse('set_password'), reverse('logout'), '/static/')
            if (member and member.must_change_password
                    and not request.path.startswith(allowed)):
                return redirect(f"{reverse('set_password')}?{urlencode({'next': request.get_full_path()})}")
        return self.get_response(request)
