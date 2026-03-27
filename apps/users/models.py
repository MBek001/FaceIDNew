import json
import numpy as np
from django.db import models


class User(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
    face_encoding = models.TextField(null=True, blank=True)
    is_face_registered = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.name} ({self.email})"

    def get_face_encoding_array(self):
        if not self.face_encoding:
            return None
        return np.array(json.loads(self.face_encoding))

    def get_current_shift(self):
        from datetime import date
        today = date.today()
        assignment = self.shift_assignments.filter(
            effective_from__lte=today
        ).select_related('shift').order_by('-effective_from').first()
        return assignment.shift if assignment else None
