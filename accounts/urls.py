from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth URLs
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    
    # Password reset - CUSTOM (notifies admin, no self-reset link)
    path('forgot-password/',
         views.AdminNotifiedPasswordResetView.as_view(
             template_name='accounts/forgot_password.html'
         ),
         name='password_reset'),

    path('forgot-password/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/forgot_password_done.html'
         ),
         name='password_reset_done'),
    
     path('password-change/', 
         views.CustomPasswordChangeView.as_view(), 
         name='password_change'),
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'  
         ), 
         name='password_change_done'),
  

    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/<int:user_id>/approve/', views.approve_user, name='approve_user'),
    path('admin/users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('admin/reset-requests/', views.password_reset_requests, name='password_reset_requests'),
    path('admin/reset-password/<int:user_id>/', views.generate_temp_password_view, name='generate_temp_password'),

  


]
