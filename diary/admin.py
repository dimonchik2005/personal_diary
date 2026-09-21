from django.contrib import admin
from django.utils import timezone

from .models import Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "created_at", "updated_at")
    list_display_links = ("id", "title")
    search_fields = ("title", "content", "owner__email")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("owner",)

    @admin.display(description="Создано", ordering="created_at")
    def created_at_display(self, obj):
        return timezone.localtime(obj.created_at).strftime("%d.%m.%Y %H:%M")

    @admin.display(description="Изменено", ordering="updated_at")
    def updated_at_display(self, obj):
        return timezone.localtime(obj.updated_at).strftime("%d.%m.%Y %H:%M")