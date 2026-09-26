from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


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
            "Введите номер телефона в указанном формате" "+79991234567"
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


class UserProfileForm(forms.ModelForm):
    """Редактирование основных данных аккаунта."""

    class Meta:
        model = User
        fields = ("username", "phone")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+79991234567",
                    "autocomplete": "tel",
                    "inputmode": "tel",
                }
            ),
        }
        help_texts = {
            "username": "Минимум 3 символа. Никнейм должен быть уникальным.",
            "phone": (
                "Необязательно. Введите + и от 8 до 15 цифр "
                "без пробелов, скобок и дефисов."
            ),
        }

    def clean_username(self):
        username = self.cleaned_data["username"]

        if len(username) < 3:
            raise ValidationError(
                "Никнейм должен содержать минимум 3 символа.",
                code="username_too_short",
            )

        existing_users = User.objects.filter(username__iexact=username).exclude(
            pk=self.instance.pk
        )

        if existing_users.exists():
            raise ValidationError(
                "Этот никнейм уже занят.",
                code="username_exists",
            )

        return username


class EmailVerificationForm(forms.Form):
    code = forms.RegexField(
        regex=r"\A[0-9]{6}\Z",
        label="Код из письма",
        max_length=6,
        error_messages={
            "required": "Введите код из письма.",
            "invalid": "Код должен состоять из 6 цифр.",
            "max_length": "Код должен состоять из 6 цифр.",
        },
        widget=forms.TextInput(
            attrs={
                "class": "form-control text-center",
                "placeholder": "000000",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
            }
        ),
    )


class ResumeVerificationForm(forms.Form):
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
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

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email or not password:
            return cleaned_data

        user = User.objects.filter(email=email).first()

        if user is None:
            # Выполняем хеширование и для неизвестного аккаунта.
            User().set_password(password)
            password_valid = False
        else:
            password_valid = user.check_password(password)

        if not password_valid:
            raise ValidationError(
                "Неверные данные или подтверждение недоступно.",
                code="verification_unavailable",
            )

        pending_verification_exists = (
            user.email_verification if hasattr(user, "email_verification") else None
        )

        if (
            user.is_active
            or pending_verification_exists is None
            or pending_verification_exists.confirmed_at is not None
            or pending_verification_exists.email != user.email
        ):
            raise ValidationError(
                "Неверные данные или подтверждение недоступно.",
                code="verification_unavailable",
            )

        self.pending_user = user
        return cleaned_data
