from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.users.models import User


@method_decorator(login_required, name='dispatch')
class UserFaceResetView(View):
    def post(self, request, user_id):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Forbidden'}, status=403)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        user.face_encoding = None
        user.is_face_registered = False
        user.telegram_id = None
        user.save(update_fields=['face_encoding', 'is_face_registered', 'telegram_id'])

        return JsonResponse({'success': True})
