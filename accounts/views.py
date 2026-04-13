from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from conferences.models import Conference
from .decorators import admin_required


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
        
        # Check if passwords match
        if password != confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, "accounts/signup.html")
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, "accounts/signup.html")
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, "accounts/signup.html")
        
        # Create user
        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "Compte créé avec succès! Vous pouvez maintenant vous connecter.")
        return redirect("login")
    
    return render(request, "accounts/signup.html")

def logout_view(request):
    logout(request)
    return redirect("accounts:login")  # <- 4 SPACES (CORRECT!)
@admin_required
def admin_dashboard(request):
    """
    Main admin dashboard with statistics
    """
    # Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    pending_approval = User.objects.filter(is_active=False).count()
    total_conferences = Conference.objects.count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'pending_approval': pending_approval,
            'total_conferences': total_conferences,
        },
        'recent_users': recent_users,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@admin_required
def user_list(request):
    """
    List all users with management options
    """
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
