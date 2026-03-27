from datetime import datetime, timedelta
from django.db import models


class Shift(models.Model):
    name = models.CharField(max_length=100)
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    late_threshold_minutes = models.IntegerField(default=15)
    report_delay_hours = models.IntegerField(default=2)

    class Meta:
        ordering = ['shift_start']
        verbose_name = 'Shift'
        verbose_name_plural = 'Shifts'

    def __str__(self):
        return f"{self.name} ({self.shift_start.strftime('%H:%M')} - {self.shift_end.strftime('%H:%M')})"

    @property
    def is_night_shift(self):
        return self.shift_end < self.shift_start

    @property
    def report_fire_time(self):
        from datetime import date
        base = datetime.combine(date.today(), self.shift_end)
        return (base + timedelta(hours=self.report_delay_hours)).time()


class UserShift(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='shift_assignments'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='user_assignments'
    )
    effective_from = models.DateField()

    class Meta:
        ordering = ['-effective_from']
        unique_together = ('user', 'effective_from')
        verbose_name = 'User Shift Assignment'
        verbose_name_plural = 'User Shift Assignments'

    def __str__(self):
        return f"{self.user.name} → {self.shift.name} from {self.effective_from}"
