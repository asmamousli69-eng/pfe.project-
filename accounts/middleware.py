from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages
from .models import UserProfile


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            try:
                # Check if profile exists and requires password change
                if hasattr(request.user, 'profile') and request.user.profile.force_password_change:
                    
                    # Allowed URLs (don't redirect these)
                    allowed_urls = [
                        reverse('accounts:password_change'),
                        reverse('accounts:password_change_done'),
                        reverse('accounts:logout'),
                        '/admin/password_change/',
                        '/accounts/logout/',
                    ]
                    
                    # Check current URL
                    current_path = request.path_info
                    
                    # If not on an allowed page, redirect to password change
                    if current_path not in allowed_urls and not current_path.startswith('/accounts/logout'):
                        messages.warning(request, 'You must change your temporary password before continuing.')
                        return redirect('accounts:password_change')
                        
            except UserProfile.DoesNotExist:
                pass
        
        response = self.get_response(request)
        return response
