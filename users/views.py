import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, TemplateView, UpdateView
from kombu.exceptions import OperationalError

from .forms import (
    EmailVerificationForm,
    ResumeVerificationForm,
    UserLoginForm,
    UserProfileForm,
    UserRegisterForm,
)
from .models import User
from .services import issue_email_code, verify_email_code
from .tasks import send_verification_email, send_welcome_email

logger = logging.getLogger(__name__)


def enqueue_verification_email(request, verification, code):
    try:
        send_verification_email.apply_async(
            args=[verification.pk, code],
            argsrepr=f"({verification.pk}, '<hidden>')",
            expires=verification.expires_at,
        )
    except OperationalError:
        logger.error(
            "Не удалось поставить письмо подтверждения в очередь: %s",
            verification.pk,
        )
        messages.error(
            request,
            "Не удалось отправить запрос на письмо. "
            "Попробуйте повторную отправку через минуту.",
        )
    else:
        messages.info(
            request,
            "Код запрошен. Проверьте почту и папку «Спам».",
        )


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:verify_email")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("diary:entry_list")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.is_active = False
            self.object.save()

            verification, code = issue_email_code(self.object.pk)

            transaction.on_commit(
                lambda: enqueue_verification_email(
                    self.request,
                    verification,
                    code,
                )
            )

        self.request.session.cycle_key()
        self.request.session["pending_verification_user_id"] = self.object.pk

        return redirect(self.success_url)


class UserLoginView(LoginView):
    authentication_form = UserLoginForm
    template_name = "users/login.html"


class AccountView(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    http_method_names = ["post", "options"]

    def get_object(self, queryset=None):
        return self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = "profile"
        return kwargs

    def form_valid(self, form):
        self.object = form.save()

        return JsonResponse(
            {
                "message": "Настройки аккаунта сохранены.",
                "username": self.object.username,
            }
        )

    def form_invalid(self, form):
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )


class PendingVerificationMixin:
    """Определяет подтверждаемый аккаунт по сессии."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("diary:entry_list")

        user_id = request.session.get("pending_verification_user_id")

        self.pending_user = User.objects.filter(
            pk=user_id,
            is_active=False,
        ).first()

        if self.pending_user is None:
            request.session.pop("pending_verification_user_id", None)
            messages.info(
                request,
                "Нет незавершённого подтверждения в этом браузере.",
            )
            return redirect("users:resume_verification")

        return super().dispatch(request, *args, **kwargs)


class EmailVerificationView(PendingVerificationMixin, FormView):
    form_class = EmailVerificationForm
    template_name = "users/verify_email.html"
    success_url = reverse_lazy("diary:entry_list")

    def form_valid(self, form):
        try:
            user = verify_email_code(
                self.pending_user.pk,
                form.cleaned_data["code"],
            )
        except ValidationError as error:
            form.add_error("code", error)
            return self.form_invalid(form)

        self.request.session.pop("pending_verification_user_id", None)
        login(self.request, user)

        try:
            send_welcome_email.delay(user.email_verification.pk)
        except OperationalError:
            logger.error(
                "Не удалось поставить приветственное письмо "
                "в очередь для пользователя %s",
                user.pk,
            )

        messages.success(self.request, "Email подтверждён. Добро пожаловать!")
        return super().form_valid(form)


class ResendVerificationView(PendingVerificationMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            verification, code = issue_email_code(self.pending_user.pk)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            enqueue_verification_email(request, verification, code)

        return redirect("users:verify_email")


class ResumeVerificationView(FormView):
    form_class = ResumeVerificationForm
    template_name = "users/resume_verification.html"
    success_url = reverse_lazy("users:verify_email")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("diary:entry_list")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session.cycle_key()
        self.request.session["pending_verification_user_id"] = form.pending_user.pk

        return super().form_valid(form)
