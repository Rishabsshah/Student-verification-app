from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

class PasswordOnlyForm(forms.Form):
    """Form for Step 4 - only asks for password"""
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'id': 'id_password1'}),
        min_length=6
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'id': 'id_password2'}),
        min_length=6
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data
