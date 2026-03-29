from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.password_reset_request, name='password_reset_request'),
    path('forgot-password/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('forgot-password/reset/', views.password_reset_confirm, name='password_reset_confirm'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('profile/delete/', views.ProfileDeleteView.as_view(), name='profile_delete'),
]