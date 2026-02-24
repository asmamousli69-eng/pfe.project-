from django.contrib import admin
from .models import Conference

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "date", "location", "audience", "acts")
    search_fields = ("name", "key")
    list_filter = ("audience", "acts")
