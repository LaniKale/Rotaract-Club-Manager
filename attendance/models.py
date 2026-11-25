"""
Attendance app – Model component.

  Meeting          – a type of Event (inheritance in the class diagram).
  QRCode           – owned by one Meeting (composition). Expires when the session ends.
  AttendanceRecord – one member checking in to one meeting (method: QR or Manual).
"""
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from events.models import Event
from members.models import ClubMember


class Meeting(Event):
    """Inherits title, date, start_time, end_time, location and description from Event."""

    def view_meeting_attendance(self):
        return self.attendance_records.select_related('member').order_by(
            Lower('member__surname'), Lower('member__first_name'))

    def expected_members(self):
        """Active members who were already in the club on the day of this meeting."""
        return ClubMember.objects.filter(is_removed=False, date_added__lte=self.date)

    def absent_members(self):
        """Expected members who have not checked in."""
        present = self.attendance_records.values_list('member_id', flat=True)
        return self.expected_members().exclude(pk__in=present)


class QRCode(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='qr_code')
    token = models.CharField(max_length=64, unique=True)
    date_generated = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()

    def __str__(self):
        return f'QR for {self.meeting}'

    @classmethod
    def generate_for(cls, meeting):
        """generateQRCode(): create (or renew) the meeting's QR code."""
        hours = getattr(settings, 'QR_CODE_VALID_HOURS', 3)
        qr, _ = cls.objects.update_or_create(
            meeting=meeting,
            defaults={'token': secrets.token_urlsafe(16),
                      'expiry_time': timezone.now() + timedelta(hours=hours)},
        )
        return qr

    def is_valid(self):
        """The QR code works only until attendance is closed or it expires."""
        return timezone.now() < self.expiry_time

    def deactivate(self):
        """Close attendance now: the QR code stops working."""
        self.expiry_time = timezone.now()
        self.save()


class AttendanceRecord(models.Model):
    METHOD_CHOICES = [('QR', 'QR scan'), ('Manual', 'Manual')]

    member = models.ForeignKey(ClubMember, on_delete=models.CASCADE,
                               related_name='attendance_records')
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE,
                                related_name='attendance_records')
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default='QR')

    class Meta:
        # Business rule: one check-in per member per meeting.
        constraints = [models.UniqueConstraint(fields=['member', 'meeting'],
                                               name='one_checkin_per_meeting')]

    def __str__(self):
        return f'{self.member} at {self.meeting} ({self.method})'
