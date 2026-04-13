from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth URLs
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    
    # Password reset URLs (with success_url fixed)
    path('forgot-password/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/forgot_password.html',
             success_url='/accounts/forgot-password/done/'  # ADD THIS
         ),
         name='password_reset'),

    path('forgot-password/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/forgot_password_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/forgot_password_confirm.html',
             success_url='/accounts/reset/done/'  # ADD THIS
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/forgot_password_complete.html'
         ),
         name='password_reset_complete'),

    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/<int:user_id>/approve/', views.approve_user, name='approve_user'),
    path('admin/users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
    path('admin/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
