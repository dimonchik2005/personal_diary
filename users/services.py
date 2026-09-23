import secrets
from datetime import timedelta
from math import ceil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import EmailVerification

User = get_user_model()


def issue_email_code(user_id):
    """Создаёт новый код и возвращает подтверждение вместе с кодом."""

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)

        verification = (
            EmailVerification.objects.select_for_update().filter(user=user).first()
        )

        if user.is_active or (
            verification is not None and verification.confirmed_at is not None
        ):
            raise ValidationError(
                "Для этого аккаунта подтверждение регистрации недоступно."
            )

        now = timezone.now()

        if verification is not None:
            available_at = verification.last_requested_at + timedelta(
                seconds=settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS
            )

            if now < available_at:
                seconds_left = ceil((available_at - now).total_seconds())

                raise ValidationError(
                    "Повторно запросить код можно через " f"{seconds_left} сек."
                )

        code = f"{secrets.randbelow(1_000_000):06d}"

        verification, _ = EmailVerification.objects.update_or_create(
            user=user,
            defaults={
                "email": user.email,
                "code_hash": make_password(code),
                "expires_at": now
                + timedelta(seconds=settings.EMAIL_VERIFICATION_CODE_TTL_SECONDS),
                "attempts": 0,
                "last_requested_at": now,
                "confirmed_at": None,
            },
        )

    return verification, code


def verify_email_code(user_id, code):
    """Проверяет код и активирует пользователя."""

    error_message = None

    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)

        verification = (
            EmailVerification.objects.select_for_update().filter(user=user).first()
        )

        if verification is None:
            error_message = "Сначала запросите код подтверждения."

        elif verification.confirmed_at is not None:
            error_message = "Этот email уже подтверждён."

        elif user.is_active:
            error_message = "Аккаунт уже активирован."

        elif verification.email != user.email:
            error_message = "Email изменился. Запросите новый код."

        elif timezone.now() >= verification.expires_at:
            error_message = "Срок действия кода истёк. Запросите новый."

        elif verification.attempts >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
            error_message = "Попытки закончились. Запросите новый код."

        elif not check_password(code, verification.code_hash):
            verification.attempts += 1
            verification.save(update_fields=["attempts"])

            attempts_left = (
                settings.EMAIL_VERIFICATION_MAX_ATTEMPTS - verification.attempts
            )

            if attempts_left:
                error_message = f"Неверный код. Осталось попыток: {attempts_left}."
            else:
                error_message = "Попытки закончились. Запросите новый код."

        else:
            verification.confirmed_at = timezone.now()
            verification.save(update_fields=["confirmed_at"])

            user.is_active = True
            user.save(update_fields=["is_active"])

    if error_message is not None:
        raise ValidationError(error_message)

    return user
