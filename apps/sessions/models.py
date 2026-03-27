from django.db import models

STATUS_PRESENT = 'present'
STATUS_LATE = 'late'
STATUS_ABSENT = 'absent'
STATUS_INCOMPLETE = 'incomplete'

STATUS_CHOICES = [
    (STATUS_PRESENT, 'Present'),
    (STATUS_LATE, 'Late'),
    (STATUS_ABSENT, 'Absent'),
    (STATUS_INCOMPLETE, 'Incomplete'),
]


class WorkSession(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='work_sessions'
    )
    session_date = models.DateField()
    shift = models.ForeignKey(
        'shifts.Shift',
        on_delete=models.PROTECT
    )
    came_event = models.OneToOneField(
        'attendance.AttendanceEvent',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='came_session'
    )
    gone_event = models.OneToOneField(
        'attendance.AttendanceEvent',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='gone_session'
    )
    computed_came_at = models.DateTimeField(null=True, blank=True)
    computed_gone_at = models.DateTimeField(null=True, blank=True)
    work_minutes = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    api_response = models.JSONField(null=True, blank=True)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'session_date')
        ordering = ['-session_date']
        verbose_name = 'Work Session'
        verbose_name_plural = 'Work Sessions'

    def __str__(self):
        return f"{self.user.name} — {self.session_date} — {self.status}"

    @property
    def work_hours_display(self):
        if self.work_minutes is None:
            return None
        hours = self.work_minutes // 60
        minutes = self.work_minutes % 60
        return f"{hours}h {minutes}m"


class AdminNotifyConfig(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=150)
    notify_on_came = models.BooleanField(default=True)
    notify_on_gone = models.BooleanField(default=True)
    notify_on_report_sent = models.BooleanField(default=True)
    notify_on_report_failed = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Admin Notification Config'
        verbose_name_plural = 'Admin Notification Configs'

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"
