from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from .forms import FoodForm, ContactForm, FoodSearchForm
from .models import Food
from requests_app.forms import FoodRequestForm
from requests_app.models import FoodRequest, Delivery


def home(request):
    return render(request, 'food/home.html')


def about(request):
    return render(request, 'food/about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Here you could send an email or save to database
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'food/contact.html', {'form': form})


@login_required
def donor_dashboard(request):
    food_items = Food.objects.filter(donor=request.user)
    requests = FoodRequest.objects.filter(food__donor=request.user).select_related('receiver', 'delivery__ngo').order_by('-requested_at')
    total_donations = food_items.count()
    available_items = food_items.filter(is_available=True).count()
    pending_requests = requests.filter(status='pending').count()
    return render(request, 'dashboard/donor_dashboard.html', {
        'food_items': food_items,
        'requests': requests,
        'total_donations': total_donations,
        'available_items': available_items,
        'pending_requests': pending_requests,
    })


@login_required
def receiver_dashboard(request):
    requests = FoodRequest.objects.filter(receiver=request.user).select_related('food__donor', 'delivery').order_by('-requested_at')
    total_requests = requests.count()
    accepted_requests = requests.filter(status='accepted').count()
    pending_requests = requests.filter(status='pending').count()
    delivered_requests = requests.filter(status='delivered').count()
    return render(request, 'dashboard/receiver_dashboard.html', {
        'requests': requests,
        'total_requests': total_requests,
        'accepted_requests': accepted_requests,
        'pending_requests': pending_requests,
        'delivered_requests': delivered_requests,
    })


@login_required
def ngo_dashboard(request):
    # Show pending deliveries (unassigned) and assigned to this NGO
    deliveries = Delivery.objects.filter(
        models.Q(ngo__isnull=True, status='pending') | models.Q(ngo=request.user)
    ).select_related('food_request__food__donor', 'food_request__receiver').order_by('-updated_at')
    return render(request, 'dashboard/ngo_dashboard.html', {'deliveries': deliveries})


