from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Application
from django.core.exceptions import ValidationError
import cloudinary.uploader

from .models import Organization, Internship
class CustomUserCreationForm(UserCreationForm):
    cor_picture = forms.ImageField(required=False, label="Upload COR")

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'address', 'date_of_birth',
            'phone_number', 'email', 'school_name', 'college', 'course', 'cor_picture', 'skills', 'experience'
        ]
        widgets = {
            'password1': forms.PasswordInput(attrs={'placeholder': 'Enter Password'}),
            'password2': forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        allowed_domain = 'psu.palawan.edu.ph'
        
        # Extract the domain part of the email
        domain = email.split('@')[-1] if email else ""
        
        # Validate domain
        if domain != allowed_domain:
            raise ValidationError(f"Registration is only allowed with '{allowed_domain}' email addresses.")
        
        return email
    
class OrganizationRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    otp = forms.CharField(max_length=6, required=False)

    class Meta:
        model = Organization
        fields = ['company_name', 'first_name', 'last_name', 'location', 'company_email', 'otp', 'password', 'confirm_password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class InternshipForm(forms.ModelForm):
    COURSE_CHOICES = {
    'College of Arts and Humanities': [
        ('BA_English', 'Bachelor of Arts in English'),
        ('BA_Literature', 'Bachelor of Arts in Literature'),
        ('BA_Psychology', 'Bachelor of Arts in Psychology'),
        ('BA_Communication', 'Bachelor of Arts in Communication'),
        # Add more courses as needed
    ],
    'College of Business and Accountancy': [
        ('BS_Accountancy', 'Bachelor of Science in Accountancy'),
        ('BS_Business_Administration', 'Bachelor of Science in Business Administration'),
        ('BS_Economics', 'Bachelor of Science in Economics'),
        ('BS_Finance', 'Bachelor of Science in Finance'),
        # Add more courses as needed
    ],
    'College of Criminal Justice Education': [
        ('BS_Criminal_Justice', 'Bachelor of Science in Criminal Justice'),
        ('BS_Criminology', 'Bachelor of Science in Criminology'),
        ('BS_Law_Enforcement', 'Bachelor of Science in Law Enforcement'),
        # Add more courses as needed
    ],
    'College of Engineering, Architecture, and Technology': [
        ('BS_Architecture', 'Bachelor of Science in Architecture'),
        ('BS_Civil_Engineering', 'Bachelor of Science in Civil Engineering'),
        ('BS_Electrical_Engineering', 'Bachelor of Science in Electrical Engineering'),
        ('BS_Mechanical_Engineering', 'Bachelor of Science in Mechanical Engineering'),
        ('BS_Information_Technology', 'Bachelor of Science in Information Technology'),
        # Add more courses as needed
    ],
    'College of Hospitality Management and Tourism': [
        ('BS_Hotel_and_Restaurant_Management', 'Bachelor of Science in Hotel and Restaurant Management'),
        ('BS_Tourism_Management', 'Bachelor of Science in Tourism Management'),
        ('BS_Travel_Management', 'Bachelor of Science in Travel Management'),
        # Add more courses as needed
    ],
    'College of Nursing and Health Sciences': [
        ('BS_Nursing', 'Bachelor of Science in Nursing'),
        ('BS_Pharmacy', 'Bachelor of Science in Pharmacy'),
        ('BS_Medical_Technology', 'Bachelor of Science in Medical Technology'),
        ('BS_Physiotherapy', 'Bachelor of Science in Physiotherapy'),
        # Add more courses as needed
    ],
    'College of Sciences': [
        ('BS_Biology', 'Bachelor of Science in Biology'),
        ('BS_Chemistry', 'Bachelor of Science in Chemistry'),
        ('BS_Physics', 'Bachelor of Science in Physics'),
        ('BS_Mathematics', 'Bachelor of Science in Mathematics'),
        # Add more courses as needed
    ],
    'College of Teacher Education': [
        ('Bachelor_of_Education', 'Bachelor of Education'),
        ('Bachelor_of_Elementary_Education', 'Bachelor of Elementary Education'),
        ('Bachelor_of_Special_Education', 'Bachelor of Special Education'),
        # Add more courses as needed
    ]
}
    class Meta:
        model = Internship
        fields = ['title', 'description', 'application_process', 'max_applicants', 'required_skills', 'required_experience', 'preferred_college', 'preferred_course']

    def __init__(self, *args, **kwargs):
        super(InternshipForm, self).__init__(*args, **kwargs)

        self.fields['title'].widget.attrs['placeholder'] = 'e.g., Software Engineering Intern'
        self.fields['description'].widget.attrs['placeholder'] = 'e.g., Assist in software development...'
        self.fields['application_process'].widget.attrs['placeholder'] = 'e.g., Send resume and cover letter to email@example.com'
        self.fields['required_skills'].widget.attrs['placeholder'] = 'e.g., Python, JavaScript, SQL'
        self.fields['required_experience'].widget.attrs['placeholder'] = 'e.g., 1-2 years'

        self.fields['preferred_college'].choices = [(k, k) for k in self.COURSE_CHOICES.keys()]
        self.fields['preferred_course'].choices = []  # Default to empty until a college is selected

        # Dynamically set course choices if preferred_college is in POST data
        preferred_college = self.data.get('preferred_college')
        if preferred_college in self.COURSE_CHOICES:
            self.fields['preferred_course'].choices = self.COURSE_CHOICES[preferred_college]

        
        
class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture', 'first_name', 'last_name', 'phone_number', 'address', 'course', 'college', 'skills', 'experience']

    # You can add custom validations if needed
    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if skills:
            skills = [skill.strip() for skill in skills.split(',') if skill.strip()]
        return ", ".join(skills)  # Ensure skills are stored in a standardized format

    def clean_experience(self):
        experience = self.cleaned_data.get('experience')
        if experience < 0:
            raise forms.ValidationError("Experience cannot be negative.")
        return experience
    
    
class ProfileFormOrg(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['profile_picture', 'first_name', 'last_name', 'company_name',]


   
def validate_pdf_or_txt(file):
    valid_mime_types = ['application/pdf', 'text/plain']
    if file.content_type not in valid_mime_types:
        raise ValidationError('Invalid file format. Please upload a PDF or TXT file.')

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'application_letter']

    resume = forms.FileField(
        required=True,
        validators=[validate_pdf_or_txt],
        label="Upload Resume",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control shadow-sm',
            'accept': '.pdf,.txt'
        }),
        help_text="Accepted formats: PDF, TXT"
    )

    application_letter = forms.FileField(
        required=True,
        validators=[validate_pdf_or_txt],
        label="Upload Application Letter",
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control shadow-sm',
            'accept': '.pdf,.txt'
        }),
        help_text="Accepted formats: PDF, TXT"
    )