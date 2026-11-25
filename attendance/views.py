"""
Attendance app – Controller component (MVC): AttendanceController in the SDS.
"""
import io

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from events.forms import EventForm
from members.models import ChangeLog
from members.navigation import back_url

from .forms import ManualCheckInForm
from .models import AttendanceRecord, Meeting, QRCode


class MeetingForm(EventForm):
    class Meta(EventForm.Meta):
        model = Meeting


@permission_required('attendance.view_meeting', raise_exception=True)
def meeting_list(request):
    meetings = Meeting.objects.filter(is_removed=False).order_by('-date', '-start_time')
    return render(request, 'attendance/meeting_list.html', {'meetings': meetings})


@permission_required('attendance.add_meeting', raise_exception=True)
def meeting_add(request):
    form = MeetingForm(request.POST or None, request.FILES or None, initial={'title': 'General Meeting'},
                       allow_clash=request.POST.get('confirm_clash') == '1')
    if request.method == 'POST' and form.is_valid():
        meeting = form.save()
        ChangeLog.log_change(request.user, 'Event', meeting.pk, 'Add', new_value=meeting.title)
        messages.success(request, 'Meeting created. Start attendance when the meeting begins.')
        return redirect('attendance:detail', pk=meeting.pk)
    return render(request, 'events/event_form.html', {
        'form': form, 'title': 'Add meeting', 'cancel_url': back_url(request, 'attendance:meetings')})


@permission_required('attendance.view_meeting', raise_exception=True)
def meeting_detail(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    qr = getattr(meeting, 'qr_code', None)
    checkin_url = None
    if qr and qr.is_valid():
        checkin_url = request.build_absolute_uri(reverse('attendance:checkin', args=[qr.token]))
    records = meeting.view_meeting_attendance()
    absent = meeting.absent_members()
    expected = meeting.expected_members().count()
    present_expected = expected - absent.count()
    return render(request, 'attendance/meeting_detail.html', {
        'meeting': meeting, 'qr': qr, 'checkin_url': checkin_url,
        'records': records, 'absent': absent, 'expected': expected,
        'turnout': round(100 * present_expected / expected) if expected else None,
        'history': ChangeLog.objects.filter(record_type='Attendance', record_id=meeting.pk)[:20],
    })


@permission_required('attendance.add_meeting', raise_exception=True)
def start_session(request, pk):
    if request.method == 'POST':
        QRCode.generate_for(get_object_or_404(Meeting, pk=pk))
        messages.success(request, 'Attendance started. Display the QR code for members to scan.')
    return redirect('attendance:detail', pk=pk)


@permission_required('attendance.add_meeting', raise_exception=True)
def close_session(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)
    if request.method == 'POST' and hasattr(meeting, 'qr_code'):
        meeting.qr_code.deactivate()
        messages.success(request, 'Attendance closed. The QR code no longer works.')
    return redirect('attendance:detail', pk=pk)


@permission_required('attendance.view_meeting', raise_exception=True)
def qr_image(request, pk):
    """Returns the meeting's QR code as a PNG image."""
    qr = get_object_or_404(QRCode, meeting_id=pk)
    url = request.build_absolute_uri(reverse('attendance:checkin', args=[qr.token]))
    buffer = io.BytesIO()
    qrcode.make(url).save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def checkin(request, token):
    """processScanResult() / recordAttendance() in the SDS: the page members reach by scanning the meeting's QR code.
    Members check in as themselves, so they must be logged in. Their phone stays
    logged in, so after the first time, checking in is one scan and one tap."""
    qr = QRCode.objects.filter(token=token).select_related('meeting').first()
    if not qr or not qr.is_valid():
        return render(request, 'attendance/checkin_result.html', {
            'ok': False, 'message': 'This attendance session has ended.'})
    if not request.user.is_authenticated:
        # Not logged in: log in first, then come straight back here.
        return redirect_to_login(request.get_full_path())

    member = getattr(request.user, 'club_member', None)
    if member is None or member.is_removed:
        # Login not linked to an active member record: show the link to apply to join.
        return render(request, 'attendance/checkin_result.html', {
            'ok': False, 'message': 'Your login is not linked to an active member record.',
            'register': True})

    already = AttendanceRecord.objects.filter(member=member, meeting=qr.meeting).exists()
    if request.method == 'POST':
        record, created = AttendanceRecord.objects.get_or_create(
            member=member, meeting=qr.meeting, defaults={'method': 'QR'})
        if not created:
            return render(request, 'attendance/checkin_result.html', {
                'ok': False, 'message': 'You are already checked in for this meeting.',
                'meeting': qr.meeting})
        return render(request, 'attendance/checkin_result.html', {
            'ok': True, 'message': f'Attendance recorded. Welcome, {member.first_name}!',
            'meeting': qr.meeting})
    return render(request, 'attendance/checkin.html',
                  {'meeting': qr.meeting, 'member': member, 'already': already})


@permission_required('attendance.add_attendancerecord', raise_exception=True)
def manual_checkin(request, pk):
    """recordAttendance() for a member who cannot scan: an executive marks them present."""
    meeting = get_object_or_404(Meeting, pk=pk)
    form = ManualCheckInForm(request.POST or None, meeting=meeting)
    if request.method == 'POST' and form.is_valid():
        member = form.cleaned_data['member']
        _, created = AttendanceRecord.objects.get_or_create(member=member, meeting=meeting,
                                                            defaults={'method': 'Manual'})
        if created:
            ChangeLog.log_change(request.user, 'Attendance', meeting.pk, 'Add',
                                 new_value=f'{member.full_name} marked present (manual)')
        messages.success(request, f'{member.full_name} marked present.')
    return redirect('attendance:detail', pk=pk)


@permission_required('attendance.add_attendancerecord', raise_exception=True)
def remove_record(request, pk):
    """Undo a check-in recorded by mistake. The removal is kept in the change log."""
    record = get_object_or_404(AttendanceRecord.objects.select_related('member', 'meeting'), pk=pk)
    meeting, member = record.meeting, record.member
    if request.method == 'POST':
        at = f'{timezone.localtime(record.timestamp):%I:%M %p}'.lstrip('0')
        ChangeLog.log_change(request.user, 'Attendance', meeting.pk, 'Remove',
                             old_value=f'{member.full_name} ({record.get_method_display()} check-in at {at})')
        record.delete()
        messages.success(request, f'{member.full_name} is no longer marked present.')
        return redirect('attendance:detail', pk=meeting.pk)
    return render(request, 'confirm.html', {
        'title': 'Remove check-in',
        'message': f'Remove {member.full_name}\'s check-in for {meeting.title} on '
                   f'{meeting.date:%d/%m/%Y}? They will show as absent. This is recorded in the change history.',
        'cancel_url': reverse('attendance:detail', args=[meeting.pk]),
    })


@login_required
def my_attendance(request):
    """A member views their own attendance record."""
    member = getattr(request.user, 'club_member', None)
    records = member.get_attendance_history() if member else []
    return render(request, 'attendance/my_attendance.html', {'member': member, 'records': records,
                   'summary': member.attendance_summary() if member else None})
