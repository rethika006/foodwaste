from django.conf import settings
from django.db import models
from food.models import Food


class FoodRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='requests')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='food_requests')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.receiver.username} -> {self.food.name} ({self.status})"


class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('taken', 'Taken'),
        ('received', 'Received'),
        ('delivered', 'Delivered'),
    ]
    food_request = models.OneToOneField(FoodRequest, on_delete=models.CASCADE, related_name='delivery')
    ngo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='managed_deliveries', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Delivery {self.food_request.id} {self.status}"
