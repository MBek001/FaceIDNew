import requests
from django.conf import settings
from django.utils import timezone
from apps.users.models import User


def sync_users_from_api():
    headers = {'X-Attendance-Key': settings.ATTENDANCE_API_KEY}

    response = requests.get(
        f'{settings.EXTERNAL_API_URL}/attendance/users',
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    api_users = data.get('items', [])

    api_user_ids = set()
    created_count = 0
    updated_count = 0

    for user_data in api_users:
        user_id = str(user_data['id'])
        api_user_ids.add(user_id)

        _, created = User.objects.update_or_create(
            id=user_id,
            defaults={
                'attendance_user_id': user_data['id'],
                'name': user_data.get('full_name') or user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'position': user_data.get('role', ''),
                'is_active': True,
                'synced_at': timezone.now(),
            }
        )
        if created:
            created_count += 1
        else:
            updated_count += 1

    deactivated_count = User.objects.exclude(
        id__in=api_user_ids
    ).filter(is_active=True).update(is_active=False)

    return {
        'created': created_count,
        'updated': updated_count,
        'deactivated': deactivated_count,
    }
