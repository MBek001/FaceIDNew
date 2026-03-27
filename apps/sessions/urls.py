from django.urls import path
from apps.sessions.views import SessionDetailView

urlpatterns = [
    path('<int:pk>/', SessionDetailView.as_view(), name='session-detail'),
]
