from django import forms
from .models import Food


class FoodForm(forms.ModelForm):
    preparation_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    preparation_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    expiry_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = Food
        fields = ['name', 'description', 'quantity', 'location', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['preparation_date'].initial = self.instance.preparation_time.date()
            self.fields['preparation_time'].initial = self.instance.preparation_time.time()
            self.fields['expiry_date'].initial = self.instance.expiry_time.date()
            self.fields['expiry_time'].initial = self.instance.expiry_time.time()

    def clean(self):
        cleaned_data = super().clean()
        prep_date = cleaned_data.get('preparation_date')
        prep_time = cleaned_data.get('preparation_time')
        exp_date = cleaned_data.get('expiry_date')
        exp_time = cleaned_data.get('expiry_time')
        if prep_date and prep_time and exp_date and exp_time:
            from datetime import datetime
            prep_datetime = datetime.combine(prep_date, prep_time)
            exp_datetime = datetime.combine(exp_date, exp_time)
            if exp_datetime <= prep_datetime:
                raise forms.ValidationError("Expiry time must be after preparation time.")
            self.instance.preparation_time = prep_datetime
            self.instance.expiry_time = exp_datetime
        return cleaned_data


class FoodSearchForm(forms.Form):
    SORT_CHOICES = [
        ('recent', 'Most Recent'),
        ('expiry_soon', 'Expiring Soon'),
        ('expiry_later', 'Expiring Later'),
        ('name', 'Food Name (A-Z)'),
    ]
    
    location = forms.CharField(
        max_length=255, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter location (city, area, or address)',
            'aria-label': 'Search by location'
        })
    )
    food_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for food name',
            'aria-label': 'Search by food name'
        })
    )
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='recent',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'aria-label': 'Sort by'
        })
    )


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
