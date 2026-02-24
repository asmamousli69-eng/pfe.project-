
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
path('forgot-password/', 
     auth_views.PasswordResetView.as_view(
         template_name='accounts/forgot_password.html'
     ), 
     name='password_reset'),

path('forgot-password/done/', 
     auth_views.PasswordResetDoneView.as_view(
         template_name='accounts/forgot_password_done.html'
     ), 
     name='password_reset_done'),

path('reset/<uidb64>/<token>/', 
     auth_views.PasswordResetConfirmView.as_view(
         template_name='accounts/forgot_password_confirm.html'
     ), 
     name='password_reset_confirm'),

path('reset/done/', 
     auth_views.PasswordResetCompleteView.as_view(
         template_name='accounts/forgot_password_complete.html'
     ), 
     name='password_reset_complete'),

]
