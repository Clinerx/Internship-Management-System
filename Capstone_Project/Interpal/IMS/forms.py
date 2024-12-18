from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from .models import Organization, Internship

class CustomUserCreationForm(UserCreationForm):
    cor_picture = forms.ImageField(required=False, label="Upload COR")

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'address', 'date_of_birth',
            'phone_number', 'email', 'school_name', 'college', 'course', 'cor_picture'
        ]
        widgets = {
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter Password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
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
    
    
class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = ['title', 'location', 'description', 'requirements', 'application_process', 'max_applicants']
        
    def __init__(self, *args, **kwargs):
        super(InternshipForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['placeholder'] = 'e.g., Software Engineering Intern'
        self.fields['location'].widget.attrs['placeholder'] = 'e.g., New York, NY'
        self.fields['description'].widget.attrs['placeholder'] = 'e.g., Assist in software development...'
        self.fields['requirements'].widget.attrs['placeholder'] = 'e.g., Python, teamwork, communication skills'
        self.fields['application_process'].widget.attrs['placeholder'] = 'e.g., Send resume and cover letter to email@example.com'
        
        
        
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture', 'first_name', 'last_name', 'email', 'phone_number', 'address', 'course', 'college']