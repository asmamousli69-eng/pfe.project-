from django.urls import path
from . import views

urlpatterns = [
    path("", views.conference_list, name="conference_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create/", views.conference_create, name="conference_create"),
    path("edit/<int:id>/", views.conference_edit, name="conference_edit"),
     path('delete/<int:id>/', views.delete_conference, name='delete_conference'),
    path('scraping/', views.scraping_page, name='scraping_page'),
    path('scraping/start/', views.start_scraping, name='start_scraping'),
]