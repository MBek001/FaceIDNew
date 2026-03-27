from celery import shared_task
from apps.users.services import sync_users_from_api


@shared_task
def sync_users_task():
    try:
        result = sync_users_from_api()
        return result
    except Exception as exc:
        from apps.sessions.tasks import notify_admins_error
        notify_admins_error.delay(f"User sync failed: {str(exc)}")
        raise
