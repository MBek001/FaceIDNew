# Data Models

## apps/users — User

Primary key is a string ID (from the external HR API, not auto-generated).

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| id | CharField(64) | PK | External HR system ID |
| name | CharField(150) | required | Full name |
| email | EmailField | unique | Work email, used for bot registration |
| phone | CharField(30) | blank | Phone number |
| department | CharField(100) | blank | Department name |
| position | CharField(100) | blank | Job title |
| telegram_id | BigIntegerField | null, unique | Set when user registers via bot |
| face_encoding | TextField | null | JSON-encoded numpy array (128 floats) |
| is_face_registered | BooleanField | default=False | True after successful bot photo upload |
| is_active | BooleanField | default=True | False when not in HR API response |
| synced_at | DateTimeField | null | Last time synced from API |

**Set by:** HR API sync (most fields), Telegram bot registration (telegram_id, face_encoding, is_face_registered).

**Methods:**
- `get_face_encoding_array()` — returns numpy array or None
- `get_current_shift()` — returns latest Shift assigned to this user

---

## apps/shifts — Shift

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| id | BigAutoField | PK | Auto-generated |
| name | CharField(100) | required | Human-readable name |
| shift_start | TimeField | required | Shift begin time (Asia/Tashkent) |
| shift_end | TimeField | required | Shift end time (Asia/Tashkent) |
| late_threshold_minutes | IntegerField | default=15 | Minutes after shift_start before marking late |
| report_delay_hours | IntegerField | default=2 | Hours after shift_end when report fires |

**Properties:**
- `is_night_shift` — True when shift_end < shift_start (crosses midnight)
- `report_fire_time` — Time when Celery should send the shift report

---

## apps/shifts — UserShift

Associates a User to a Shift from a given date. Multiple records per user create a history of shift changes.

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| id | BigAutoField | PK | Auto |
| user | FK(User) | CASCADE | The employee |
| shift | FK(Shift) | PROTECT | The shift |
| effective_from | DateField | unique with user | Date when this assignment starts |

**Set by:** Admin via Django admin or dashboard shifts form.

The active shift for a user is the assignment with the highest `effective_from` that is ≤ today.

---

## apps/attendance — AttendanceEvent

Append-only. Never modified, never deleted.

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| id | BigAutoField | PK | Auto |
| user | FK(User) | PROTECT | Who scanned |
| scanned_at | DateTimeField | required, tz-aware | Exact moment of scan |
| action | CharField(10) | came/gone | Terminal button pressed |
| photo | FileField | required | Saved to media/attendance/YYYY/MM/DD/ |
| face_confidence | FloatField | required | face_recognition distance value (lower = more confident) |
| terminal_ip | GenericIPAddressField | null | IP of the scanning device |
| created_at | DateTimeField | auto_now_add | Record creation time |

**Set by:** Terminal scan endpoint only. No admin write access.

---

## apps/sessions — WorkSession

One record per (user, session_date). Recomputed from Layer 1 events.

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| id | BigAutoField | PK | Auto |
| user | FK(User) | PROTECT | The employee |
| session_date | DateField | unique with user | The work date this session represents |
| shift | FK(Shift) | PROTECT | Shift active at computation time |
| came_event | OneToOneFK(AttendanceEvent) | null | First came event for this date |
| gone_event | OneToOneFK(AttendanceEvent) | null | First gone event for this date |
| computed_came_at | DateTimeField | null | Copy of came_event.scanned_at |
| computed_gone_at | DateTimeField | null | Copy of gone_event.scanned_at |
| work_minutes | IntegerField | null | gone - came in minutes |
| status | CharField(20) | present/late/absent/incomplete | Attendance status |
| is_sent | BooleanField | default=False | Whether sent to external API |
| sent_at | DateTimeField | null | When it was sent |
| api_response | JSONField | null | Raw API response on success |
| computed_at | DateTimeField | auto_now | Last recomputation time |

**Set by:** `compute_session_for_user_date()` in apps/sessions/services.py.

---

## apps/sessions — AdminNotifyConfig

| Field | Type | Constraints | Purpose |
|---|---|---|---|
| id | BigAutoField | PK | Auto |
| telegram_id | BigIntegerField | unique | Admin's Telegram user ID |
| name | CharField(150) | required | Human label |
| notify_on_came | BooleanField | default=True | Receive photo on Keldi event |
| notify_on_gone | BooleanField | default=True | Receive photo on Ketdi event |
| notify_on_report_sent | BooleanField | default=True | Receive summary after shift report |
| notify_on_report_failed | BooleanField | default=True | Receive error on report failure |

**Set by:** Django admin manually.

---

## Model Relationships

```
User ──< UserShift >── Shift
User ──< AttendanceEvent
User ──< WorkSession >── Shift
WorkSession ── came_event ── AttendanceEvent
WorkSession ── gone_event ── AttendanceEvent
```
