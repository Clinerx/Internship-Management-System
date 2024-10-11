from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import Organization


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'address', 'date_of_birth', 'phone_number', 'email', 'school_name', 'college', 'course']
        widgets = {
            'password': forms.PasswordInput(),
        }
    
class OrganizationRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    otp = forms.CharField(max_length=6, required=False)

    class Meta:
        model = Organization
        fields = ['company_name', 'first_name', 'last_name', 'company_email', 'otp', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data