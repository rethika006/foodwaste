from django.contrib import admin
from .models import FoodRequest, Delivery


@admin.register(FoodRequest)
class FoodRequestAdmin(admin.ModelAdmin):
    list_display = ('food', 'receiver', 'status', 'requested_at')
    list_filter = ('status',)
    search_fields = ('food__name', 'receiver__username')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('food_request', 'ngo', 'status', 'updated_at')
    list_filter = ('status',)
    search_fields = ('ngo__username', 'food_request__food__name')
