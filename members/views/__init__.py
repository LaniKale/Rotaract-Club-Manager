"""Members app – Controller component (MVC): MemberController in the SDS.
One module per SRS feature:

  add_member.py     A1  Add new member record
  view_members.py   A2  View and search member records
  remove_member.py  A3  Remove member record
  edit_member.py    A4  Edit member record
  common.py         shared helpers, dashboard, password reset

Every executive view is protected with @permission_required, so the login and role
check happens before anything reaches the Model (Security Constraint).
"""
from .add_member import member_add
from .common import dashboard, member_reset_password
from .edit_member import member_edit
from .remove_member import member_remove, member_restore, removed_list
from .view_members import member_detail, member_list

__all__ = ['dashboard', 'member_add', 'member_detail', 'member_edit', 'member_list', 'member_remove',
           'member_reset_password', 'member_restore', 'removed_list']
