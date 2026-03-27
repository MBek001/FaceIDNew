# System Architecture

## ASCII Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SYSTEMS                          │
│   External HR API (users)        Telegram Bot API               │
└────────────┬─────────────────────────────┬───────────────────────┘
             │ sync_users_task (2am)        │ aiogram polling
             ▼                             ▼
┌────────────────────────────────────────────────────────────────┐
│                        DJANGO APPLICATION                       │
│                                                                 │
│  ┌──────────────┐    ┌───────────────┐   ┌──────────────────┐  │
│  │  apps/users  │    │   apps/bot    │   │ apps/attendance  │  │
│  │              │    │               │   │                  │  │
│  │  User model  │◄───│  FSM handlers │   │  ScanView (POST) │  │
│  │  sync svc    │    │  photo reg    │   │  face matching   │  │
│  └──────┬───────┘    └───────────────┘   └────────┬─────────┘  │
│         │                                          │            │
│         │                           AttendanceEvent created     │
│         │                                          │            │
│  ┌──────▼───────┐                       ┌──────────▼──────────┐ │
│  │ apps/shifts  │                       │    apps/sessions    │ │
│  │              │                       │                     │ │
│  │  Shift model │◄──────────────────────│  WorkSession model  │ │
│  │  UserShift   │   compute_status()    │  compute_session()  │ │
│  │  services    │   get_session_date()  │  send_shift_reports │ │
│  └──────────────┘                       └──────────┬──────────┘ │
│                                                     │           │
│  ┌──────────────────────────────────────────────────▼─────────┐ │
│  │                      CELERY TASKS                          │ │
│  │  compute_and_notify  │  send_shift_reports  │  sync_users  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     dashboard/                           │   │
│  │  LoginView  │  IndexView  │  EmployeeListView  │  etc.   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
             │                             │
             ▼                             ▼
      SQLite db.sqlite3            media/ (photos)
```

## Two-Layer Data Model

The system maintains a strict separation between raw data and computed data.

### Layer 1 — AttendanceEvent (Raw, Immutable)
- Created by the terminal scan endpoint when a face is recognized.
- Fields: user, scanned_at, action (came/gone), photo file, face_confidence, terminal_ip.
- Never modified after creation. Never deleted. Append-only.
- This is the permanent source of truth for all attendance history.

### Layer 2 — WorkSession (Computed, Recomputable)
- Derived by combining Layer 1 events with shift rules.
- Created or updated by `compute_session_for_user_date()` in apps/sessions/services.py.
- Can be wiped and rebuilt at any time from Layer 1 without data loss.
- When a shift changes or a bug is fixed, Layer 2 is recomputed. Layer 1 is never touched.
- Sessions marked `is_sent=True` have been reported to the external API and are skipped during recompute.

## How Celery Connects the Layers

1. Terminal POSTs a scan → `ScanView` creates an `AttendanceEvent`.
2. `compute_and_notify.delay(event.id)` is called immediately.
3. Celery worker picks up the task, calls `compute_session_for_user_date()`.
4. `send_shift_reports` runs every 5 minutes via Celery Beat, sends unsent sessions to the external API.
5. `sync_users_task` runs nightly at 2am to pull updated user data from the HR API.

## Service Boundaries

| Module | Responsibility |
|---|---|
| apps/users/services.py | Sync users from external HR API |
| apps/shifts/services.py | Shift rule logic: session date computation, status (present/late) |
| apps/attendance/services.py | Face detection, face matching, IP extraction |
| apps/sessions/services.py | Session computation from raw events |
| apps/sessions/tasks.py | Async notification and report delivery |
| dashboard/views.py | Read-only dashboard views + shift management forms |
