"""A7 – Delete selected events and the Removed Events list."""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from members.models import ChangeLog, describe_user

from ..forms import EventSearchForm
from ..models import Event, RemovedEvent


@permission_required('events.delete_event', raise_exception=True)
def event_delete(request):
    """A7: delete one or more selected events, after confirmation.
    Events are moved to the Removed Events list, never permanently deleted."""
    events = Event.objects.filter(is_removed=False, date__gte=timezone.localdate()).order_by('date', 'start_time')
    if request.method == 'POST':
        selected = events.filter(pk__in=request.POST.getlist('event_ids'))
        if not selected:
            messages.error(request, 'Select at least one event to delete.')
            return redirect('events:delete')
        if not request.POST.get('confirmed'):
            return render(request, 'events/event_delete_confirm.html', {'selected': selected})
        with transaction.atomic():
            for event in selected:
                event.is_removed = True
                event.save()
                RemovedEvent.objects.update_or_create(
                    event=event, defaults={'removed_by': describe_user(request.user)})
                ChangeLog.log_change(request.user, 'Event', event.pk, 'Remove',
                                     old_value=event.title)
        messages.success(request, f'{selected.count()} event(s) moved to the Removed Events list.')
        return redirect('events:list')
    search = EventSearchForm(request.GET or None)
    return render(request, 'events/event_delete.html', {
        'events': search.apply(events), 'search': search, 'searching': search.is_searching()})


@permission_required('events.view_event', raise_exception=True)
def removed_list(request):
    return render(request, 'events/removed_list.html',
                  {'removed': RemovedEvent.objects.select_related('event')})
