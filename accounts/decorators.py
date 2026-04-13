from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    """
    Decorator to check if user is staff/admin.
    Redirects to login if not authenticated, or home if not staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            return redirect('dashboard') # Changed from 'home' to 'dashboard' to match your project
        return view_func(request, *args, **kwargs)
    return _wrapped_view
