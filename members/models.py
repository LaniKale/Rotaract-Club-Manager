"""
Members app – Model component (MVC).

Classes:
  ClubMember    – every member, executive or not. The role decides what they can do.
  RemovedMember – the Removed Members list (A3.1). Records are never deleted.
  ChangeLog     – audit trail of every add / edit / remove (A4.3, SAFETY-3).

  MembershipApplication – a sign-up sent from the Join page (after scanning a
                  meeting QR code). An executive reviews it: accepting opens the
                  Add member form already filled in; rejecting just closes it.

Logins use Django's built-in User model; roles use Django's built-in Group model.
"""
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models.functions import Lower
from django.utils.crypto import get_random_string


FACULTY_CHOICES = [(f, f) for f in [
    'Faculty of Engineering',
    'Faculty of Humanities and Education',
    'Faculty of Law',
    'Faculty of Medical Sciences',
    'Faculty of Science and Technology',
    'Faculty of Social Sciences',
    'Faculty of Sport',
]]


class ClubMember(models.Model):
    STATUS_PROSPECTIVE = 'Prospective'
    STATUS_MEMBER = 'Member'
    STATUS_CHOICES = [
        (STATUS_PROSPECTIVE, 'Prospective member'),
        (STATUS_MEMBER, 'Member'),
    ]
    DEFAULT_ROLE = 'Member'

    # Login 1–1 ClubMember. Every member gets a login when they are added (A1).
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='club_member',
    )
    first_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    faculty = models.CharField(max_length=100, choices=FACULTY_CHOICES)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)  # optional
    address = models.CharField(max_length=255, blank=True)      # optional
    membership_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PROSPECTIVE)
    # A Role is a Django Group. Roles and their permissions are managed on the
    # Roles screen, so new roles can be added without changing code.
    role = models.ForeignKey(Group, on_delete=models.PROTECT, null=True, blank=True,
                             related_name='club_members')
    must_change_password = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        # Records are sorted when displayed: surname, then first name (A2.4, A4.3).
        # Case-insensitive, so 'de Souza' sorts with the Ds, not after every capital letter.
        ordering = [Lower('surname'), Lower('first_name')]
        # Resetting a password is its own permission, granted to roles on the Roles screen.
        permissions = [('reset_member_password', 'Can reset member passwords')]

    def __str__(self):
        return f'{self.surname}, {self.first_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.surname}'

    def save(self, *args, **kwargs):
        if self.role_id is None:
            self.role, _ = Group.objects.get_or_create(name=self.DEFAULT_ROLE)
        super().save(*args, **kwargs)
        self.sync_login()

    def sync_login(self):
        """Keep the login in step with the member record: the login belongs only
        to this member's role group, and a removed member cannot log in."""
        if not self.user:
            return
        self.user.groups.set([self.role] if self.role and not self.is_removed else [])
        active = not self.is_removed
        if self.user.is_active != active:
            self.user.is_active = active
            self.user.save(update_fields=['is_active'])

    def create_login(self):
        """Create this member's login (username = email) with a temporary password.
        Returns the temporary password, or None if that email already has a login."""
        username = self.email.lower()
        if self.user or User.objects.filter(username__iexact=username).exists():
            return None
        password = make_temporary_password()
        self.user = User.objects.create_user(username=username, email=self.email,
                                             password=password,
                                             first_name=self.first_name, last_name=self.surname)
        self.must_change_password = True
        self.save()
        return password

    def reset_password(self):
        """resetPassword(): give the member a new temporary password."""
        if not self.user:
            return self.create_login()
        password = make_temporary_password()
        self.user.set_password(password)
        self.user.save()
        self.must_change_password = True
        self.save(update_fields=['must_change_password'])
        return password

    def has_permission(self, action):
        """True if the member's role grants this permission.
        Permissions come from the member's role, e.g. has_permission('members.change_clubmember')."""
        return bool(self.user and self.user.has_perm(action))

    def attendance_summary(self):
        """Attendance rate: meetings attended out of meetings held since the member joined.
        A meeting they attended before their join date still counts."""
        from django.db.models import Q
        from django.utils import timezone

        from attendance.models import Meeting
        held = Meeting.objects.filter(is_removed=False, date__lte=timezone.localdate()).filter(
            Q(date__gte=self.date_added) | Q(attendance_records__member=self)).distinct()
        total = held.count()
        attended = self.attendance_records.filter(meeting__in=held).count()
        return {'attended': attended, 'total': total,
                'percent': round(100 * attended / total) if total else None}

    def get_attendance_history(self):
        return self.attendance_records.select_related('meeting').order_by('-timestamp')


