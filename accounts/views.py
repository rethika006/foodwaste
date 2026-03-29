from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView, DeleteView

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    CustomUserChangeForm,
    PasswordResetRequestForm,
    OTPVerificationForm,
    PasswordResetForm,
)
from .models import CustomUser
from food.models import Food
from requests_app.models import FoodRequest, Delivery


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. You can login now.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if not request.POST.get('remember'):
                request.session.set_expiry(0)
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def _mask_email(email):
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def _mask_phone(phone):
    if not phone:
        return phone
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) <= 4:
        return '*' * len(phone)
    prefix = phone[:2]
    suffix = phone[-2:]
    middle = '*' * max(0, len(phone) - len(prefix) - len(suffix))
    return prefix + middle + suffix


def _send_otp(user, otp, method):
    if method == 'email':
        if not user.email:
            return False
        try:
            send_mail(
                'FoodWaste Password Reset OTP',
                f'Your OTP for password reset is {otp}. It expires in 10 minutes.',
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@foodwaste.local'),
                [user.email],
                fail_silently=False,
            )
            return True
        except Exception:
            return False

    if method == 'phone':
        if not user.phone:
            return False
        # Replace this block with real SMS provider integration.
        # Example: send_sms(user.phone, otp)
        return True

    return False


def password_reset_request(request):
    if request.method == 'POST':
        # After account lookup, user chooses contact method if both are available.
        if 'contact_method' in request.POST:
            method = request.POST.get('contact_method')
            user_id = request.session.get('pwd_reset_user_id')
            if not user_id:
                messages.error(request, 'Session expired. Please start password reset again.')
                return redirect('password_reset_request')

            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found. Please start again.')
                return redirect('password_reset_request')

            otp = request.session.get('pwd_reset_otp')
            if not otp:
                otp = '{:06d}'.format(__import__('random').randint(0, 999999))
                request.session['pwd_reset_otp'] = otp
                request.session['pwd_reset_otp_expires'] = (timezone.now() + timezone.timedelta(minutes=10)).isoformat()
                request.session['pwd_reset_verified'] = False
                request.session['pwd_reset_attempts'] = 0

            if _send_otp(user, otp, method):
                request.session['pwd_reset_selected_method'] = method
                messages.success(request, f'OTP sent to your {method}.')
                return redirect('password_reset_verify')

            # If email failed and a phone is available, keep user on choice page
            available_methods = []
            if user.email:
                available_methods.append('email')
            if user.phone:
                available_methods.append('phone')

            if method == 'email' and user.phone:
                messages.warning(request, 'Unable to send OTP via email. Please select phone to receive OTP.')
                return render(request, 'accounts/password_reset_contact_choice.html', {
                    'methods': available_methods,
                    'email': _mask_email(user.email),
                    'phone': _mask_phone(user.phone),
                })

            messages.error(request, f'Unable to send OTP via {method}. Please try another method.')
            return redirect('password_reset_request')

        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['username_or_email'].strip()
            user = None
            try:
                user = CustomUser.objects.get(username__iexact=identifier)
            except CustomUser.DoesNotExist:
                try:
                    user = CustomUser.objects.get(email__iexact=identifier)
                except CustomUser.DoesNotExist:
                    user = None

            if not user:
                messages.error(request, 'No account found with that username/email.')
                return redirect('password_reset_request')

            otp = '{:06d}'.format(__import__('random').randint(0, 999999))
            expiry = timezone.now() + timezone.timedelta(minutes=10)

            request.session['pwd_reset_user_id'] = user.id
            request.session['pwd_reset_otp'] = otp
            request.session['pwd_reset_otp_expires'] = expiry.isoformat()
            request.session['pwd_reset_verified'] = False
            request.session['pwd_reset_attempts'] = 0

            available_methods = []
            if user.email:
                available_methods.append('email')
            if user.phone:
                available_methods.append('phone')

            if not available_methods:
                messages.error(request, 'Your account has no email or phone number set for OTP delivery.')
                return redirect('password_reset_request')

            if len(available_methods) > 1:
                # Ask user to choose preferred contact channel with masked display.
                return render(request, 'accounts/password_reset_contact_choice.html', {
                    'methods': available_methods,
                    'email': _mask_email(user.email),
                    'phone': _mask_phone(user.phone),
                })

            method = available_methods[0]
            if _send_otp(user, otp, method):
                request.session['pwd_reset_selected_method'] = method
                messages.success(request, f'OTP sent to your {method}.')
                return redirect('password_reset_verify')

            messages.error(request, f'Unable to send OTP via {method}. Please check your {method} settings.')
            return redirect('password_reset_request')

    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_verify(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            if not request.session.get('pwd_reset_user_id'):
                messages.error(request, 'Password reset session expired, please start again.')
                return redirect('password_reset_request')

            attempts = request.session.get('pwd_reset_attempts', 0)
            if attempts >= 5:
                messages.error(request, 'Too many invalid OTP attempts. Please request a new OTP.')
                return redirect('password_reset_request')

            saved_otp = request.session.get('pwd_reset_otp')
            expires = request.session.get('pwd_reset_otp_expires')
            if not saved_otp or not expires:
                messages.error(request, 'OTP data missing, please request again.')
                return redirect('password_reset_request')

            if timezone.now() > timezone.datetime.fromisoformat(expires):
                messages.error(request, 'OTP expired. Please request a new one.')
                return redirect('password_reset_request')

            if form.cleaned_data['otp'] != saved_otp:
                request.session['pwd_reset_attempts'] = attempts + 1
                messages.error(request, 'Invalid OTP. Please try again.')
            else:
                request.session['pwd_reset_verified'] = True
                messages.success(request, 'OTP verified. Please set a new password.')
                return redirect('password_reset_confirm')
    else:
        form = OTPVerificationForm()

    return render(request, 'accounts/password_reset_verify.html', {'form': form})


def password_reset_confirm(request):
    if not request.session.get('pwd_reset_verified'):
        messages.error(request, 'Please verify OTP first.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_id = request.session.get('pwd_reset_user_id')
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                messages.error(request, 'User account not found. Start again.')
                return redirect('password_reset_request')

            user.set_password(form.cleaned_data['new_password1'])
            user.save()

            for key in ['pwd_reset_user_id', 'pwd_reset_otp', 'pwd_reset_otp_expires', 'pwd_reset_verified', 'pwd_reset_attempts']:
                request.session.pop(key, None)

            messages.success(request, 'Your password has been reset successfully. Please login.')
            return redirect('login')
    else:
        form = PasswordResetForm()

    return render(request, 'accounts/password_reset_confirm.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have logged out successfully.')
    return redirect('home')


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'donor':
        return redirect('donor_dashboard')
    elif user.role == 'receiver':
        return redirect('receiver_dashboard')
    elif user.role == 'ngo':
        return redirect('ngo_dashboard')
    else:
        return redirect('home')


class ProfileUpdateView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        if user.role == 'donor':
            food_qs = Food.objects.filter(donor=user)
            context['stat1'] = food_qs.count()
            context['stat2'] = food_qs.filter(is_available=True).count()
            context['stat3'] = FoodRequest.objects.filter(food__donor=user, status='pending').count()
        elif user.role == 'receiver':
            req_qs = FoodRequest.objects.filter(receiver=user)
            context['stat1'] = req_qs.count()
            context['stat2'] = req_qs.filter(status='accepted').count()
            context['stat3'] = req_qs.filter(status='pending').count()
        elif user.role == 'ngo':
            del_qs = Delivery.objects.filter(ngo=user)
            context['stat1'] = del_qs.count()
            context['stat2'] = del_qs.filter(status='delivered').count()
            context['stat3'] = del_qs.exclude(status='delivered').count()
        return context


class ProfileDeleteView(DeleteView):
    model = CustomUser
    template_name = 'accounts/profile_confirm_delete.html'
    success_url = reverse_lazy('home')

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Account deleted successfully.')
        return super().delete(request, *args, **kwargs)
