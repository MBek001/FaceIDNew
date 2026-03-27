# System Flows

## Flow 1: User Sync from External API

```
Celery Beat (2am daily)
    │
    ▼
sync_users_task() [apps/users/tasks.py]
    │
    ▼
sync_users_from_api() [apps/users/services.py]
    │
    ├── GET {EXTERNAL_API_URL}/get-users
    │       Authorization: Bearer {EXTERNAL_API_KEY}
    │
    ├── For each user in response:
    │       User.objects.update_or_create(id=user_data['id'], defaults={...})
    │
    └── Deactivate users not in response:
            User.objects.exclude(id__in=api_user_ids).update(is_active=False)

Returns: { created, updated, deactivated }
```

Can also be triggered manually from Django admin → User admin → "Sync users from external API" action.

---

## Flow 2: Telegram Bot Registration

FSM state diagram:

```
START command
    │
    ├── Already registered? ──► "Already registered" message. END.
    │
    ▼
[State: waiting_email]
    │
    User sends text
    │
    ├── Invalid email format? ──► Ask again.
    ├── Email not in DB? ──► "Not found" message. END.
    ├── Email already linked? ──► "Linked to another account" message. END.
    │
    ▼
[State: waiting_photo]
    │
    User sends photo (F.photo)
    │
    ├── Non-photo message? ──► "Send a photo" message.
    ├── No face detected? ──► "No face found" message. Ask again.
    ├── Multiple faces? ──► "Only you should be in the photo" message. Ask again.
    │
    ▼
face_recognition.face_encodings(rgb_array) → encoding (128-float array)

User.face_encoding = json.dumps(encoding.tolist())
User.telegram_id = message.from_user.id
User.is_face_registered = True
User.save()

state.clear()
    │
    ▼
"Registration complete" message. Bot flow ends.
```

---

## Flow 3: Office Terminal Scan

```
User presses KELDI or KETDI button on screen
    │
    ▼ (JS)
Webcam opens → countdown 3, 2, 1 → canvas.toBlob()
    │
    ▼
POST /terminal/scan/
    form data: image (JPEG blob), action (came|gone)
    header: X-CSRFToken

    │
    ▼ (ScanView.post)
1. Validate action field
2. Validate image present
3. decode_image_to_rgb_array(image_bytes) → numpy RGB array
4. extract_face_encoding(rgb_array)
    ├── No face → 422 {"error": "..."}
    └── Multiple faces → 422 {"error": "..."}
5. find_matching_user(face_encoding)
    ├── Compare against all is_face_registered=True users
    ├── Use face_recognition.face_distance()
    └── No match within FACE_TOLERANCE → 401 {"error": "..."}
6. AttendanceEvent.objects.create(...)
7. compute_and_notify.delay(event.id) ← async Celery task
8. Return 200 {"success": True, user_name, department, action, scanned_at}

    │ (browser)
    ▼
Show result card → wait 5 seconds → reset to buttons
```

---

## Flow 4: Admin Telegram Notification

Triggered inside `compute_and_notify` Celery task after session computation:

```
notify_admins_of_event(event_id)
    │
    ├── Fetch event + user
    ├── Determine recipients from AdminNotifyConfig
    │       (notify_on_came or notify_on_gone based on event.action)
    │
    ├── Build caption text (name, department, time, status/hours)
    │
    └── For each admin recipient:
            bot.send_photo(chat_id, FSInputFile(event.photo.path), caption)
```

For errors, `notify_admins_error` sends a plain text message to `notify_on_report_failed=True` recipients.

---

## Flow 5: Scheduled Report Sending with Night Shift Logic

Runs every 5 minutes via Celery Beat:

```
send_shift_reports() [apps/sessions/tasks.py]
    │
    ├── Get current time in Asia/Tashkent
    │
    └── For each Shift in DB:
            │
            ├── Compute report_fire_time = shift_end + report_delay_hours
            ├── Define window: fire_time ± 2.5 minutes
            │
            ├── Current time outside window? → skip this shift
            │
            ├── Compute session_date using get_session_date()
            │       For night shifts (end < start), if current time < shift_end,
            │       session_date = yesterday.
            │
            ├── Find assigned users for this shift
            │       (latest UserShift per user where effective_from ≤ today)
            │
            ├── Fetch WorkSessions: user in assigned_users, date=session_date, is_sent=False
            │
            └── For each session:
                    │
                    ├── Build payload: {user_id, session_date, came_at, gone_at, work_minutes, status}
                    │
                    ├── POST {EXTERNAL_API_URL}/attendance/record (3 retries, 5s sleep)
                    │
                    ├── On success: session.is_sent=True, session.sent_at=now(), session.api_response=...
                    └── On all retries failed: notify_admins_error.delay(...)
```
