from django.db import models

ACTION_CAME = 'came'
ACTION_GONE = 'gone'
ACTION_CHOICES = [
    (ACTION_CAME, 'Keldi'),
    (ACTION_GONE, 'Ketdi'),
]


class AttendanceEvent(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='events'
    )
    scanned_at = models.DateTimeField()
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    photo = models.FileField(upload_to='attendance/%Y/%m/%d/')
    face_confidence = models.FloatField()
    terminal_ip = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scanned_at']
        verbose_name = 'Attendance Event'
        verbose_name_plural = 'Attendance Events'

    def __str__(self):
        action_label = 'Keldi' if self.action == ACTION_CAME else 'Ketdi'
        local_time = self.scanned_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.user.name} — {action_label} — {local_time}"
