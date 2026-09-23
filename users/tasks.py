from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerification

logger = get_task_logger(__name__)


@shared_task
def check_worker():
    logger.info("Проверочная задача успешно выполнена.")


@shared_task
def send_test_email():
    send_mail(
        subject="Проверка почты — Личный дневник",
        message=(
            "Это тестовое письмо из проекта «Личный дневник».\n"
            "Отправка выполнена фоновой задачей Celery."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )


@shared_task
def send_verification_email(verification_id, code):
    verification = (
        EmailVerification.objects.select_related("user")
        .filter(pk=verification_id)
        .first()
    )

    if verification is None:
        return

    if verification.confirmed_at is not None:
        return

    if verification.user.is_active:
        return

    if verification.email != verification.user.email:
        return

    if verification.attempts >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
        return

    if not check_password(code, verification.code_hash):
        return

    if timezone.now() >= verification.expires_at:
        return

    send_mail(
        subject="Код подтверждения — Личный дневник",
        message=(
            f"Ваш код подтверждения: {code}\n\n"
            "Введите его на странице подтверждения регистрации.\n"
            "Код действует ограниченное время. "
            "Если он истёк, запросите новый на сайте.\n\n"
            "Если вы не регистрировались, проигнорируйте это письмо."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[verification.email],
        fail_silently=False,
    )


@shared_task
def send_welcome_email(verification_id):
    verification = (
        EmailVerification.objects.select_related("user")
        .filter(
            pk=verification_id,
            confirmed_at__isnull=False,
            user__is_active=True,
        )
        .first()
    )

    if verification is None:
        return

    user = verification.user

    if user.email != verification.email:
        return

    send_mail(
        subject="Добро пожаловать в Личный дневник!",
        message=(
            f"Здравствуйте, {user.username}!\n\n"
            "Ваш email подтверждён, аккаунт готов к работе.\n"
            "Теперь вы можете создавать записи, "
            "редактировать их и находить нужное через поиск.\n\n"
            "Спасибо за регистрацию!"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[verification.email],
        fail_silently=False,
    )
