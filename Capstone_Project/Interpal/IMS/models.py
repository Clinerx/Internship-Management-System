from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings  # This will allow us to reference the CustomUser model
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError
from django.urls import reverse  # Import reverse for URL generation

def validate_image_extension(value):
    """Validate that the uploaded file is an image."""
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
    file_extension = value.name.split('.')[-1].lower()
    if file_extension not in valid_extensions:
        raise ValidationError('Only image files (jpg, jpeg, png, gif) are allowed.')
# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError("The Email field is required")
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None):
        user = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
COLLEGE_CHOICES = [
    ('College of Arts and Humanities', 'College of Arts and Humanities'),
    ('College of Business and Accountancy', 'College of Business and Accountancy'),
    ('College of Criminal Justice Education', 'College of Criminal Justice Education'),
    ('College of Engineering, Architecture, and Technology', 'College of Engineering, Architecture, and Technology'),
    ('College of Hospitality Management and Tourism', 'College of Hospitality Management and Tourism'),
    ('College of Nursing and Health Sciences', 'College of Nursing and Health Sciences'),
    ('College of Sciences', 'College of Sciences'),
    ('College of Teacher Education', 'College of Teacher Education'),
]

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    school_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Modify the college field to use choices
    college = models.CharField(max_length=255, choices=COLLEGE_CHOICES, blank=True, null=True)
    
    course = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=32, null=True, blank=True)
    reset_otp = models.IntegerField(blank=True, null=True)
    cor_picture = CloudinaryField('image', blank=True, null=True, folder='cor_pictures')
    profile_picture = CloudinaryField('image', blank=True, null=True, folder='profile_picture')
    organization = models.OneToOneField(
        'Organization', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user'
    )
    skills = models.TextField(help_text="Comma-separated skills", blank=True, null=True)
    experience = models.PositiveIntegerField(default=0)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'date_of_birth', 'cor_picture']

    def __str__(self):
        return self.email

    def skills_list(self):
        """Return a list of skills."""
        return [skill.strip().lower() for skill in (self.skills or "").split(",") if skill.strip()]



class UserVisit(models.Model):
    count = models.IntegerField(default=0)

    def __str__(self):
        return str(self.count)

class OrganizationManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, company_name, password=None):
        if not email:
            raise ValueError("The Email field is required")
        organization = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
        )
        organization.set_password(password)
        organization.save(using=self._db)
        return organization

    def create_superuser(self, email, first_name, last_name, company_name, password=None):
        organization = self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            password=password
        )
        organization.is_admin = True
        organization.is_staff = True
        organization.is_superuser = True
        organization.save(using=self._db)
        return organization

class Organization(models.Model):
    
    company_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    company_email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    location = models.CharField(max_length=200, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    profile_picture = CloudinaryField('image', blank=True, null=True)
    credential_upload = CloudinaryField('image', blank=True, null=True)

    objects = OrganizationManager()

    USERNAME_FIELD = 'company_email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'company_name']

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

    def __str__(self):
        return self.company_name

class Internship(models.Model):
    
    COLLEGE_CHOICES = [
        ('College of Arts and Humanities', 'College of Arts and Humanities'),
        ('College of Business and Accountancy', 'College of Business and Accountancy'),
        ('College of Criminal Justice Education', 'College of Criminal Justice Education'),
        ('College of Engineering, Architecture, and Technology', 'College of Engineering, Architecture, and Technology'),
        ('College of Hospitality Management and Tourism', 'College of Hospitality Management and Tourism'),
        ('College of Nursing and Health Sciences', 'College of Nursing and Health Sciences'),
        ('College of Sciences', 'College of Sciences'),
        ('College of Teacher Education', 'College of Teacher Education'),
    ]
    
    title = models.CharField(max_length=200, null=True)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.SET_NULL,
        null=True,
        related_name='internships'
    )
    location = models.CharField(max_length=200, null=True)
    description = models.TextField()
    requirements = models.TextField()
    application_process = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    max_applicants = models.PositiveIntegerField(default=1)
    required_skills = models.TextField(blank=True, null=True)
    required_experience = models.PositiveIntegerField(null=True, blank=True)
    
    # Add these two fields for preferred college and course
    preferred_college = models.CharField(
        max_length=255,
        choices=COLLEGE_CHOICES,
        null=True
    )
    preferred_course = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title

    def get_applications(self):
        return self.applications.all()

    def get_absolute_url(self):
        """Return the URL for the internship's detail page."""
        return reverse('internship_detail', args=[str(self.id)])
    
    def required_skills_list(self):
        """Return a list of required skills."""
        return [skill.strip().lower() for skill in (self.requirements or "").split(",") if skill.strip()]

    def set_preferred_course(self):
        """Set the preferred courses based on the selected college."""
        if self.preferred_college in self.COURSE_CHOICES:
            self.preferred_course = self.COURSE_CHOICES[self.preferred_college][0][0]


    
class Application(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Review', 'In Review'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Offer Extended', 'Offer Extended'),
        ('Completed', 'Completed')
    ]

    internship = models.ForeignKey(
        'Internship',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        null=True
    )
    student_first_name = models.CharField(max_length=255, null=True)
    student_last_name = models.CharField(max_length=255, null=True)
    student_college = models.CharField(max_length=255, null=True)
    student_course = models.CharField(max_length=255, null=True)
    resume = CloudinaryField('file', folder='resumes', blank=True, null=True)
    application_letter = CloudinaryField('file', folder='application_letters', blank=True, null=True)
    applied_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    
    review_stage = models.CharField(max_length=100, default="Under Review")
    comments = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only set on creation
            self.organization = self.internship.organization
            self.student_first_name = self.student.first_name
            self.student_last_name = self.student.last_name
            self.student_college = self.student.college
            self.student_course = self.student.course
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_first_name} {self.student_last_name} - {self.internship.title}"

    def get_student_profile_picture(self):
        if self.student.profile_picture:
            return self.student.profile_picture.url
        return None
    
    
    
    
class OrganizationIntern(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, null=True) 
    hire_date = models.DateField(auto_now_add=True)
    start_date = models.DateField(null=True)  # Specifies when the internship starts
    end_date = models.DateField(null=True)  # Specifies when the internship ends

    def __str__(self):
        return (
            f"{self.student.first_name} {self.student.last_name} - "
            f"{self.internship.title} at {self.organization.name} "
            f"from {self.start_date} to {self.end_date}"
        )





class AccountApproval(models.Model):
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE, null=True, blank=True)  # Make user nullable
    is_approved = models.BooleanField(default=False)  # False = Pending, True = Approved
    email = models.EmailField(null=True, blank=True)  # Email field for notifications
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {'Approved' if self.is_approved else 'Pending'}"
        return f"Unknown Account - {'Approved' if self.is_approved else 'Pending'}"

class OrganizationApproval(models.Model):
    organization = models.OneToOneField('Organization', on_delete=models.CASCADE)  # Reference to the organization
    is_approved = models.BooleanField(default=False)  # Approval status
    email = models.EmailField(null=True, blank=True)  # Email field for notifications
    approval_date = models.DateTimeField(null=True, blank=True)  # When approval was granted
    created_at = models.DateTimeField(auto_now_add=True)  # Record creation timestamp

    def __str__(self):
        return f"{self.organization.company_name} - {'Approved' if self.is_approved else 'Pending'}"

    def approve(self):
        """Approve the organization account."""
        self.is_approved = True
        self.approval_date = now()
        self.save()

    def revoke_approval(self):
        """Revoke the approval."""
        self.is_approved = False
        self.approval_date = None
        self.save()
