"""Events app – Controller component (MVC): EventController in the SDS.
One module per SRS feature:

  add_event.py      A6  Add event (plus the calendar, list and search)
  delete_events.py  A7  Delete selected events
"""
from .add_event import event_add, event_feed, event_ics, event_list
from .delete_events import event_delete, removed_list

__all__ = ['event_add', 'event_delete', 'event_feed', 'event_ics', 'event_list', 'removed_list']
