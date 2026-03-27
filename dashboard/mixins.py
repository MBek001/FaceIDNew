from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class DashboardAccessMixin(LoginRequiredMixin):
    login_url = '/dashboard/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        if not request.user.is_staff:
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)
