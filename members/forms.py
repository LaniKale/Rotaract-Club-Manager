"""Forms do the Controller's data validation: required fields, names, email and phone format (A1.4, A4.2)."""
import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User

from .models import FACULTY_CHOICES, ClubMember, MembershipApplication
from .roles import CAPABILITIES, LOCKED_ROLES


# Letters (including accented ones), with spaces, hyphens, full stops or apostrophes
# between them (straight ' or the curly ’ that phones type): O'Brien, Mary-Jane, St. John.
NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+([ '’\-.]+[A-Za-zÀ-ÖØ-öø-ÿ]+)*\.?$")
PHONE_ALLOWED = re.compile(r'^\+?[\d\s\-()]+$')


class PersonDetailsMixin:
    """Checks shared by the Add/Edit member form and the public Join form:
    names are letters only (A1 TS-4), the email is a valid address and the phone
    number is a real phone number in a standard format."""

    def _clean_name(self, field, label):
        name = ' '.join(self.cleaned_data.get(field, '').split())  # tidy extra spaces
        if name and not NAME_PATTERN.match(name):
            raise forms.ValidationError(f'{label} can only contain letters, spaces, hyphens and apostrophes.')
        return name

    def clean_first_name(self):
        return self._clean_name('first_name', 'First name')

    def clean_surname(self):
        return self._clean_name('surname', 'Surname')

    def _clean_email_format(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        # Django has already checked the basic format; also insist on a real domain.
        domain = email.rpartition('@')[2]
        if ' ' in email or '.' not in domain or domain.startswith('.') or domain.endswith('.'):
            raise forms.ValidationError('Enter a valid email address.')
        return email

    def clean_phone_number(self):
        """Accepts 876-555-1234, (876) 555-1234, 876 555 1234, 8765551234 or +1 876 555 1234,
        and saves it in one standard format."""
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            return ''
        message = 'Enter a valid phone number, e.g. 876-555-1234.'
        if not PHONE_ALLOWED.match(phone):
            raise forms.ValidationError(message)  # letters or other symbols
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]  # drop the North American country code
        if len(digits) == 10:
            return f'{digits[:3]}-{digits[3:6]}-{digits[6:]}'
        if len(digits) == 7:
            return f'{digits[:3]}-{digits[3:]}'
        if phone.startswith('+') and 8 <= len(digits) <= 15:
            return '+' + digits  # an overseas number
        raise forms.ValidationError(message)


PHONE_WIDGET = forms.TextInput(attrs={'type': 'tel', 'inputmode': 'tel', 'autocomplete': 'tel'})


class ClubMemberForm(PersonDetailsMixin, forms.ModelForm):
    class Meta:
        model = ClubMember
        fields = ['first_name', 'surname', 'faculty', 'email', 'phone_number', 'address',
                  'membership_status', 'role']
        labels = {'phone_number': 'Phone number'}
        widgets = {'phone_number': PHONE_WIDGET}

    def __init__(self, *args, can_manage_roles=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].choices = [('', 'Select a faculty')] + FACULTY_CHOICES
        role = self.fields['role']
        role.queryset = Group.objects.order_by('name')
        role.empty_label = None
        role.required = False
        if not can_manage_roles:
            # Only role managers may change roles, so nobody can promote themselves.
            role.disabled = True
            role.help_text = ('New members start as Member. Only the President (or anyone whose role '
                              'can manage roles) can assign executive roles.')
            if not self.instance.pk:
                role.initial = Group.objects.filter(name=ClubMember.DEFAULT_ROLE).first()

    def clean_email(self):
        email = self._clean_email_format()
        member = self.instance
        # The email is the member's login username, so two logins cannot share one.
        if (member.pk and member.user and '@' in member.user.username
                and email.lower() != member.user.username.lower()):
            if User.objects.filter(username__iexact=email).exclude(pk=member.user.pk).exists():
                raise forms.ValidationError('Another login already uses this email address.')
        return email


class MemberSearchForm(forms.Form):
    first_name = forms.CharField(required=False)
    surname = forms.CharField(required=False)
    faculty = forms.ChoiceField(required=False, choices=[('', 'Any faculty')] + FACULTY_CHOICES)
    status = forms.ChoiceField(required=False,
                               choices=[('', 'Any status')] + ClubMember.STATUS_CHOICES)


class RoleForm(forms.Form):
    name = forms.CharField(max_length=150, label='Role name')
    capabilities = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple,
        choices=[(key, label) for key, label, _help, _perms in CAPABILITIES],
        label='This role can')

    def __init__(self, *args, role=None, **kwargs):
        self.role = role
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        clash = Group.objects.filter(name__iexact=name)
        if self.role:
            clash = clash.exclude(pk=self.role.pk)
        if clash.exists():
            raise forms.ValidationError('A role with this name already exists.')
        if name in LOCKED_ROLES:
            raise forms.ValidationError(f'"{name}" is a locked role name.')
        return name


class EmailLoginForm(AuthenticationForm):
    """Members log in with their email address (phones show the email keyboard)."""
    username = forms.CharField(label='Email', widget=forms.EmailInput(
        attrs={'autofocus': True, 'autocomplete': 'email'}))

    access_restricted = False

    def clean(self):
        try:
            return super().clean()
        except forms.ValidationError:
            # A3.3: a removed member who enters their correct details is told their
            # membership is no longer active, instead of "incorrect email or password".
            if self._is_removed_member():
                self.access_restricted = True
                raise forms.ValidationError('Account Access Restricted', code='removed')
            raise

    def _is_removed_member(self):
        username = self.cleaned_data.get('username', '')
        password = self.cleaned_data.get('password', '')
        user = (User.objects.filter(username__iexact=username).first()
                or User.objects.filter(email__iexact=username).first())
        member = getattr(user, 'club_member', None) if user else None
        return bool(member and member.is_removed and not user.is_active and user.check_password(password))


class MembershipApplicationForm(PersonDetailsMixin, forms.ModelForm):
    """The public Join form: the same details as the Add member form."""
    class Meta:
        model = MembershipApplication
        fields = MembershipApplication.FORM_FIELDS
        labels = {'phone_number': 'Phone number'}
        widgets = {'phone_number': PHONE_WIDGET}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].choices = [('', 'Select a faculty')] + FACULTY_CHOICES

    def clean_email(self):
        email = self._clean_email_format()
        if ClubMember.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email already belongs to a club member. '
                                        'Log in instead, or ask the Secretary for help.')
        if MembershipApplication.objects.filter(email__iexact=email,
                                                status=MembershipApplication.STATUS_PENDING).exists():
            raise forms.ValidationError('An application with this email is already waiting for review.')
        return email
