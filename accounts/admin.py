from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Add custom fields to the list display in admin
    list_display = ('full_name', 'email', 'phone_number', 'verification_status', 'enrollment_number', 'is_staff')

    @admin.display(description='Full Name', ordering='first_name')
    def full_name(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else '—'

    # Add custom fields to the detail view nicely
    fieldsets = UserAdmin.fieldsets + (
        ('Verification Info', {'fields': ('verification_status', 'enrollment_number', 'identity_hash', 'phone_number', 'selfie_image')}),
    )

admin.site.register(User, CustomUserAdmin)
