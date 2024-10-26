from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings  # This will allow us to reference the CustomUser model
from django.contrib.auth.hashers import check_password
from django.utils import timezone

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

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    school_name = models.CharField(max_length=255, blank=True, null=True)
    college = models.CharField(max_length=255, blank=True, null=True)
    course = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=32, null=True, blank=True)
    reset_otp = models.IntegerField(blank=True, null=True)

    # One-to-one relationship with Organization (optional)
    organization = models.OneToOneField(
        'Organization', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user'  # Reverse relation name
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'date_of_birth']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True


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
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

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
    title = models.CharField(max_length=200, null=True)
    organization = models.ForeignKey(
        Organization, 
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

    def __str__(self):
        return self.title

    def get_applications(self):
        return self.applications.all()