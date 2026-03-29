from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    phone = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'address', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['phone', 'address']:
                field.widget.attrs['class'] = 'form-control'


class CustomUserChangeForm(UserChangeForm):
    password = None  # Remove password field

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'autofocus': True,
        'class': 'form-control',
        'autocomplete': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'autocomplete': 'current-password'
    }))


class PasswordResetRequestForm(forms.Form):
    username_or_email = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        label='OTP',
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )


class PasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data
