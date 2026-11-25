from datetime import datetime, timedelta

from django import forms
from django.db.models import Q
from django.utils import timezone

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'date', 'start_time', 'end_time', 'location', 'description', 'flyer']
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'rc-date', 'placeholder': 'dd/mm/yyyy', 'autocomplete': 'off'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    MAX_FLYER_MB = 5

    def __init__(self, *args, allow_clash=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_clash = allow_clash
        self.clashes = []
        self.fields['date'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['end_time'].required = True  # A6.2: every field except description and flyer
        self.fields['flyer'].help_text = 'JPG, PNG or PDF, up to 5 MB.'

    def find_clashes(self, date, start, end):
        """A6.3: other events on the same date whose times overlap this one."""
        def span(s, e):
            begin = datetime.combine(date, s)
            return begin, datetime.combine(date, e) if e else begin + timedelta(minutes=1)
        new_start, new_end = span(start, end)
        others = Event.objects.filter(is_removed=False, date=date).exclude(pk=self.instance.pk)
        return [e for e in others
                if span(e.start_time, e.end_time)[0] < new_end and new_start < span(e.start_time, e.end_time)[1]]

    def clean_flyer(self):
        flyer = self.cleaned_data.get('flyer')
        if flyer and hasattr(flyer, 'size') and flyer.size > self.MAX_FLYER_MB * 1024 * 1024:
            raise forms.ValidationError(f'The flyer must be {self.MAX_FLYER_MB} MB or smaller.')
        return flyer

    def clean(self):
        data = super().clean()
        date, start, end = data.get('date'), data.get('start_time'), data.get('end_time')
        today, now = timezone.localdate(), timezone.localtime().time()
        if date and date < today:
            self.add_error('date', 'The event date cannot be in the past.')
        elif date == today and start and start < now:
            self.add_error('start_time', 'The start time has already passed.')
        if start and end and end <= start:
            self.add_error('end_time', 'The end time must be after the start time.')
        if date and start and end and not self.errors:
            self.clashes = self.find_clashes(date, start, end)
            if self.clashes and not self.allow_clash:
                raise forms.ValidationError(
                    'This event overlaps another event on the same date. Tick "Save anyway" to add it, '
                    'or Cancel.', code='clash')
        return data


class EventSearchForm(forms.Form):
    """Search upcoming events by name, location or description, and/or by date."""
    q = forms.CharField(required=False, label='Search events', max_length=100,
                        widget=forms.TextInput(attrs={'type': 'search', 'class': 'form-control', 'placeholder': 'Name, location or description'}))
    date = forms.DateField(required=False, label='Date', input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                           widget=forms.DateInput(format='%Y-%m-%d', attrs={
                               'class': 'form-control rc-date', 'placeholder': 'dd/mm/yyyy', 'autocomplete': 'off'}))

    def is_searching(self):
        return self.is_valid() and bool(self.cleaned_data['q'].strip() or self.cleaned_data['date'])

    def apply(self, events):
        """Narrow a queryset of events to those matching the search."""
        if not self.is_searching():
            return events
        words, date = self.cleaned_data['q'].strip(), self.cleaned_data['date']
        if words:
            events = events.filter(Q(title__icontains=words) | Q(location__icontains=words)
                                   | Q(description__icontains=words))
        if date:
            events = events.filter(date=date)
        return events
