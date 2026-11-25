"""A2 – View and search member records."""
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render

from ..forms import MemberSearchForm
from ..models import ChangeLog, ClubMember
from .common import _may_act_on


@permission_required('members.view_clubmember', raise_exception=True)
def member_list(request):
    """A2: view and search member records."""
    form = MemberSearchForm(request.GET or None)
    members = ClubMember.objects.filter(is_removed=False)
    if form.is_valid():
        data = form.cleaned_data
        if data['first_name']:
            members = members.filter(first_name__icontains=data['first_name'])
        if data['surname']:
            members = members.filter(surname__icontains=data['surname'])
        if data['faculty']:
            members = members.filter(faculty=data['faculty'])
        if data['status']:
            members = members.filter(membership_status=data['status'])
    return render(request, 'members/member_list.html', {'form': form, 'members': members})


@permission_required('members.view_clubmember', raise_exception=True)
def member_detail(request, pk):
    member = get_object_or_404(ClubMember, pk=pk)
    new_password = request.session.pop('new_password', None)
    if not new_password or new_password['member'] != member.pk:
        new_password = None
    return render(request, 'members/member_detail.html', {
        'member': member,
        'new_password': new_password and new_password['password'],
        'may_act_on': _may_act_on(request, member),
        'attendance': member.get_attendance_history(),
        'summary': member.attendance_summary(),
        'history': ChangeLog.objects.filter(record_type='Member', record_id=member.pk)[:20],
    })
