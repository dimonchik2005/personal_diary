from django.conf import settings
from django.db import models


class Entry(models.Model):
    """Вход в запись личного дневника."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name="Владелец",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок",
    )
    content = models.TextField(
        verbose_name="Содержание",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения",
    )

    class Meta:
        verbose_name = "Запись дневника"
        verbose_name_plural = "Записи дневника"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title
