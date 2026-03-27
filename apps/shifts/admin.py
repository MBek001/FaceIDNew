from django.contrib import admin
from apps.shifts.models import Shift, UserShift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'shift_start', 'shift_end',
        'is_night_shift_display', 'late_threshold_minutes',
        'report_delay_hours', 'report_fire_time_display'
    ]

    def is_night_shift_display(self, obj):
        return obj.is_night_shift
    is_night_shift_display.boolean = True
    is_night_shift_display.short_description = 'Night Shift'

    def report_fire_time_display(self, obj):
        return obj.report_fire_time.strftime('%H:%M')
    report_fire_time_display.short_description = 'Report Fires At'


@admin.register(UserShift)
class UserShiftAdmin(admin.ModelAdmin):
    list_display = ['user', 'shift', 'effective_from']
    list_filter = ['shift', 'effective_from']
    search_fields = ['user__name', 'user__email']
    autocomplete_fields = ['user']
