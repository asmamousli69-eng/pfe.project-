from django.db import models
from django.contrib.auth.models import User

class Conference(models.Model):
    AUDIENCE_CHOICES = [
        ('national', 'National'),
        ('international', 'International'),
    ]

    name = models.CharField(max_length=200)
    key = models.CharField(max_length=20, unique=True)
    domain = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES)
    acts = models.BooleanField(default=False)
    annulee = models.BooleanField(default=False)


    def __str__(self):
        return self.name



class ScrapingJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    conferences_found = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.url} - {self.status}"
    