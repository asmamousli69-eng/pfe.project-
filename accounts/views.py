from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Redirect to dashboard instead of conference list
            return redirect("dashboard")  # Change this to your dashboard URL name
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
    return redirect("login")