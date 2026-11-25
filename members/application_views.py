"""
Membership applications (Controller).

  join             – the public Join page. Reached from the login page after scanning a
                     meeting QR code, or from a direct link. No login needed.
  application_list – executives who can add members see the waiting applications.
  Accepting opens the normal Add member form pre-filled (see member_add in views.py),
  so the login, temporary password and change log work exactly as before.
  application_reject – closes an application without creating a member.
"""
import re

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import MembershipApplicationForm
from .models import ChangeLog, MembershipApplication

CHECKIN_PATH = re.compile(r'/attendance/checkin/([^/?#]+)/')


def _meeting_from(next_url):
    """The meeting whose QR code the person scanned, if the code is still valid."""
    from attendance.models import QRCode
    match = CHECKIN_PATH.search(next_url or '')
    if not match:
        return None
    qr = QRCode.objects.filter(token=match.group(1)).select_related('meeting').first()
    return qr.meeting if qr and qr.is_valid() else None


def join(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')
    meeting = _meeting_from(next_url)
    member = getattr(request.user, 'club_member', None) if request.user.is_authenticated else None
    if member and not member.is_removed:
        messages.info(request, 'You are already a club member.')
        return redirect('dashboard')

    form = MembershipApplicationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        application = form.save(commit=False)
        application.meeting = meeting
        application.save()
        return render(request, 'members/join_done.html', {'application': application})
    return render(request, 'members/join.html', {'form': form, 'next': next_url, 'meeting': meeting})


@permission_required('members.add_clubmember', raise_exception=True)
def application_list(request):
    applications = MembershipApplication.objects.select_related('meeting', 'member')
    return render(request, 'members/application_list.html', {
        'pending': applications.filter(status=MembershipApplication.STATUS_PENDING).order_by('submitted_at'),
        'reviewed': applications.exclude(status=MembershipApplication.STATUS_PENDING)
                                .order_by('-reviewed_at')[:20],
    })


@permission_required('members.add_clubmember', raise_exception=True)
def application_reject(request, pk):
    application = get_object_or_404(MembershipApplication, pk=pk,
                                    status=MembershipApplication.STATUS_PENDING)
    if request.method == 'POST':
        application.close(MembershipApplication.STATUS_REJECTED, request.user)
        ChangeLog.log_change(request.user, 'Application', application.pk, 'Remove',
                             old_value=f'Rejected application from {application.full_name}')
        messages.success(request, f'The application from {application.full_name} was rejected.')
        return redirect('members:applications')
    return render(request, 'confirm.html', {
        'title': 'Reject application',
        'message': f'Reject the application from {application.full_name} ({application.email})? '
                   'No member record or login will be created.',
        'cancel_url': reverse('members:applications'),
    })
