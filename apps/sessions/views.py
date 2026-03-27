from django.views.generic import DetailView
from dashboard.mixins import DashboardAccessMixin
from apps.sessions.models import WorkSession


class SessionDetailView(DashboardAccessMixin, DetailView):
    model = WorkSession
    template_name = 'dashboard/session_detail.html'
    context_object_name = 'session'
