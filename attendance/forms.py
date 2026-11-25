from django import forms

from members.models import ClubMember


class ManualCheckInForm(forms.Form):
    member = forms.ModelChoiceField(queryset=ClubMember.objects.none(), label='Member')

    def __init__(self, *args, meeting=None, **kwargs):
        super().__init__(*args, **kwargs)
        present = meeting.attendance_records.values_list('member_id', flat=True) if meeting else []
        self.fields['member'].queryset = ClubMember.objects.filter(
            is_removed=False).exclude(pk__in=present)
