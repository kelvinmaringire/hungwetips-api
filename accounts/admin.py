from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Admin configuration for CustomUser model."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'email_verified', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('email_verified', 'is_staff', 'is_active', 'is_superuser', 'date_joined')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('email_verified', 'dob', 'sex', 'physical_address', 'phone_number')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'email_verified')
        }),
    )
