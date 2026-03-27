from django.contrib import admin
from django.contrib import messages
from apps.users.models import User
from apps.users.services import sync_users_from_api
from apps.shifts.models import UserShift


class UserShiftInline(admin.TabularInline):
    model = UserShift
    extra = 1
    fields = ['shift', 'effective_from']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'department', 'position',
        'is_face_registered', 'is_active', 'synced_at'
    ]
    list_filter = ['is_active', 'is_face_registered', 'department']
    search_fields = ['name', 'email']
    readonly_fields = ['synced_at', 'face_encoding', 'telegram_id']
    inlines = [UserShiftInline]
    actions = ['sync_from_api', 'recompute_sessions']

    def sync_from_api(self, request, queryset):
        try:
            result = sync_users_from_api()
            self.message_user(
                request,
                f"Sync complete: {result['created']} created, "
                f"{result['updated']} updated, {result['deactivated']} deactivated.",
                messages.SUCCESS
            )
        except Exception as exc:
            self.message_user(request, f"Sync failed: {exc}", messages.ERROR)
    sync_from_api.short_description = "Sync users from external API"

    def recompute_sessions(self, request, queryset):
        from datetime import timedelta
        from apps.sessions.services import compute_session_for_user_date
        from apps.shifts.services import get_session_date
        from apps.attendance.models import AttendanceEvent

        count = 0
        for user in queryset:
            shift = user.get_current_shift()
            if not shift:
                continue
            events = AttendanceEvent.objects.filter(user=user)
            session_dates = set()
            for event in events:
                sd = get_session_date(shift, event.scanned_at)
                session_dates.add(sd)
            for sd in session_dates:
                compute_session_for_user_date(user, sd)
                count += 1

        self.message_user(
            request,
            f"Recomputed {count} sessions for {queryset.count()} employees.",
            messages.SUCCESS
        )
    recompute_sessions.short_description = "Recompute work sessions"
