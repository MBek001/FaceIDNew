import asyncio
import requests
import pytz
import time
from datetime import datetime, timedelta, date
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.sessions.models import AdminNotifyConfig, WorkSession
from apps.attendance.models import AttendanceEvent, ACTION_CAME
from apps.sessions.services import compute_session_for_user_date
from apps.shifts.services import get_session_date
from apps.shifts.models import Shift, UserShift

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


@shared_task
def compute_and_notify(event_id):
    event = AttendanceEvent.objects.select_related('user').get(id=event_id)
    user = event.user
    shift = user.get_current_shift()

    if shift:
        session_date = get_session_date(shift, event.scanned_at)
        compute_session_for_user_date(user, session_date)

    notify_admins_of_event(event_id)


def notify_admins_of_event(event_id):
    from aiogram import Bot
    from aiogram.types import FSInputFile

    event = AttendanceEvent.objects.select_related('user').get(id=event_id)
    user = event.user
    local_time = event.scanned_at.astimezone(TASHKENT_TZ).strftime('%H:%M')

    if event.action == ACTION_CAME:
        recipients = AdminNotifyConfig.objects.filter(notify_on_came=True)
        session = getattr(event, 'came_session', None)
        status_text = session.status if session else 'hisoblanmoqda'
        caption = (
            f"✅ Keldi\n"
            f"👤 {user.name}\n"
            f"🏢 {user.department} — {user.position}\n"
            f"🕐 {local_time}\n"
            f"📊 Holat: {status_text}"
        )
    else:
        recipients = AdminNotifyConfig.objects.filter(notify_on_gone=True)
        session = getattr(event, 'gone_session', None)
        hours_text = session.work_hours_display if session else '—'
        caption = (
            f"🚪 Ketdi\n"
            f"👤 {user.name}\n"
            f"🏢 {user.department}\n"
            f"🕐 {local_time}\n"
            f"⏱ Ish vaqti: {hours_text}"
        )

    if not recipients.exists():
        return

    bot = Bot(token=settings.BOT_TOKEN)

    async def send_to_all():
        for admin_config in recipients:
            try:
                await bot.send_photo(
                    chat_id=admin_config.telegram_id,
                    photo=FSInputFile(event.photo.path),
                    caption=caption
                )
            except Exception:
                pass
        await bot.session.close()

    asyncio.run(send_to_all())


@shared_task
def notify_admins_error(message):
    from aiogram import Bot

    recipients = AdminNotifyConfig.objects.filter(notify_on_report_failed=True)
    if not recipients.exists():
        return

    bot = Bot(token=settings.BOT_TOKEN)

    async def send_to_all():
        for admin_config in recipients:
            try:
                await bot.send_message(
                    chat_id=admin_config.telegram_id,
                    text=f"⚠️ Tizim xatosi:\n{message}"
                )
            except Exception:
                pass
        await bot.session.close()

    asyncio.run(send_to_all())


@shared_task
def send_shift_reports():
    from aiogram import Bot

    now_tashkent = datetime.now(TASHKENT_TZ)
    current_time = now_tashkent.time()

    for shift in Shift.objects.all():
        fire_time = shift.report_fire_time
        fire_datetime = datetime.combine(date.today(), fire_time)
        window_start = (fire_datetime - timedelta(minutes=2, seconds=30)).time()
        window_end = (fire_datetime + timedelta(minutes=2, seconds=30)).time()

        if not (window_start <= current_time <= window_end):
            continue

        session_date = get_session_date(shift, now_tashkent)

        assigned_user_ids = (
            UserShift.objects
            .filter(shift=shift, effective_from__lte=date.today())
            .order_by('user_id', '-effective_from')
            .distinct('user_id')
            .values_list('user_id', flat=True)
        )

        sessions = WorkSession.objects.filter(
            user_id__in=assigned_user_ids,
            session_date=session_date,
            is_sent=False
        ).select_related('user')

        sent_count = 0
        failed_count = 0

        for session in sessions:
            came_at = session.computed_came_at.astimezone(TASHKENT_TZ) if session.computed_came_at else None
            gone_at = session.computed_gone_at.astimezone(TASHKENT_TZ) if session.computed_gone_at else None

            if not session.user.attendance_user_id:
                failed_count += 1
                continue

            payload = {
                'employee_id': session.user.attendance_user_id,
                'attendance_date': str(session.session_date),
                'check_in_time': came_at.strftime('%H:%M:%S') if came_at else None,
            }
            if gone_at:
                payload['check_out_time'] = gone_at.strftime('%H:%M:%S')

            success = False
            api_response_data = None

            for attempt in range(3):
                try:
                    headers = {'X-Attendance-Key': settings.ATTENDANCE_API_KEY}

                    response = requests.post(
                        f'{settings.EXTERNAL_API_URL}/attendance/records',
                        json=payload,
                        headers=headers,
                        timeout=15
                    )
                    response.raise_for_status()
                    api_response_data = response.json()
                    success = True
                    break
                except Exception:
                    if attempt < 2:
                        time.sleep(5)

            if success:
                session.is_sent = True
                session.sent_at = timezone.now()
                session.api_response = api_response_data
                session.save(update_fields=['is_sent', 'sent_at', 'api_response'])
                sent_count += 1
            else:
                failed_count += 1

        if failed_count > 0:
            notify_admins_error.delay(
                f"Shift '{shift.name}' uchun {failed_count} ta hisobot yuborilmadi."
            )

        if sent_count > 0:
            recipients = AdminNotifyConfig.objects.filter(notify_on_report_sent=True)
            if recipients.exists():
                bot = Bot(token=settings.BOT_TOKEN)

                async def send_report_summary():
                    msg = (
                        f"📊 Hisobot yuborildi\n"
                        f"Shift: {shift.name}\n"
                        f"Sana: {session_date}\n"
                        f"Yuborildi: {sent_count} ta"
                    )
                    for admin_config in recipients:
                        try:
                            await bot.send_message(
                                chat_id=admin_config.telegram_id,
                                text=msg
                            )
                        except Exception:
                            pass
                    await bot.session.close()

                asyncio.run(send_report_summary())
