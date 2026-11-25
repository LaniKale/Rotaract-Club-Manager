"""A1 – Add new member record."""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse

from ..forms import ClubMemberForm
from ..models import ChangeLog, ClubMember, MembershipApplication
from ..navigation import back_url
from ..roles import MANAGE_ROLES_PERM
from .common import _show_password_once


@permission_required('members.add_clubmember', raise_exception=True)
def member_add(request):
    """A1: add a new member record. New members default to 'Prospective'.
    With ?application=<id>, the form is pre-filled from that membership application."""
    application_id = request.POST.get('application') or request.GET.get('application')
    application = MembershipApplication.objects.filter(
        pk=application_id, status=MembershipApplication.STATUS_PENDING).first() if application_id else None
    form = ClubMemberForm(request.POST or None,
                          initial=application.as_member_initial() if application else None,
                          can_manage_roles=request.user.has_perm(MANAGE_ROLES_PERM))
    duplicates = None
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        # A1.3: warn if a member with the same name and email already exists.
        duplicates = ClubMember.objects.filter(
            first_name__iexact=data['first_name'], surname__iexact=data['surname'],
            email__iexact=data['email'])
        if duplicates.exists() and not request.POST.get('confirm_duplicate'):
            messages.warning(request, 'A member with this name and email already exists. '
                                      'Tick "Save anyway" to add them again.')
        else:
            with transaction.atomic():  # all-or-nothing save (Reliability)
                member = form.save()
                password = member.create_login()  # every member gets a login
                ChangeLog.log_change(request.user, 'Member', member.pk, 'Add',
                                     new_value=member.full_name + (' (from application)' if application else ''))
                if application:
                    application.close(MembershipApplication.STATUS_ACCEPTED, request.user, member)
            if password:
                _show_password_once(request, member, password)
                messages.success(request, f'{member.full_name} was added and their login was created.')
            else:
                messages.warning(request, f'{member.full_name} was added, but a login already uses '
                                          f'{member.email}, so no new login was created.')
            return redirect('members:detail', pk=member.pk)
    return render(request, 'members/member_form.html', {
        'form': form, 'duplicates': duplicates, 'application': application,
        'title': f'Accept application: {application.full_name}' if application else 'Add member',
        'cancel_url': reverse('members:applications') if application else back_url(request, 'members:list')})
