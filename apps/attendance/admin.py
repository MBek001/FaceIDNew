from django.contrib import admin
from apps.attendance.models import AttendanceEvent


@admin.register(AttendanceEvent)
class AttendanceEventAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'action', 'scanned_at', 'face_confidence', 'terminal_ip'
    ]
    list_filter = ['action', 'scanned_at']
    search_fields = ['user__name', 'user__email']
    readonly_fields = [
        'user', 'scanned_at', 'action', 'photo',
        'face_confidence', 'terminal_ip', 'created_at'
    ]
    date_hierarchy = 'scanned_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
