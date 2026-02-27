from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),     
    path('conferences/', include('conferences.urls')),
    path('', lambda request: redirect('conference_list')),  # Homepage redirect
]