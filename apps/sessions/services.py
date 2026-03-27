from datetime import timedelta
from apps.attendance.models import AttendanceEvent, ACTION_CAME, ACTION_GONE
from apps.sessions.models import (
    WorkSession, STATUS_ABSENT, STATUS_INCOMPLETE
)
from apps.shifts.services import get_session_date, compute_status


def compute_session_for_user_date(user, session_date):
    shift = user.get_current_shift()
    if shift is None:
        return None

    search_dates = [session_date, session_date + timedelta(days=1)]
    events = AttendanceEvent.objects.filter(
        user=user,
        scanned_at__date__in=search_dates
    ).order_by('scanned_at')

    came_event = None
    gone_event = None

    for event in events:
        event_session_date = get_session_date(shift, event.scanned_at)
        if event_session_date != session_date:
            continue
        if event.action == ACTION_CAME and came_event is None:
            came_event = event
        elif event.action == ACTION_GONE and gone_event is None:
            gone_event = event

    if came_event is None and gone_event is None:
        return None

    work_minutes = None
    if came_event and gone_event:
        delta = gone_event.scanned_at - came_event.scanned_at
        work_minutes = int(delta.total_seconds() / 60)

    if came_event:
        status = compute_status(shift, came_event.scanned_at)
        if gone_event is None:
            status = STATUS_INCOMPLETE
    else:
        status = STATUS_ABSENT

    session, _ = WorkSession.objects.update_or_create(
        user=user,
        session_date=session_date,
        defaults={
            'shift': shift,
            'came_event': came_event,
            'gone_event': gone_event,
            'computed_came_at': came_event.scanned_at if came_event else None,
            'computed_gone_at': gone_event.scanned_at if gone_event else None,
            'work_minutes': work_minutes,
            'status': status,
        }
    )
    return session
