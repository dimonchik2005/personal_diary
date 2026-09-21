from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User
from django import forms

class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "username", "phone")

    def clean_username(self):
        username = super().clean_username()

        if len(username) < 3:
            raise ValidationError(
                "Никнейм должен содержать минимум 3 символа.",
                code="username_too_short",
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Пользователь с таким email уже зарегистрирован.",
                code="email_exists",
            )

        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["phone"].widget.attrs.update(
            {
                "placeholder": "+79991234567",
                "autocomplete": "tel",
                "inputmode": "tel",
            }
        )
        self.fields["phone"].help_text = (
            "Введите номер телефона в указанном формате"
            "+79991234567"
        )

class UserLoginForm(AuthenticationForm):
    """Форма входа по email и паролю."""

    username = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "name@example.com",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "current-password",
            }
        ),
    )

    error_messages = {
        "invalid_login": "Неверный email или пароль.",
        "inactive": "Этот аккаунт отключён.",
    }