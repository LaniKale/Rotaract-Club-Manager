"""A3 – Remove a member record, the Removed Members list, and restore."""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..models import ChangeLog, ClubMember, RemovedMember, describe_user
from .common import _is_role_manager, _may_act_on, _only_role_manager


@permission_required('members.delete_clubmember', raise_exception=True)
def member_remove(request, pk):
    """A3: remove a member. They are moved to the Removed Members list, never deleted."""
    member = get_object_or_404(ClubMember, pk=pk, is_removed=False)
    if not _may_act_on(request, member):
        raise PermissionDenied
    if _is_role_manager(member) and _only_role_manager(member):
        messages.error(request, f'{member.full_name} is the only member who can manage roles, '
                                f'so they cannot be removed.')
        return redirect('members:detail', pk=member.pk)
    if request.method == 'POST':
        with transaction.atomic():
            member.is_removed = True
            member.save()
            RemovedMember.objects.update_or_create(
                member=member, defaults={'removed_by': describe_user(request.user)})
            ChangeLog.log_change(request.user, 'Member', member.pk, 'Remove',
                                 old_value=member.full_name)
        messages.success(request, f'{member.full_name} was moved to the Removed Members list.')
        return redirect('members:list')
    return render(request, 'confirm.html', {
        'title': 'Remove member',
        'message': f'Remove {member.full_name}? They will be moved to the Removed Members '
                   f'list and can be restored later.',
        'cancel_url': reverse('members:detail', args=[member.pk]),
    })


@permission_required('members.view_clubmember', raise_exception=True)
def removed_list(request):
    removed = RemovedMember.objects.select_related('member')
    return render(request, 'members/removed_list.html', {'removed': removed})


@permission_required('members.delete_clubmember', raise_exception=True)
def member_restore(request, pk):
    member = get_object_or_404(ClubMember, pk=pk, is_removed=True)
    if request.method == 'POST':
        with transaction.atomic():
            member.is_removed = False
            member.save()
            RemovedMember.objects.filter(member=member).delete()
            ChangeLog.log_change(request.user, 'Member', member.pk, 'Restore',
                                 new_value=member.full_name)
        messages.success(request, f'{member.full_name} was restored.')
    return redirect('members:removed')
