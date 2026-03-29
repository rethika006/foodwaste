from django.contrib import admin
from .models import Food


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'donor', 'quantity', 'preparation_time', 'expiry_time', 'is_available')
    list_filter = ('is_available', 'expiry_time')
    search_fields = ('name', 'description', 'location', 'donor__username')
