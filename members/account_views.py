"""Password changes. Members with a temporary password must set their own first."""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


@login_required
def set_password(request):
    member = getattr(request.user, 'club_member', None)
    forced = bool(member and member.must_change_password)
    form_class = SetPasswordForm if forced else PasswordChangeForm
    form = form_class(request.user, request.POST or None)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST' and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)  # stay logged in
        if member:
            member.must_change_password = False
            member.save(update_fields=['must_change_password'])
        messages.success(request, 'Your password has been set.')
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('dashboard')
    return render(request, 'registration/set_password.html',
                  {'form': form, 'forced': forced, 'next': next_url})
