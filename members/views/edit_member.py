"""A4 – Edit a member record. Every changed field is written to the change history."""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ..forms import ClubMemberForm
from ..models import ChangeLog, ClubMember
from ..roles import MANAGE_ROLES_PERM
from .common import TRACKED_FIELDS, _is_role_manager, _only_role_manager


@permission_required('members.change_clubmember', raise_exception=True)
def member_edit(request, pk):
    """A4: edit a member record. Each changed field is written to the ChangeLog (A4.3)."""
    member = get_object_or_404(ClubMember, pk=pk, is_removed=False)
    old_values = {f: getattr(member, f) for f in TRACKED_FIELDS}
    form = ClubMemberForm(request.POST or None, instance=member,
                          can_manage_roles=request.user.has_perm(MANAGE_ROLES_PERM))
    if request.method == 'POST' and form.is_valid():
        new_role = form.cleaned_data.get('role')
        loses_role_management = not (new_role and new_role.permissions.filter(
            codename='change_group', content_type__app_label='auth').exists())
        if (member.role != new_role and loses_role_management
                and _is_role_manager(member) and _only_role_manager(member)):
            messages.error(request, 'This is the only member who can manage roles. '
                                    'Give someone else that role first.')
            return redirect('members:edit', pk=member.pk)
        with transaction.atomic():
            member = form.save()
            if member.user:
                user = member.user
                if '@' in user.username:  # email-based logins follow the member's email
                    user.username = member.email.lower()
                user.email = member.email
                user.first_name, user.last_name = member.first_name, member.surname
                user.save()
            for field in TRACKED_FIELDS:
                new = getattr(member, field)
                if old_values[field] != new:
                    ChangeLog.log_change(request.user, 'Member', member.pk, 'Edit',
                                         field, old_values[field], new)
        messages.success(request, 'Member record updated.')
        return redirect('members:detail', pk=member.pk)
    return render(request, 'members/member_form.html', {
        'form': form, 'title': f'Edit {member.full_name}', 'member': member,
        'cancel_url': reverse('members:detail', args=[member.pk])})
