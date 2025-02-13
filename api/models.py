# backend/api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):  # Extend Django's built-in User model
    id = models.UUIDField(primary_key=True, editable=False) #keep the supabase id
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

class Track(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tracks')
    title = models.CharField(max_length=200)
    genre = models.CharField(max_length=100, blank=True, null=True)
    bpm = models.IntegerField(blank=True, null=True)
    key = models.CharField(max_length=50, blank=True, null=True)
    file_path = models.CharField(max_length=255)  # Store the B2 URL
    preview_path = models.CharField(max_length=255) # For now, same as file_path

    def __str__(self):
        return self.title

class License(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='licenses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='licenses', blank=True, null=True) # Who bought the liscense
    license_type = models.CharField(max_length=100)
    price = models.FloatField()
    agreement_text = models.TextField()
    file_path = models.CharField(max_length=255, blank=True, null=True) # Optional

    def __str__(self):
        return f"{self.license_type} for {self.track.title}"