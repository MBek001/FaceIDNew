# Session Recompute Guide

## When to Run Recompute

- A user's shift assignment was changed retroactively.
- A bug was found in the session computation logic and then fixed.
- Sessions were accidentally deleted or corrupted.
- A new shift rule (late threshold, night shift boundary) was adjusted.
- You want to rebuild sessions for a specific date range after correcting data.

## Command Syntax

```bash
python manage.py recompute_sessions \
    --from-date YYYY-MM-DD \
    [--to-date YYYY-MM-DD] \
    [--user-id USER_ID] \
    [--dry-run]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--from-date` | Yes | Start date (inclusive) |
| `--to-date` | No | End date (inclusive). Defaults to today. |
| `--user-id` | No | Limit to one user. Defaults to all active users. |
| `--dry-run` | No | Print what would happen without saving anything. |

## Examples

```bash
# Recompute all users for the current month
python manage.py recompute_sessions --from-date 2025-03-01

# Recompute one user for a date range
python manage.py recompute_sessions \
    --from-date 2025-03-01 \
    --to-date 2025-03-31 \
    --user-id emp-001

# Preview without changes
python manage.py recompute_sessions --from-date 2025-03-01 --dry-run
```

## What Is Safe to Recompute

Sessions where `is_sent=False` are safe to recompute. The command will:
1. Delete the existing unsent `WorkSession` for the date.
2. Call `compute_session_for_user_date()` to rebuild from raw `AttendanceEvent` records.

## What Cannot Be Recomputed

Sessions where `is_sent=True` have been reported to the external API. The command skips them and logs a message. This is intentional: once a session is reported to the external system, recomputing it would create inconsistency between the local database and the external system.

If you need to correct a sent session, you must update it in the external system directly or contact the system owner.

## Step-by-Step: Shift Change → Recompute Procedure

1. Go to Django admin → User → find the employee.
2. In the UserShift inline, add a new assignment with the new shift and the correct `effective_from` date.
3. Save.
4. Run the management command for the affected date range:
   ```bash
   python manage.py recompute_sessions \
       --from-date YYYY-MM-DD \
       --user-id EMPLOYEE_ID
   ```
5. Verify the recomputed sessions in the dashboard under Reports or the employee detail page.
6. If sessions look correct, they will be included in the next scheduled `send_shift_reports` run.

Layer 1 (`AttendanceEvent`) is never touched during this entire process.
