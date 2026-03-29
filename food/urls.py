from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('receiver/dashboard/', views.receiver_dashboard, name='receiver_dashboard'),
    path('ngo/dashboard/', views.ngo_dashboard, name='ngo_dashboard'),
    path('food/add/', views.add_food, name='add_food'),
    path('food/list/', views.available_food, name='food_list'),
    path('food/<int:pk>/', views.food_detail, name='food_detail'),
    path('food/request/<int:pk>/<str:action>/', views.manage_request, name='manage_request'),
    path('delivery/update/<int:pk>/<str:status>/', views.update_delivery, name='update_delivery'),
    path('request/ngo/delivery/<int:pk>/', views.request_ngo_delivery, name='request_ngo_delivery'),
    path('pickup/food/<int:pk>/', views.pickup_food, name='pickup_food'),
    path('mark/taken/<int:pk>/', views.mark_taken, name='mark_taken'),
    path('mark/received/<int:pk>/', views.mark_received, name='mark_received'),
    path('cancel/ngo/request/<int:pk>/', views.cancel_ngo_request, name='cancel_ngo_request'),
]