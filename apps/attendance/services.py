import io
import numpy as np
from PIL import Image
from django.conf import settings
from apps.users.models import User


def decode_image_to_rgb_array(image_bytes):
    pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return np.array(pil_image)


def extract_face_encoding(rgb_array):
    import face_recognition
    locations = face_recognition.face_locations(rgb_array)

    if len(locations) == 0:
        return None, "Rasm tanda yuz aniqlanmadi. Kameraga to'g'ridan qarang."

    if len(locations) > 1:
        return None, "Bir nechta yuz aniqlandi. Faqat siz bo'lishingiz kerak."

    encodings = face_recognition.face_encodings(rgb_array, locations)
    return encodings[0], None


def find_matching_user(face_encoding_array):
    import face_recognition
    registered_users = User.objects.filter(
        is_face_registered=True,
        is_active=True
    )

    best_user = None
    best_distance = 1.0

    for user in registered_users:
        stored_encoding = user.get_face_encoding_array()
        if stored_encoding is None:
            continue

        distances = face_recognition.face_distance(
            [stored_encoding], face_encoding_array
        )
        distance = distances[0]

        if distance < settings.FACE_TOLERANCE and distance < best_distance:
            best_distance = distance
            best_user = user

    return best_user, best_distance


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
