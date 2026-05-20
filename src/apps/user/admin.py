from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from src.apps.user.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff", "is_customer", "is_validate"]
    list_filter = ["is_active", "is_staff", "is_customer", "is_validate", "receive_news"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]
    readonly_fields = ["last_login"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_customer", "is_validate", "groups", "user_permissions")}),
        ("Preferences", {"fields": ("receive_news",)}),
        ("Dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2", "is_staff", "is_active"),
        }),
    )
