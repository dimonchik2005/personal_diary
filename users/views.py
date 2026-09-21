from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth import login

from .forms import UserLoginForm, UserRegisterForm
from .models import User


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:account")

    def form_valid(self, form):
        response = super().form_valid(form)

        login(self.request, self.object)

        return response


class UserLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = "users/login.html"


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"

