from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "phone", "is_staff", "is_active")
    search_fields = ("email", "username", "phone")
    ordering = ("email",)

    fieldsets = UserAdmin.fieldsets + (
        ("Контакты", {"fields": ("phone",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Контакты", {"fields": ("email", "phone")}),
    )