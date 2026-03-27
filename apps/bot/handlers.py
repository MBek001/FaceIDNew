import io
import json
import numpy as np
from PIL import Image
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from apps.bot.states import RegistrationStates
from apps.users.models import User

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    existing = User.objects.filter(telegram_id=message.from_user.id).first()
    if existing:
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz.\n"
            "Ofis terminalidan foydalanishingiz mumkin."
        )
        return

    await state.set_state(RegistrationStates.waiting_email)
    await message.answer(
        "Xush kelibsiz!\n\n"
        "Iltimos, ish emailingizni kiriting:"
    )


@router.message(RegistrationStates.waiting_email)
async def handle_email(message: Message, state: FSMContext):
    email = message.text.strip().lower()

    if '@' not in email or '.' not in email.split('@')[-1]:
        await message.answer("Noto'g'ri email format. Iltimos qaytadan kiriting:")
        return

    user = User.objects.filter(email=email, is_active=True).first()

    if user is None:
        await message.answer(
            "Bu email topilmadi.\n"
            "Admin bilan bog'laning."
        )
        return

    if user.telegram_id is not None:
        await message.answer(
            "Bu email boshqa Telegram akkauntga bog'liq.\n"
            "Admin bilan bog'laning."
        )
        return

    await state.update_data(email=email, user_id=user.id)
    await state.set_state(RegistrationStates.waiting_photo)
    await message.answer(
        f"Email tasdiqlandi! Salom, {user.name}!\n\n"
        "Endi yuzingizning rasmini yuboring.\n\n"
        "Eslatma:\n"
        "— Yaxshi yorug'lik bo'lsin\n"
        "— Ko'zoynaksiz bo'ling\n"
        "— Kameraga to'g'ridan qarang\n"
        "— Faqat siz ko'rinishingiz kerak"
    )


@router.message(RegistrationStates.waiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    import face_recognition
    fsm_data = await state.get_data()
    user = User.objects.get(id=fsm_data['user_id'])

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)

    photo_bytes = io.BytesIO()
    await message.bot.download_file(file.file_path, photo_bytes)
    photo_bytes.seek(0)

    pil_image = Image.open(photo_bytes).convert('RGB')
    rgb_array = np.array(pil_image)

    locations = face_recognition.face_locations(rgb_array)

    if len(locations) == 0:
        await message.answer(
            "Rasmda yuz aniqlanmadi.\n"
            "Yaxshiroq yorug'likda qaytadan urinib ko'ring:"
        )
        return

    if len(locations) > 1:
        await message.answer(
            "Bir nechta yuz aniqlandi.\n"
            "Faqat siz ko'rinishingiz kerak. Qaytadan urinib ko'ring:"
        )
        return

    encoding = face_recognition.face_encodings(rgb_array, locations)[0]

    user.face_encoding = json.dumps(encoding.tolist())
    user.telegram_id = message.from_user.id
    user.is_face_registered = True
    user.save(update_fields=['face_encoding', 'telegram_id', 'is_face_registered'])

    await state.clear()
    await message.answer(
        "✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!\n\n"
        "Endi ofis terminalida Keldi/Ketdi tugmalaridan foydalanishingiz mumkin."
    )


@router.message(RegistrationStates.waiting_photo)
async def handle_non_photo_in_photo_state(message: Message, state: FSMContext):
    await message.answer(
        "Iltimos rasm yuboring.\n"
        "Hujjat yoki fayl emas, oddiy rasm (foto) bo'lishi kerak."
    )
