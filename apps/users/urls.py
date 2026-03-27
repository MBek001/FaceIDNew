from django.urls import path
from apps.users.views import UserFaceResetView

urlpatterns = [
    path('<str:user_id>/reset-face/', UserFaceResetView.as_view(), name='user-face-reset'),
]
