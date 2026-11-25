from django.contrib import admin

from .models import AttendanceRecord, Meeting, QRCode


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time', 'location']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['member', 'meeting', 'timestamp', 'method']
    list_filter = ['method', 'meeting']


admin.site.register(QRCode)
