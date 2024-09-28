from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'address', 'date_of_birth', 'phone_number', 'email', 'school_name', 'college', 'course']
        widgets = {
            'password': forms.PasswordInput(),
        }
        