@login_required
def add_food(request):
    if request.user.role != 'donor':
        messages.error(request, 'Only donors can add food items.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = FoodForm(request.POST, request.FILES)
        if form.is_valid():
            food = form.save(commit=False)
            food.donor = request.user
            food.save()
            messages.success(request, 'Food added successfully.')
            return redirect('donor_dashboard')
    else:
        form = FoodForm()

    return render(request, 'food/add_food.html', {'form': form})


@login_required
def available_food(request):
    # Only receivers can view food listings
    if request.user.role != 'receiver':
        messages.error(request, 'Only receivers can view available food listings.')
        return redirect('dashboard')
    
    items = Food.objects.filter(is_available=True).order_by('-created_at')
    search_form = FoodSearchForm(request.GET or None)
    search_results_count = None
    
    # Handle search and filtering
    if search_form.is_valid():
        location = search_form.cleaned_data.get('location', '').strip()
        food_name = search_form.cleaned_data.get('food_name', '').strip()
        sort_by = search_form.cleaned_data.get('sort_by', 'recent')
        
        # Filter by location
        if location:
            items = items.filter(
                Q(location__icontains=location) |
                Q(donor__address__icontains=location)
            )
        
        # Filter by food name
        if food_name:
            items = items.filter(
                Q(name__icontains=food_name) |
                Q(description__icontains=food_name)
            )
        
        # Apply sorting
        if sort_by == 'expiry_soon':
            items = items.order_by('expiry_time')
        elif sort_by == 'expiry_later':
            items = items.order_by('-expiry_time')
        elif sort_by == 'name':
            items = items.order_by('name')
        else:  # recent
            items = items.order_by('-created_at')
        
        search_results_count = items.count()
    else:
        search_form = FoodSearchForm()
    
    context = {
        'items': items,
        'search_form': search_form,
        'search_results_count': search_results_count,
    }
    return render(request, 'food/food_list.html', context)


@login_required
def food_detail(request, pk):
    item = get_object_or_404(Food, pk=pk)
    can_request = request.user.role == 'receiver'
    already_requested = FoodRequest.objects.filter(food=item, receiver=request.user).exists()
    if request.method == 'POST' and can_request:
        form = FoodRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.food = item
            req.receiver = request.user
            req.save()
            messages.success(request, 'Food request sent.')
            return redirect('receiver_dashboard')
    else:
        form = FoodRequestForm()

    return render(request, 'food/food_detail.html', {'item': item, 'form': form, 'already_requested': already_requested})


@login_required
def manage_request(request, pk, action):
    req = get_object_or_404(FoodRequest, pk=pk, food__donor=request.user)
    if action == 'accept':
        req.status = 'accepted'
        req.save()
        # Delivery.objects.get_or_create(food_request=req, defaults={'ngo': None, 'status': 'pending'})
        messages.success(request, 'Request accepted.')
    elif action == 'reject':
        req.status = 'rejected'
        req.save()
        messages.success(request, 'Request rejected.')
    elif action == 'received':
        if req.status == 'accepted':
            req.food.is_available = False
            req.food.save()
            req.status = 'delivered'
            req.save()
            delivery, created = Delivery.objects.get_or_create(food_request=req, defaults={'ngo': None, 'status': 'delivered'})
            if not created:
                delivery.status = 'delivered'
                delivery.save()
            messages.success(request, 'Food marked as received and removed from available list.')
    return redirect('donor_dashboard')


@login_required
def update_delivery(request, pk, status):
    delivery = get_object_or_404(Delivery, pk=pk)
    # Allow NGO to accept pending deliveries or update their own
    if delivery.ngo is None and status == 'accepted':
        delivery.ngo = request.user
        delivery.status = 'accepted'
        delivery.save()
        messages.success(request, 'Delivery accepted.')
    elif delivery.ngo == request.user:
        if status == 'taken' and delivery.status == 'accepted':
            delivery.status = 'taken'
            delivery.save()
            messages.success(request, 'Food marked as taken.')
        elif status == 'delivered' and delivery.status == 'received':
            delivery.status = 'delivered'
            delivery.save()
            delivery.food_request.status = 'delivered'
            delivery.food_request.save()
            delivery.food_request.food.is_available = False
            delivery.food_request.food.save()
            messages.success(request, 'Food delivered successfully.')
        else:
            messages.error(request, 'Invalid status update.')
    else:
        messages.error(request, 'Unauthorized action.')
    return redirect('ngo_dashboard')


@login_required
def request_ngo_delivery(request, pk):
    req = get_object_or_404(FoodRequest, pk=pk, receiver=request.user, status='accepted')
    if not hasattr(req, 'delivery'):
        Delivery.objects.create(food_request=req, ngo=None, status='pending')
        messages.success(request, 'NGO delivery requested.')
    else:
        messages.info(request, 'Delivery already requested.')
    return redirect('receiver_dashboard')


@login_required
def mark_taken(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk, food_request__food__donor=request.user)
    if delivery.status == 'taken':
        delivery.status = 'received'
        delivery.save()
        messages.success(request, 'Food given.')
    else:
        messages.error(request, 'Cannot give food at this time.')
    return redirect('donor_dashboard')


@login_required
def mark_received(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk, food_request__receiver=request.user)
    if delivery.status == 'received' and delivery.ngo is None:
        delivery.status = 'delivered'
        delivery.save()
        delivery.food_request.status = 'delivered'
        delivery.food_request.save()
        delivery.food_request.food.is_available = False
        delivery.food_request.food.save()
        messages.success(request, 'Food marked as received.')
    else:
        messages.error(request, 'Cannot mark as received at this time.')
    return redirect('receiver_dashboard')


@login_required
def cancel_ngo_request(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk, food_request__receiver=request.user, status='pending', ngo__isnull=True)
    delivery.delete()
    messages.success(request, 'NGO delivery request cancelled.')
    return redirect('receiver_dashboard')


@login_required
def pickup_food(request, pk):
    req = get_object_or_404(FoodRequest, pk=pk, receiver=request.user, status='accepted')
    if not hasattr(req, 'delivery'):
        Delivery.objects.create(food_request=req, ngo=None, status='taken')
        messages.success(request, 'Food marked as taken. Please confirm with donor.')
    else:
        messages.info(request, 'Delivery already initiated.')
    return redirect('receiver_dashboard')

