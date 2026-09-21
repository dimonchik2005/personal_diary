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
