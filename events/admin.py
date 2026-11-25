from django.contrib import admin

from .models import Event, RemovedEvent


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time', 'location', 'is_removed']
    list_filter = ['is_removed']
    search_fields = ['title', 'location']


admin.site.register(RemovedEvent)
