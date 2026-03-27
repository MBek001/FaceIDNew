# Telegram Bot Documentation

## Running the Bot

```bash
python -m apps.bot.main
```

The bot uses aiogram 3.x with long polling. It sets up Django before starting so all models are available.

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Begin registration, or confirm already registered |

No other commands are implemented. The bot is single-purpose: face registration.

---

## FSM States and Transitions

```
(no state) ──/start──► waiting_email
                │
                ├── already registered ──► (clear state, end)
                │
                ▼
          waiting_email
                │
                ├── invalid email format ──► stay in waiting_email
                ├── email not found ──► (clear state, end)
                ├── email already linked ──► (clear state, end)
                │
                ▼
          waiting_photo
                │
                ├── non-photo message ──► stay in waiting_photo
                ├── no face in photo ──► stay in waiting_photo
                ├── multiple faces ──► stay in waiting_photo
                │
                ▼
        (save encoding, clear state)
                │
                ▼
             (end)
```

FSM storage uses `MemoryStorage`. State is lost if the bot process restarts, but users simply need to run `/start` again.

---

## Photo Validation Rules

1. The message must contain a Telegram photo (not a file/document).
2. The largest resolution version is downloaded (`message.photo[-1]`).
3. The image is opened with Pillow and converted to RGB.
4. `face_recognition.face_locations()` must return exactly 1 face.
5. If 0 faces: user is asked to retry with better lighting.
6. If 2+ faces: user is asked to be alone in the frame.
7. `face_recognition.face_encodings()` extracts the 128-float vector.
8. The encoding is serialized as JSON and stored in `User.face_encoding`.

---

## Error Messages and Their Causes

| Situation | Message Sent |
|---|---|
| Already registered | "Siz allaqachon ro'yxatdan o'tgansiz." |
| Invalid email format | "Noto'g'ri email format. Iltimos qaytadan kiriting:" |
| Email not in DB or not active | "Bu email topilmadi. Admin bilan bog'laning." |
| Email linked to another Telegram account | "Bu email boshqa Telegram akkauntga bog'liq." |
| Photo contains no face | "Rasmda yuz aniqlanmadi. Yaxshiroq yorug'likda..." |
| Photo contains multiple faces | "Bir nechta yuz aniqlandi. Faqat siz ko'rinishingiz kerak." |
| Non-photo message during photo step | "Iltimos rasm yuboring. Hujjat yoki fayl emas..." |
| Success | "✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!" |
