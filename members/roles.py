"""
Roles and permissions (Security Constraint: Role-Based Access Control).

A role is a Django Group. Instead of showing executives Django's technical
permission names, the Roles screen shows the plain-language CAPABILITIES below.
Each capability is a bundle of Django permissions.
"""
from django.contrib.auth.models import Group, Permission

CAPABILITIES = [
    ('view_members', 'View member records',
     'Search and view member records (A2).',
     ['members.view_clubmember']),
    ('edit_members', 'Add and edit member records',
     'Add new members and edit member records (A1, A4).',
     ['members.view_clubmember', 'members.add_clubmember', 'members.change_clubmember']),
    ('reset_passwords', 'Reset member passwords',
     'Give a member a new temporary password when they forget theirs.',
     ['members.view_clubmember', 'members.reset_member_password']),
    ('remove_members', 'Remove and restore members',
     'Move members to the Removed Members list and restore them (A3).',
     ['members.view_clubmember', 'members.delete_clubmember', 'members.view_removedmember']),
    ('view_history', 'View change history',
     'See who changed a member record, when, and what changed.',
     ['members.view_changelog']),
    ('manage_events', 'Manage events',
     'Add events and delete selected events (A6, A7).',
     ['events.view_event', 'events.add_event', 'events.delete_event', 'events.view_removedevent']),
    ('run_attendance', 'Run meetings and attendance',
     'Create meetings, start and close QR attendance, and mark members present manually (A5).',
     ['attendance.view_meeting', 'attendance.add_meeting',
      'attendance.view_attendancerecord', 'attendance.add_attendancerecord']),
    ('manage_roles', 'Manage roles',
     'Create roles, choose what each role can do, and assign roles to members.',
     ['auth.view_group', 'auth.add_group', 'auth.change_group', 'auth.delete_group']),
]

CAPABILITY_KEYS = [c[0] for c in CAPABILITIES]
MANAGE_ROLES_PERM = 'auth.change_group'

# Roles nobody can edit or delete from the Roles screen. The Member role is
# every new member's starting role, so it stays fixed with no extra capabilities.
# To unlock it later, remove 'Member' from this list.
LOCKED_ROLES = ['Member']


def is_locked(group):
    return group is not None and group.name in LOCKED_ROLES

# The roles the club starts with (created by `python manage.py setup_roles`).
DEFAULT_ROLES = {
    'President': CAPABILITY_KEYS,
    'Vice President': ['view_members', 'edit_members', 'remove_members', 'view_history',
                       'manage_events', 'run_attendance'],
    'Secretary': ['view_members', 'edit_members', 'reset_passwords', 'remove_members', 'view_history',
                  'manage_events', 'run_attendance'],
    'Treasurer': ['manage_events', 'run_attendance'],
    'Member': [],
}


def _permission(perm):
    app_label, codename = perm.split('.')
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def perms_for(capability_keys):
    perms = set()
    for key, _label, _help, cap_perms in CAPABILITIES:
        if key in capability_keys:
            perms.update(cap_perms)
    return perms


def capabilities_of(group):
    """Which capabilities a role currently has (all of a capability's permissions)."""
    have = {f'{p.content_type.app_label}.{p.codename}'
            for p in group.permissions.select_related('content_type')}
    return [key for key, _l, _h, cap_perms in CAPABILITIES if set(cap_perms) <= have]


def set_capabilities(group, capability_keys):
    group.permissions.set([_permission(p) for p in perms_for(capability_keys)])


def roles_that_can_manage_roles(exclude=None):
    groups = Group.objects.filter(permissions__codename='change_group',
                                  permissions__content_type__app_label='auth')
    if exclude is not None:
        groups = groups.exclude(pk=exclude.pk)
    return groups.distinct()


def someone_active_can_manage_roles(exclude_role=None):
    """True if at least one active member, in a role other than exclude_role, can manage roles."""
    from .models import ClubMember
    return ClubMember.objects.filter(
        role__in=roles_that_can_manage_roles(exclude=exclude_role),
        is_removed=False, user__isnull=False, user__is_active=True).exists()


def anyone_currently_manages_roles():
    return someone_active_can_manage_roles()
