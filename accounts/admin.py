from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib import messages
import string
import logging

from .models import UserProfile, PasswordResetRequest

logger = logging.getLogger('cerist_security')


class CustomUserAdmin(UserAdmin):
    actions = ['generate_temp_password', 'approve_user', 'deactivate_user']
    list_display = ['username', 'email', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']

    def generate_temp_password(self, request, queryset):
        """Generate temporary password and notify user"""
        for user in queryset:
            # Generate secure 12-char password
            temp_password = get_random_string(
                12,
                string.ascii_letters + string.digits + "!@#$%^&*"
            )

            # Set password
            user.set_password(temp_password)
            user.save()

            # Update or create profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.force_password_change = True
            profile.save()

            # Mark any pending reset requests as processed
            PasswordResetRequest.objects.filter(
                user=user,
                is_processed=False
            ).update(
                is_processed=True,
                processed_by=request.user,
                processed_at=timezone.now()
            )

            # Send email to user
            try:
                send_mail(
                    subject='[CERIST Portal] Your Temporary Password',
                    message=f'''Dear {user.first_name or user.username},

Your password has been reset by the administrator.

Your temporary password is: {temp_password}

Please login at: http://127.0.0.1:8000/accounts/login/
You will be required to change this password immediately.

Best regards,
CERIST Conference Management System''',
                    from_email='admin@cerist.dz',
                    recipient_list=[user.email],
                    fail_silently=False,
                )

                # Log security event
                logger.info(f"Admin {request.user} reset password for {user.username}")
                messages.success(request, f"Temporary password sent to {user.username}")

            except Exception as e:
                logger.error(f"Failed to send email to {user.email}: {str(e)}")
                messages.error(request, f"Failed to email {user.username}, but password was reset.")
    
    generate_temp_password.short_description = "Generate temporary password & notify user"

    def approve_user(self, request, queryset):
        queryset.update(is_active=True)
        messages.success(request, f"Approved {queryset.count()} users")
    approve_user.short_description = "Approve selected users"

    def deactivate_user(self, request, queryset):
        queryset.update(is_active=False)
        messages.success(request, f"Deactivated {queryset.count()} users")
    deactivate_user.short_description = "Deactivate selected users"

    # ADD THIS METHOD HERE - at the end of the class, before it closes
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Hide password field help text with reset link
        if 'password' in form.base_fields:
            form.base_fields['password'].help_text = (
                "Raw passwords are not stored. Use 'Generate temporary password' action from the user list view to reset passwords."
            )
        return form


# Register PasswordResetRequest
@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'requested_at', 'is_processed', 'processed_by']
    list_filter = ['is_processed', 'requested_at']
    readonly_fields = ['requested_at', 'user']
    search_fields = ['user__username', 'user__email']

    def has_add_permission(self, request):
        return False  # Only created via forgot-password form


# Unregister default User and register custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register UserProfile
admin.site.register(UserProfile)
