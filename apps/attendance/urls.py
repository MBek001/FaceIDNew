from django.urls import path
from apps.attendance.views import TerminalView, ScanView

urlpatterns = [
    path('', TerminalView.as_view(), name='terminal'),
    path('scan/', ScanView.as_view(), name='terminal-scan'),
]
