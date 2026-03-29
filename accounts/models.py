from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('receiver', 'Receiver'),
        ('ngo', 'NGO'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='receiver')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
