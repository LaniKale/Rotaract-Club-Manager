"""
Roles screen (Controller). Executives with the "Manage roles" capability can
create roles, choose what each role can do, and delete unused roles.
"""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import RoleForm
from .models import ChangeLog, ClubMember
from .roles import CAPABILITIES, capabilities_of, is_locked, set_capabilities

MANAGE = 'auth.change_group'


def _active_role_managers_after(role, new_capabilities):
    """How many active members could still manage roles if `role` had `new_capabilities`."""
    count = 0
    members = ClubMember.objects.filter(is_removed=False, user__is_active=True).select_related('role')
    for m in members:
        caps = new_capabilities if m.role_id == role.pk else capabilities_of(m.role) if m.role else []
        if 'manage_roles' in caps:
            count += 1
    return count


def _currently_any_role_manager():
    return any('manage_roles' in capabilities_of(m.role)
               for m in ClubMember.objects.filter(is_removed=False, user__is_active=True,
                                                  role__isnull=False).select_related('role'))


@permission_required(MANAGE, raise_exception=True)
def role_list(request):
    roles = []
    labels = {key: label for key, label, _h, _p in CAPABILITIES}
    for group in Group.objects.order_by('name'):
        roles.append({
            'group': group,
            'members': group.club_members.filter(is_removed=False).count(),
            'capabilities': [labels[k] for k in capabilities_of(group)],
            'locked': is_locked(group),
        })
    return render(request, 'members/role_list.html', {'roles': roles})


@permission_required(MANAGE, raise_exception=True)
def role_edit(request, pk=None):
    role = get_object_or_404(Group, pk=pk) if pk else None
    if is_locked(role):
        messages.error(request, f'The {role.name} role is locked and cannot be edited.')
        return redirect('roles:list')
    initial = {'name': role.name, 'capabilities': capabilities_of(role)} if role else {}
    form = RoleForm(request.POST or None, role=role, initial=initial)
    if request.method == 'POST' and form.is_valid():
        caps = form.cleaned_data['capabilities']
        if (role and _currently_any_role_manager()
                and _active_role_managers_after(role, caps) == 0):
            messages.error(request, 'At least one active member must be able to manage roles. '
                                    'Keep "Manage roles" ticked for this role, or give it to another role first.')
        else:
            with transaction.atomic():
                group = role or Group()
                group.name = form.cleaned_data['name']
                group.save()
                set_capabilities(group, caps)
                ChangeLog.log_change(request.user, 'Role', group.pk, 'Edit' if role else 'Add',
                                     'capabilities', '', ', '.join(caps) or 'none')
            messages.success(request, f'Role "{group.name}" saved.')
            return redirect('roles:list')
    return render(request, 'members/role_form.html', {
        'form': form, 'role': role, 'capabilities': CAPABILITIES,
        'title': f'Edit role: {role.name}' if role else 'New role'})


@permission_required(MANAGE, raise_exception=True)
def role_delete(request, pk):
    role = get_object_or_404(Group, pk=pk)
    in_use = role.club_members.count()
    if is_locked(role):
        messages.error(request, f'The {role.name} role is locked and cannot be deleted.')
        return redirect('roles:list')
    if in_use:
        messages.error(request, f'"{role.name}" is still assigned to {in_use} member(s), including '
                                f'removed members. Give them another role first.')
        return redirect('roles:list')
    if request.method == 'POST':
        name = role.name
        ChangeLog.log_change(request.user, 'Role', role.pk, 'Remove', old_value=name)
        role.delete()
        messages.success(request, f'Role "{name}" deleted.')
        return redirect('roles:list')
    return render(request, 'confirm.html', {
        'title': 'Delete role', 'message': f'Delete the role "{role.name}"? No members have it.',
        'cancel_url': reverse('roles:list')})
