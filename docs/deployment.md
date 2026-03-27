# Deployment Guide

## First Run Checklist

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and edit environment file
cp .env.example .env
# Edit .env with your real values (see Environment Variables below)

# 3. Apply database migrations
python manage.py migrate

# 4. Create admin superuser
python manage.py createsuperuser

# 5. Collect static files
python manage.py collectstatic
```

## Running All 4 Processes

Open 4 separate terminals:

```bash
# Terminal 1 — Django web server
python manage.py runserver

# Terminal 2 — Celery worker (processes tasks)
celery -A config worker --loglevel=info

# Terminal 3 — Celery Beat (schedules periodic tasks)
celery -A config beat --loglevel=info

# Terminal 4 — Telegram bot
python -m apps.bot.main
```

Redis must be running before starting Celery processes.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django secret key, min 50 random chars |
| `DEBUG` | No | False | Set True only in development |
| `TELEGRAM_BOT_TOKEN` | Yes | — | From @BotFather |
| `EXTERNAL_API_URL` | Yes | — | Base URL of the HR/attendance API (no trailing slash) |
| `EXTERNAL_API_KEY` | No | "" | Bearer token for API authentication |
| `REDIS_URL` | No | redis://localhost:6379/0 | Celery broker and result backend |
| `FACE_TOLERANCE` | No | 0.5 | Face matching threshold. Lower = stricter. Range: 0.3–0.6 |

## Post-Setup Steps

1. Go to `http://localhost:8000/admin/` and log in as superuser.
2. Add at least one **Shift**: Shifts → Add Shift. Set name, start time, end time.
3. Add **AdminNotifyConfig**: Sessions → Add AdminNotifyConfig. Enter your Telegram ID and name.
   - To get your Telegram ID, message @userinfobot on Telegram.
4. Trigger **user sync**: Users → select any user → Actions → "Sync users from external API". Or wait for the 2am cron.
5. **Assign shifts** to users: Users → edit a user → UserShift inline → add shift + effective_from date.
6. Go to `http://localhost:8000/terminal/` — press KELDI or KETDI to test a scan.
7. Go to `http://localhost:8000/dashboard/` — log in and view results.

## Adding a Telegram Admin Notification Recipient

1. Django admin → Sessions → Admin Notification Configs → Add.
2. Enter `telegram_id` (numeric) and `name`.
3. Check which notification types they should receive.
4. They will now receive photos and summaries automatically.

## Common Issues and Fixes

**"No module named 'face_recognition'"**
→ `pip install face_recognition`. On Linux you may need: `sudo apt install cmake libdlib-dev`

**"Redis connection refused"**
→ Start Redis: `redis-server` or `sudo systemctl start redis`

**Celery tasks not running**
→ Ensure both worker and beat are running. Check `CELERY_BROKER_URL` in .env.

**Bot not responding**
→ Check `TELEGRAM_BOT_TOKEN` in .env. Ensure only one bot process is running.

**"FACE_TOLERANCE" causing too many false rejections**
→ Increase `FACE_TOLERANCE` in .env (e.g. 0.6). Restart the server.

**Sessions not being sent to API**
→ Check `EXTERNAL_API_URL` and `EXTERNAL_API_KEY`. Check Celery beat is running. Check `/admin/sessions/worksession/` for `is_sent=False` records.

**Recompute needed after fixing a bug**
→ See `docs/recompute_guide.md`.
