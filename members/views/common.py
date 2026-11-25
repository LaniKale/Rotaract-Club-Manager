"""Shared helpers for the member views, the dashboard, and password reset (resetPassword() in the SDS)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import ChangeLog, ClubMember
from ..roles import MANAGE_ROLES_PERM


TRACKED_FIELDS = ['first_name', 'surname', 'faculty', 'email', 'phone_number', 'address',
                  'membership_status', 'role']


@login_required
def dashboard(request):
    from events.models import Event
    upcoming = Event.objects.filter(is_removed=False, date__gte=timezone.localdate())[:5]
    return render(request, 'dashboard.html', {'upcoming_events': upcoming})


def _show_password_once(request, member, password):
    """Keep a new temporary password just long enough to show it on the next page."""
    request.session['new_password'] = {'member': member.pk, 'password': password}


def _is_role_manager(member):
    return member.has_permission(MANAGE_ROLES_PERM)


def _may_act_on(request, member):
    """Only role managers may remove or reset the password of another role manager."""
    return request.user.has_perm(MANAGE_ROLES_PERM) or not _is_role_manager(member)


def _only_role_manager(member):
    others = ClubMember.objects.filter(is_removed=False, user__is_active=True).exclude(pk=member.pk)
    return not any(_is_role_manager(m) for m in others.select_related('user'))


@permission_required('members.reset_member_password', raise_exception=True)
def member_reset_password(request, pk):
    """resetPassword(): give the member a new temporary password (no email needed)."""
    member = get_object_or_404(ClubMember, pk=pk, is_removed=False)
    if not _may_act_on(request, member):
        raise PermissionDenied
    if request.method == 'POST':
        password = member.reset_password()
        if password:
            _show_password_once(request, member, password)
            ChangeLog.log_change(request.user, 'Member', member.pk, 'Edit', 'password',
                                 '', 'reset by executive')
            messages.success(request, f'A new temporary password was created for {member.full_name}.')
        else:
            messages.error(request, f'A login already uses {member.email}, so one could not be created.')
    return redirect('members:detail', pk=member.pk)
