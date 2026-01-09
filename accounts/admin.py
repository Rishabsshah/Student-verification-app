from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Add custom fields to the list display in admin
    list_display = ('username', 'email', 'verification_status', 'enrollment_number', 'is_staff')
    
    # Add custom fields to the detail view nicely
    fieldsets = UserAdmin.fieldsets + (
        ('Verification Info', {'fields': ('verification_status', 'enrollment_number', 'identity_hash')}),
    )

admin.site.register(User, CustomUserAdmin)