def name_and_role(user):
    """The person behind a login, e.g. ('Kayla Brown', 'President')."""
    member = getattr(user, 'club_member', None) if user else None
    if member:
        return member.full_name, member.role.name if member.role else ''
    if user:
        return (user.get_full_name() or user.get_username(),
                'Administrator' if user.is_superuser else '')
    return 'system', ''


def describe_user(user):
    """e.g. 'Kayla Brown (President)'."""
    name, role = name_and_role(user)
    return f'{name} ({role})' if role else name


def make_temporary_password():
    # No look-alike characters (0/O, 1/l), so it is easy to read out to a member.
    return get_random_string(10, 'abcdefghjkmnpqrstuvwxyz23456789')


class RemovedMember(models.Model):
    member = models.OneToOneField(ClubMember, on_delete=models.CASCADE,
                                  related_name='removal')
    removal_date = models.DateTimeField(auto_now_add=True)
    removed_by = models.CharField(max_length=150)

    class Meta:
        ordering = ['-removal_date']

    def __str__(self):
        return f'{self.member} (removed {self.removal_date:%d/%m/%Y})'


class ChangeLog(models.Model):
    ACTION_CHOICES = [('Add', 'Add'), ('Edit', 'Edit'),
                      ('Remove', 'Remove'), ('Restore', 'Restore')]

    changed_by = models.CharField(max_length=150)           # login username
    changed_by_name = models.CharField(max_length=150, blank=True)
    changed_by_role = models.CharField(max_length=150, blank=True)  # role at the time
    change_date = models.DateTimeField(auto_now_add=True)
    record_type = models.CharField(max_length=20)  # 'Member', 'Event', 'Role' or 'Attendance'
    record_id = models.PositiveIntegerField()
    field_name = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    class Meta:
        ordering = ['-change_date']

    def __str__(self):
        return f'{self.change_date:%d/%m/%Y %H:%M} {self.changed_by_display}: {self.action} {self.record_type} #{self.record_id}'

    @property
    def field_label(self):
        """'phone_number' -> 'Phone number' for display."""
        return self.field_name.replace('_', ' ').capitalize()

    @property
    def changed_by_display(self):
        name = self.changed_by_name or self.changed_by
        return f'{name} ({self.changed_by_role})' if self.changed_by_role else name

    @classmethod
    def log_change(cls, user, record_type, record_id, action,
                   field_name='', old_value='', new_value=''):
        """Records a change: who made it, their role, and the old and new values."""
        name, role = name_and_role(user)
        return cls.objects.create(
            changed_by=user.get_username() if user else 'system',
            changed_by_name=name, changed_by_role=role,
            record_type=record_type, record_id=record_id, action=action,
            field_name=field_name, old_value=str(old_value), new_value=str(new_value),
        )


class MembershipApplication(models.Model):
    """A request to join the club, sent from the public Join page.
    It is not a member record: nothing is created until an executive accepts it
    and saves the (pre-filled) Add member form."""
    STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED = 'Pending', 'Accepted', 'Rejected'
    STATUS_CHOICES = [(STATUS_PENDING, 'Waiting for review'), (STATUS_ACCEPTED, 'Accepted'),
                      (STATUS_REJECTED, 'Rejected')]
    # The same details the Add member form collects.
    FORM_FIELDS = ['first_name', 'surname', 'faculty', 'email', 'phone_number', 'address']

    first_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    faculty = models.CharField(max_length=100, choices=FACULTY_CHOICES)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    meeting = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='applications')  # the meeting whose QR code they scanned
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.CharField(max_length=150, blank=True)   # name and role, e.g. "Jordan Campbell (Secretary)"
    reviewed_at = models.DateTimeField(null=True, blank=True)
    member = models.OneToOneField(ClubMember, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='application')  # the record created when accepted

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.first_name} {self.surname} ({self.status})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.surname}'

    def as_member_initial(self):
        """Values to pre-fill the Add member form with."""
        return {f: getattr(self, f) for f in self.FORM_FIELDS}

    def close(self, status, user, member=None):
        from django.utils import timezone
        self.status = status
        self.reviewed_by = describe_user(user)
        self.reviewed_at = timezone.now()
        self.member = member
        self.save()
