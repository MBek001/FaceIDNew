from datetime import date, timedelta
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.attendance.models import AttendanceEvent
from apps.sessions.models import WorkSession
from apps.sessions.services import compute_session_for_user_date
from apps.shifts.services import get_session_date


class Command(BaseCommand):
    help = (
        'Recompute WorkSessions from raw AttendanceEvents. '
        'Safe to run anytime. Only touches sessions where is_sent=False.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=str, default=None)
        parser.add_argument('--from-date', type=str, required=True)
        parser.add_argument('--to-date', type=str, default=None)
        parser.add_argument('--dry-run', action='store_true', default=False)

    def handle(self, *args, **options):
        from_date = date.fromisoformat(options['from_date'])
        to_date = date.fromisoformat(options['to_date']) if options['to_date'] else date.today()
        dry_run = options['dry_run']
        user_id = options['user_id']

        users = User.objects.filter(is_active=True)
        if user_id:
            users = users.filter(id=user_id)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.'))

        created = 0
        skipped_sent = 0

        for user in users:
            shift = user.get_current_shift()
            if not shift:
                self.stdout.write(f"  Skipping {user.name} — no shift assigned.")
                continue

            events = AttendanceEvent.objects.filter(
                user=user,
                scanned_at__date__range=[from_date, to_date + timedelta(days=1)]
            )

            session_dates = set()
            for event in events:
                sd = get_session_date(shift, event.scanned_at)
                if from_date <= sd <= to_date:
                    session_dates.add(sd)

            for sd in session_dates:
                already_sent = WorkSession.objects.filter(
                    user=user, session_date=sd, is_sent=True
                ).exists()

                if already_sent:
                    skipped_sent += 1
                    self.stdout.write(
                        f"  Skipping {user.name} — {sd} (already sent to API)"
                    )
                    continue

                if not dry_run:
                    WorkSession.objects.filter(
                        user=user, session_date=sd, is_sent=False
                    ).delete()
                    compute_session_for_user_date(user, sd)

                created += 1
                self.stdout.write(f"  {'[DRY] ' if dry_run else ''}Computed {user.name} — {sd}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Computed: {created}. Skipped (sent): {skipped_sent}."
        ))
