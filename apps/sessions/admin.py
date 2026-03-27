from django.contrib import admin
from django.contrib import messages
from apps.sessions.models import WorkSession, AdminNotifyConfig
from apps.sessions.tasks import send_shift_reports


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'session_date', 'shift', 'computed_came_at',
        'computed_gone_at', 'work_hours_display', 'status', 'is_sent'
    ]
    list_filter = ['status', 'is_sent', 'shift', 'session_date']
    search_fields = ['user__name', 'user__email']
    readonly_fields = [
        'came_event', 'gone_event', 'computed_came_at', 'computed_gone_at',
        'work_minutes', 'computed_at', 'api_response', 'sent_at'
    ]
    date_hierarchy = 'session_date'
    actions = ['send_to_api_now', 'recompute_selected']

    def work_hours_display(self, obj):
        return obj.work_hours_display
    work_hours_display.short_description = 'Work Hours'

    def send_to_api_now(self, request, queryset):
        send_shift_reports.delay()
        self.message_user(request, "Report sending task triggered.", messages.SUCCESS)
    send_to_api_now.short_description = "Trigger report send now"

    def recompute_selected(self, request, queryset):
        from apps.sessions.services import compute_session_for_user_date
        count = 0
        for session in queryset.filter(is_sent=False):
            compute_session_for_user_date(session.user, session.session_date)
            count += 1
        self.message_user(request, f"Recomputed {count} sessions.", messages.SUCCESS)
    recompute_selected.short_description = "Recompute selected sessions"


@admin.register(AdminNotifyConfig)
class AdminNotifyConfigAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'telegram_id', 'notify_on_came', 'notify_on_gone',
        'notify_on_report_sent', 'notify_on_report_failed'
    ]
