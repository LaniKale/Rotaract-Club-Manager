"""
Loads demo data for testing and the presentation.
Run:   python manage.py seed_demo

Every demo member gets a login with their email (password for all: rotaract123):
  kayla.brown@example.com     – President
  jordan.campbell@example.com – Secretary
  rushane.williams@example.com – Treasurer
  tianna.reid@example.com     – Member
"""
from datetime import time, timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.models import AttendanceRecord, Meeting
from events.models import Event
from members.models import ClubMember

PASSWORD = 'rotaract123'

ADDRESSES = ['Irvine Hall, UWI Mona, Kingston 7', '12 Hope Road, Kingston 6',
             'Chancellor Hall, UWI Mona, Kingston 7', '5 Manchester Road, Mandeville']

PEOPLE = [
    # username, first, surname, faculty, role, status
    ('president', 'Kayla', 'Brown', 'Faculty of Social Sciences', 'President', 'Member'),
    ('secretary', 'Jordan', 'Campbell', 'Faculty of Science and Technology', 'Secretary', 'Member'),
    ('treasurer', 'Rushane', 'Williams', 'Faculty of Social Sciences', 'Treasurer', 'Member'),
    ('member', 'Tianna', 'Reid', 'Faculty of Humanities and Education', 'Member', 'Member'),
    (None, 'Andre', 'Thompson', 'Faculty of Engineering', 'Member', 'Member'),
    (None, 'Shanice', 'Gordon', 'Faculty of Medical Sciences', 'Member', 'Prospective'),
    (None, 'Damion', 'Clarke', 'Faculty of Law', 'Member', 'Prospective'),
    (None, 'Kimberly', 'Edwards', 'Faculty of Science and Technology', 'Member', 'Member'),
    (None, 'Javier', 'Morgan', 'Faculty of Social Sciences', 'Member', 'Prospective'),
    (None, 'Alicia', 'Henry', 'Faculty of Humanities and Education', 'Member', 'Member'),
]


class Command(BaseCommand):
    help = 'Load demo members, events and a meeting.'

    def handle(self, *args, **options):
        call_command('setup_roles')
        today = timezone.localdate()

        for username, first, last, faculty, role, status in PEOPLE:
            email = f'{first.lower()}.{last.lower()}@example.com'
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'first_name': first, 'last_name': last})
            if created:
                user.set_password(PASSWORD)
                user.save()
            ClubMember.objects.update_or_create(
                email=email,
                defaults={'first_name': first, 'surname': last, 'faculty': faculty,
                          'role': Group.objects.get(name=role), 'membership_status': status,
                          'address': ADDRESSES[len(first) % len(ADDRESSES)],
                          'user': user, 'must_change_password': False},
            )

        events = [
            ('Beach Clean-up', 7, time(8, 0), time(12, 0), 'Hellshire Beach', 'Major community project.'),
            ('Career Workshop', 12, time(17, 0), time(19, 0), 'FST Lecture Theatre', 'CV and interview skills.'),
            ('Christmas Treat', 25, time(14, 0), time(17, 0), 'Mona Visitor Lodge', 'Fundraiser social.'),
        ]
        for title, days, start, end, location, desc in events:
            Event.objects.get_or_create(title=title, defaults={
                'date': today + timedelta(days=days), 'start_time': start, 'end_time': end,
                'location': location, 'description': desc})

        for title, days, start, end, location, desc in events:
            Event.objects.filter(title=title, end_time__isnull=True).update(end_time=end)
        Meeting.objects.filter(title='General Meeting', end_time__isnull=True).update(end_time=time(20, 0))

        meeting, _ = Meeting.objects.get_or_create(title='General Meeting', date=today, defaults={
            'start_time': time(18, 0), 'end_time': time(20, 0), 'location': 'Student Union, Room 2'})
        # Five past weekly meetings with a realistic mix of attendance, so the
        # attendance rate on each member record has something to show.
        seeded = ClubMember.objects.filter(
            email__in=[f'{p[1].lower()}.{p[2].lower()}@example.com' for p in PEOPLE])
        seeded.filter(date_added__gt=today - timedelta(days=60)).update(
            date_added=today - timedelta(days=60))
        people = list(seeded.order_by('surname', 'first_name'))
        for week in range(5, 0, -1):
            past, _ = Meeting.objects.get_or_create(title='General Meeting', date=today - timedelta(weeks=week),
                                                    defaults={'start_time': time(18, 0), 'end_time': time(20, 0),
                                                              'location': 'Student Union, Room 2'})
            for i, person in enumerate(people):
                if (i * 3 + week) % 5 != 0 and not (i % 4 == 3 and week % 2):
                    AttendanceRecord.objects.get_or_create(member=person, meeting=past,
                                                           defaults={'method': 'QR' if (i + week) % 3 else 'Manual'})

        # Two people who applied from the Join page, waiting for review.
        from members.models import MembershipApplication
        for first, last, faculty, phone in [('Brianna', 'Lawrence', 'Faculty of Medical Sciences', '876-555-0141'),
                                            ('Tyrese', 'Grant', 'Faculty of Engineering', '')]:
            MembershipApplication.objects.get_or_create(
                email=f'{first.lower()}.{last.lower()}@example.com',
                defaults={'first_name': first, 'surname': last, 'faculty': faculty,
                          'phone_number': phone, 'address': 'Taylor Hall, UWI Mona'})

        andre = ClubMember.objects.get(first_name='Andre')
        AttendanceRecord.objects.get_or_create(member=andre, meeting=meeting,
                                               defaults={'method': 'Manual'})

        self.stdout.write(self.style.SUCCESS(
            f'Demo data loaded. Log in with any member email, e.g. jordan.campbell@example.com (password: {PASSWORD})'))
