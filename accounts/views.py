from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from conferences.models import Conference
from .decorators import admin_required
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetRequest, UserProfile
from django.utils import timezone
import logging
import string
from django.contrib.auth.views import PasswordChangeView as AuthPasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm

class CustomPasswordChangeView(AuthPasswordChangeView):
    template_name = 'accounts/password_change.html'  # ADD 'accounts/' prefix
    success_url = '/accounts/password-change/done/'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Set force_password_change to False after successful change
        if hasattr(self.request.user, 'profile'):
            self.request.user.profile.force_password_change = False
            self.request.user.profile.save()
        
        return response


logger = logging.getLogger('cerist_security')

User = get_user_model()


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")  
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, "accounts/login.html")

def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm = request.POST["confirm"]
        
        if password != confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/signup.html")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, "accounts/signup.html")
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, "accounts/signup.html")
        
        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Compte créé avec succès! Vous pouvez maintenant vous connecter.")
        return redirect("accounts:login")
    
    return render(request, "accounts/signup.html")

def logout_view(request):
    logout(request)
    return redirect("accounts:login")

@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    pending_approval = User.objects.filter(is_active=False).count()
    total_conferences = Conference.objects.count()
    pending_resets = PasswordResetRequest.objects.filter(is_processed=False)
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'pending_approval': pending_approval,
            'total_conferences': total_conferences,
            'pending_resets': pending_resets.count(),
        },
        'recent_users': recent_users,
        'pending_reset_requests': pending_resets,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@admin_required
def user_list(request):
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    context = {
        'users': users,
        'current_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'accounts/user_list.html', context)

@admin_required
def password_reset_requests(request):
    requests = PasswordResetRequest.objects.all().order_by('-requested_at')
    pending_count = requests.filter(is_processed=False).count()
    
    context = {
        'requests': requests,
        'pending_count': pending_count,
    }
    return render(request, 'accounts/reset_requests.html', context)

@admin_required
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f'User {user.username} has been approved.')
    return redirect('accounts:user_list')

@admin_required
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot deactivate yourself!")
        return redirect('accounts:user_list')
    
    if user.is_active:
        user.is_active = False
        user.save()
        messages.success(request, f'User {user.username} has been deactivated.')
    return redirect('accounts:user_list')

@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete yourself!")
        return redirect('accounts:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/delete_confirm.html', {'user_obj': user})

# ADD THIS NEW FUNCTION HERE
@admin_required
def generate_temp_password_view(request, user_id):
    """
    Generate temporary password for a specific user (from reset requests page)
    """
    from django.utils.crypto import get_random_string
    
    user = get_object_or_404(User, id=user_id)
    
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
    
    print(f"DEBUG: Attempting to send email to: {user.email}")  # ADD THIS LINE
    
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
        
        print(f"DEBUG: SUCCESS! Email sent to {user.email}")  # ADD THIS LINE
        messages.success(request, f"Temporary password sent to {user.username} at {user.email}")
        
    except Exception as e:
        print(f"DEBUG: FAILED! Error: {str(e)}")  # ADD THIS LINE
        messages.error(request, f"Email failed: {str(e)}. Temp password was: {temp_password}")
    
    return redirect('accounts:password_reset_requests')


class AdminNotifiedPasswordResetView(PasswordResetView):
    template_name = 'accounts/forgot_password.html'
    email_template_name = None
    subject_template_name = None
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        
        try:
            user = User.objects.get(email=email)
            reset_request = PasswordResetRequest.objects.create(user=user)
            
            admin_emails = User.objects.filter(
                is_superuser=True, 
                email__isnull=False
            ).exclude(email='').values_list('email', flat=True)
            
            if admin_emails:
                send_mail(
                    subject=f'[CERIST] Password Reset Request: {user.username}',
                    message=f'''Administrator,

A password reset was requested:

User: {user.username}
Email: {user.email}
Time: {reset_request.requested_at}

Action: Login to admin panel and reset password for this user.

CERIST Portal''',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@cerist.dz'),
                    recipient_list=list(admin_emails),
                    fail_silently=False,
                )
            
            logger.info(f"Reset requested by {user.username}")
            
        except User.DoesNotExist:
            logger.warning(f"Reset attempted for non-existent email: {email}")
            pass
        
        return redirect('accounts:password_reset_done') 