from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Пользователь личного дневника."""

    email = models.EmailField(
        verbose_name="Электронная почта",
        unique=True,
    )
    phone = models.CharField(
        verbose_name="Номер телефона",
        max_length=16,
        blank=True,
        default="",
        validators=[
            RegexValidator(
                regex=r"\A\+[1-9][0-9]{7,14}\Z",
                message=(
                    "Введите номер в международном формате: "
                    "+79991234567, без пробелов и скобок."
                ),
            ),
        ],
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class EmailVerification(models.Model):
    """Текущее подтверждение email при регистрации."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
        verbose_name="Пользователь",
    )
    email = models.EmailField(
        verbose_name="Подтверждаемый email",
    )
    code_hash = models.CharField(
        max_length=128,
        verbose_name="Хеш кода",
    )
    expires_at = models.DateTimeField(
        verbose_name="Действителен до",
    )
    attempts = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Количество неверных попыток",
    )
    last_requested_at = models.DateTimeField(
        verbose_name="Последний запрос кода",
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата подтверждения",
    )

    class Meta:
        verbose_name = "Подтверждение email"
        verbose_name_plural = "Подтверждения email"

    def __str__(self):
        return f"Подтверждение email пользователя {self.user_id}"
