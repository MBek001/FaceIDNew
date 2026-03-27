from datetime import date
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.db.models import Count, Q
from django.shortcuts import redirect
import csv
import pytz

from dashboard.mixins import DashboardAccessMixin
from apps.users.models import User
from apps.attendance.models import AttendanceEvent
from apps.sessions.models import WorkSession, STATUS_PRESENT, STATUS_LATE, STATUS_ABSENT, STATUS_INCOMPLETE
from apps.shifts.models import Shift, UserShift

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')


class DashboardLoginView(LoginView):
    template_name = 'dashboard/login.html'
    redirect_authenticated_user = True


class DashboardLogoutView(LogoutView):
    next_page = '/dashboard/login/'


class DashboardIndexView(DashboardAccessMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()

        today_sessions = WorkSession.objects.filter(session_date=today)
        total_employees = User.objects.filter(is_active=True).count()
        present_count = today_sessions.filter(status=STATUS_PRESENT).count()
        late_count = today_sessions.filter(status=STATUS_LATE).count()
        incomplete_count = today_sessions.filter(status=STATUS_INCOMPLETE).count()
        absent_count = total_employees - present_count - late_count - incomplete_count
        unsent_count = WorkSession.objects.filter(is_sent=False).count()

        recent_events = (
            AttendanceEvent.objects
            .select_related('user')
            .order_by('-scanned_at')[:20]
        )

        ctx.update({
            'total_employees': total_employees,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': max(0, absent_count),
            'incomplete_count': incomplete_count,
            'unsent_count': unsent_count,
            'recent_events': recent_events,
            'today': today,
        })
        return ctx


class EmployeeListView(DashboardAccessMixin, ListView):
    template_name = 'dashboard/employees.html'
    context_object_name = 'employees'
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.all()
        search = self.request.GET.get('search', '').strip()
        department = self.request.GET.get('department', '')
        face_registered = self.request.GET.get('face_registered', '')
        is_active = self.request.GET.get('is_active', '')

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        if department:
            qs = qs.filter(department=department)
        if face_registered in ('true', 'false'):
            qs = qs.filter(is_face_registered=(face_registered == 'true'))
        if is_active in ('true', 'false'):
            qs = qs.filter(is_active=(is_active == 'true'))

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['departments'] = (
            User.objects.values_list('department', flat=True)
            .distinct().order_by('department')
        )
        ctx['filters'] = self.request.GET
        return ctx


class EmployeeDetailView(DashboardAccessMixin, DetailView):
    template_name = 'dashboard/employee_detail.html'
    model = User
    context_object_name = 'employee'
    pk_url_kwarg = 'user_id'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.object
        today = date.today()
        month_start = today.replace(day=1)

        sessions = WorkSession.objects.filter(
            user=user,
            session_date__gte=month_start
        ).order_by('-session_date')

        total_minutes = sum(s.work_minutes or 0 for s in sessions)
        total_hours = round(total_minutes / 60, 1)

        recent_events = (
            AttendanceEvent.objects
            .filter(user=user)
            .order_by('-scanned_at')[:50]
        )

        ctx.update({
            'sessions': sessions,
            'present_days': sessions.filter(status=STATUS_PRESENT).count(),
            'late_days': sessions.filter(status=STATUS_LATE).count(),
            'incomplete_days': sessions.filter(status=STATUS_INCOMPLETE).count(),
            'total_hours': total_hours,
            'recent_events': recent_events,
            'current_shift': user.get_current_shift(),
        })
        return ctx


class AttendanceLogView(DashboardAccessMixin, ListView):
    template_name = 'dashboard/attendance.html'
    context_object_name = 'events'
    paginate_by = 25

    def get_queryset(self):
        qs = AttendanceEvent.objects.select_related('user').order_by('-scanned_at')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        action = self.request.GET.get('action', '')
        user_id = self.request.GET.get('user_id', '')

        if date_from:
            qs = qs.filter(scanned_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(scanned_at__date__lte=date_to)
        if action:
            qs = qs.filter(action=action)
        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['users'] = User.objects.filter(is_active=True).order_by('name')
        ctx['filters'] = self.request.GET
        return ctx


class ShiftsView(DashboardAccessMixin, TemplateView):
    template_name = 'dashboard/shifts.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['shifts'] = Shift.objects.annotate(
            employee_count=Count('user_assignments__user', distinct=True)
        )
        ctx['users'] = User.objects.filter(is_active=True).order_by('name')
        ctx['assignments'] = UserShift.objects.select_related('user', 'shift').order_by('-effective_from')
        return ctx

    def post(self, request):
        action = request.POST.get('form_action')

        if action == 'create_shift':
            Shift.objects.create(
                name=request.POST['name'],
                shift_start=request.POST['shift_start'],
                shift_end=request.POST['shift_end'],
                late_threshold_minutes=int(request.POST.get('late_threshold_minutes', 15)),
                report_delay_hours=int(request.POST.get('report_delay_hours', 2)),
            )

        elif action == 'assign_shift':
            UserShift.objects.update_or_create(
                user_id=request.POST['user_id'],
                effective_from=request.POST['effective_from'],
                defaults={'shift_id': request.POST['shift_id']}
            )

        return redirect('dashboard-shifts')


class ReportsView(DashboardAccessMixin, ListView):
    template_name = 'dashboard/reports.html'
    context_object_name = 'sessions'
    paginate_by = 25

    def get_queryset(self):
        qs = WorkSession.objects.select_related('user', 'shift').order_by('-session_date')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        status = self.request.GET.get('status', '')
        is_sent = self.request.GET.get('is_sent', '')
        shift_id = self.request.GET.get('shift_id', '')

        if date_from:
            qs = qs.filter(session_date__gte=date_from)
        if date_to:
            qs = qs.filter(session_date__lte=date_to)
        if status:
            qs = qs.filter(status=status)
        if is_sent in ('true', 'false'):
            qs = qs.filter(is_sent=(is_sent == 'true'))
        if shift_id:
            qs = qs.filter(shift_id=shift_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['shifts'] = Shift.objects.all()
        ctx['status_choices'] = WorkSession._meta.get_field('status').choices
        ctx['filters'] = self.request.GET
        return ctx

    def post(self, request):
        from apps.sessions.tasks import send_shift_reports
        send_shift_reports.delay()
        return redirect('dashboard-reports')
