from django.conf import settings
from django.db import models


class Food(models.Model):
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donated_food')
    name = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    preparation_time = models.DateTimeField()
    expiry_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='food_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} by {self.donor.username}"
