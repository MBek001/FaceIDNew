import pytz
from datetime import datetime, date, timedelta

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


def get_session_date(shift, aware_datetime):
    local_dt = aware_datetime.astimezone(TASHKENT_TZ)
    local_time = local_dt.time()
    local_date = local_dt.date()

    if shift.is_night_shift and local_time < shift.shift_end:
        return local_date - timedelta(days=1)

    return local_date


def compute_status(shift, came_at_aware):
    from apps.sessions.models import STATUS_PRESENT, STATUS_LATE
    local_came = came_at_aware.astimezone(TASHKENT_TZ)
    came_time = local_came.time()

    threshold_dt = datetime.combine(
        date.today(), shift.shift_start
    ) + timedelta(minutes=shift.late_threshold_minutes)
    threshold_time = threshold_dt.time()

    if came_time <= threshold_time:
        return STATUS_PRESENT
    return STATUS_LATE
