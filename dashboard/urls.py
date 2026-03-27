from django.urls import path
from dashboard.views import (
    DashboardLoginView, DashboardLogoutView,
    DashboardIndexView, EmployeeListView, EmployeeDetailView,
    AttendanceLogView, ShiftsView, ReportsView
)

urlpatterns = [
    path('login/', DashboardLoginView.as_view(), name='dashboard-login'),
    path('logout/', DashboardLogoutView.as_view(), name='dashboard-logout'),
    path('', DashboardIndexView.as_view(), name='dashboard-index'),
    path('employees/', EmployeeListView.as_view(), name='dashboard-employees'),
    path('employees/<str:user_id>/', EmployeeDetailView.as_view(), name='dashboard-employee-detail'),
    path('attendance/', AttendanceLogView.as_view(), name='dashboard-attendance'),
    path('shifts/', ShiftsView.as_view(), name='dashboard-shifts'),
    path('reports/', ReportsView.as_view(), name='dashboard-reports'),
]
