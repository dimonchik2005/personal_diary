from django import forms

from .models import Entry


class EntryForm(forms.ModelForm):
    """Форма создания и редактирования записи."""

    class Meta:
        model = Entry
        fields = ("title", "content")
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Название записи",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "О чём хотите написать?",
                    "rows": 10,
                }
            ),
        }
