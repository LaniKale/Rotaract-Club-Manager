"""Events app – Model component (MVC): Event and RemovedEvent."""
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

FLYER_TYPES = ['jpg', 'jpeg', 'png', 'pdf']


class Event(models.Model):
    title = models.CharField(max_length=150)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    flyer = models.FileField(upload_to='flyers/', blank=True,
                             validators=[FileExtensionValidator(FLYER_TYPES)],
                             help_text='Optional. JPG, PNG or PDF, up to 5 MB.')
    is_removed = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f'{self.title} ({self.date:%d/%m/%Y})'

    # --- Calendar helpers -------------------------------------------------
    @property
    def start_datetime(self):
        return datetime.combine(self.date, self.start_time)

    @property
    def end_datetime(self):
        """Events without an end time are shown as one hour long."""
        if self.end_time:
            return datetime.combine(self.date, self.end_time)
        return self.start_datetime + timedelta(hours=1)

    @staticmethod
    def _utc_stamp(local_dt):
        """Club local time (Jamaica) -> UTC, in the format calendar apps expect."""
        aware = local_dt.replace(tzinfo=ZoneInfo(settings.TIME_ZONE))
        return aware.astimezone(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    @property
    def google_calendar_url(self):
        """Link that opens this event in Google Calendar, ready to save (no API key needed)."""
        params = {
            'action': 'TEMPLATE',
            'text': self.title,
            'dates': f'{self._utc_stamp(self.start_datetime)}/{self._utc_stamp(self.end_datetime)}',
            'details': self.description,
            'location': self.location,
        }
        return 'https://calendar.google.com/calendar/render?' + urlencode(params)

    def to_ics(self, uid_domain='rotaract-uwi-mona'):
        """The event as an .ics file for Apple Calendar, Outlook and others."""
        def esc(text):
            return (text or '').replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')
        now = datetime.now(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        lines = [
            'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Rotaract UWI Mona//CMS//EN', 'METHOD:PUBLISH',
            'BEGIN:VEVENT',
            f'UID:event-{self.pk}@{uid_domain}',
            f'DTSTAMP:{now}',
            f'DTSTART:{self._utc_stamp(self.start_datetime)}',
            f'DTEND:{self._utc_stamp(self.end_datetime)}',
            f'SUMMARY:{esc(self.title)}',
            f'LOCATION:{esc(self.location)}',
            f'DESCRIPTION:{esc(self.description)}',
            'END:VEVENT', 'END:VCALENDAR',
        ]
        return '\r\n'.join(lines) + '\r\n'

    @property
    def flyer_is_image(self):
        return bool(self.flyer) and self.flyer.name.lower().endswith(('.jpg', '.jpeg', '.png'))

    @property
    def is_meeting(self):
        # A Meeting is a type of Event (inheritance in the class diagram).
        return hasattr(self, 'meeting')


class RemovedEvent(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='removal')
    removal_date = models.DateTimeField(auto_now_add=True)
    removed_by = models.CharField(max_length=150)

    class Meta:
        ordering = ['-removal_date']

    def __str__(self):
        return f'{self.event} (removed {self.removal_date:%d/%m/%Y})'
