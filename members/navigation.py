"""Helpers for sending users back to the page they came from."""
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def back_url(request, default):
    """The page the user came from (kept in a hidden 'next' field while the form is
    being filled in), or `default` (a URL name such as 'events:list')."""
    candidate = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER', '')
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()},
                                                     require_https=request.is_secure()):
        # Never "go back" to the form itself.
        if request.path not in candidate:
            return candidate
    return reverse(default)
