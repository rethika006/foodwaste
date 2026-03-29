from django import forms
from .models import FoodRequest


class FoodRequestForm(forms.ModelForm):
    class Meta:
        model = FoodRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }
