import pytz
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.core.files.base import ContentFile

from apps.attendance.models import AttendanceEvent, ACTION_CAME, ACTION_GONE
from apps.attendance.services import (
    decode_image_to_rgb_array,
    extract_face_encoding,
    find_matching_user,
    get_client_ip,
)
from apps.sessions.tasks import compute_and_notify

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


class TerminalView(TemplateView):
    template_name = 'terminal/index.html'


class ScanView(View):
    def post(self, request):
        action = request.POST.get('action')
        if action not in (ACTION_CAME, ACTION_GONE):
            return JsonResponse({'error': "Noto'g'ri amal."}, status=400)

        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({'error': 'Rasm yuborilmadi.'}, status=400)

        image_bytes = image_file.read()

        rgb_array = decode_image_to_rgb_array(image_bytes)
        face_encoding, error = extract_face_encoding(rgb_array)

        if error:
            return JsonResponse({'error': error}, status=422)

        matched_user, distance = find_matching_user(face_encoding)

        if matched_user is None:
            return JsonResponse(
                {'error': "Yuz tanilmadi. Avval ro'yxatdan o'ting."},
                status=401
            )

        now_tashkent = datetime.now(TASHKENT_TZ)

        photo_filename = (
            f"{matched_user.id}_{action}_{now_tashkent.strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        photo_content = ContentFile(image_bytes, name=photo_filename)

        event = AttendanceEvent.objects.create(
            user=matched_user,
            scanned_at=now_tashkent,
            action=action,
            photo=photo_content,
            face_confidence=round(float(distance), 4),
            terminal_ip=get_client_ip(request),
        )

        compute_and_notify.delay(event.id)

        return JsonResponse({
            'success': True,
            'user_name': matched_user.name,
            'department': matched_user.department,
            'action': action,
            'scanned_at': now_tashkent.strftime('%H:%M'),
        })
