from django.contrib import admin

from .models import ChangeLog, ClubMember, MembershipApplication, RemovedMember


@admin.register(ClubMember)
class ClubMemberAdmin(admin.ModelAdmin):
    list_display = ['surname', 'first_name', 'faculty', 'email', 'membership_status', 'role', 'is_removed']
    list_filter = ['membership_status', 'role', 'is_removed', 'faculty']
    search_fields = ['first_name', 'surname', 'email']


@admin.register(RemovedMember)
class RemovedMemberAdmin(admin.ModelAdmin):
    list_display = ['member', 'removal_date', 'removed_by']


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ['change_date', 'changed_by_display', 'action', 'record_type', 'record_id', 'field_name']
    list_filter = ['action', 'record_type']
    readonly_fields = [f.name for f in ChangeLog._meta.fields]


@admin.register(MembershipApplication)
class MembershipApplicationAdmin(admin.ModelAdmin):
    list_display = ['surname', 'first_name', 'email', 'status', 'submitted_at', 'reviewed_by']
    list_filter = ['status', 'faculty']
