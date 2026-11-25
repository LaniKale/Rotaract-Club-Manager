"""A6 – Add event, plus the calendar, list and event search every member sees."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from members.models import ChangeLog
from members.navigation import back_url

from ..forms import EventForm, EventSearchForm
from ..models import Event


@login_required
def event_list(request):
    """Events, visible to every logged-in user: a calendar view and a list of upcoming events.
    A search always shows its results in the list view."""
    search = EventSearchForm(request.GET or None)
    events = search.apply(Event.objects.filter(is_removed=False, date__gte=timezone.localdate()))
    searching = search.is_searching()
    view = 'list' if request.GET.get('view') == 'list' or searching else 'calendar'
    return render(request, 'events/event_list.html', {
        'events': events, 'view': view, 'search': search, 'searching': searching})


@permission_required('events.add_event', raise_exception=True)
def event_add(request):
    """A6: add an event."""
    form = EventForm(request.POST or None, request.FILES or None,
                     allow_clash=request.POST.get('confirm_clash') == '1')
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            event = form.save()
            ChangeLog.log_change(request.user, 'Event', event.pk, 'Add', new_value=event.title)
        messages.success(request, f'"{event.title}" was added.')
        return redirect('events:list')
    return render(request, 'events/event_form.html', {
        'form': form, 'title': 'Add event', 'cancel_url': back_url(request, 'events:list')})


@login_required
def event_feed(request):
    """Calendar data (JSON) for FullCalendar. FullCalendar asks for the dates it is showing."""
    events = Event.objects.filter(is_removed=False)
    start, end = request.GET.get('start', '')[:10], request.GET.get('end', '')[:10]
    if start and end:
        events = events.filter(date__gte=start, date__lt=end)
    data = []
    for e in events.select_related('meeting'):
        data.append({
            'id': e.pk,
            'title': e.title,
            'start': e.start_datetime.isoformat(),
            'end': e.end_datetime.isoformat(),
            'classNames': ['rc-meeting' if e.is_meeting else 'rc-event'],
            'extendedProps': {
                'isMeeting': e.is_meeting,
                'date': e.date.strftime('%A, %d/%m/%Y'),
                'time': e.start_time.strftime('%I:%M %p').lstrip('0')
                        + (f" – {e.end_time.strftime('%I:%M %p').lstrip('0')}" if e.end_time else ''),
                'location': e.location,
                'description': e.description,
                'flyer': e.flyer.url if e.flyer else '',
                'flyerIsImage': e.flyer_is_image,
                'google': e.google_calendar_url,
                'ics': reverse('events:ics', args=[e.pk]),
            },
        })
    return JsonResponse(data, safe=False)


@login_required
def event_ics(request, pk):
    """Download one event as an .ics file (Apple Calendar, Outlook, etc.)."""
    event = get_object_or_404(Event, pk=pk, is_removed=False)
    response = HttpResponse(event.to_ics(), content_type='text/calendar; charset=utf-8')
    filename = slugify(event.title) or 'event'
    response['Content-Disposition'] = f'attachment; filename="{filename}.ics"'
    return response
