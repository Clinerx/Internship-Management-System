from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils import timezone
from functools import wraps
from random import randint
from .forms import CustomUserCreationForm, OrganizationRegistrationForm
from .models import CustomUser, Organization, UserVisit
import random


User = CustomUser  # Reference your CustomUser model

# Admin view to list all users
def admin(request):
    return render(request, 'admin_folder/admin2.html')

def admin_users(request):
    users = CustomUser.objects.all()
    organizations = Organization.objects.all()
    
    context = {
        'users': users,
        'organizations': organizations,
    }
    
    return render(request, 'admin_folder/admin_view.html', context)

# Check if the email confirmation link has been clicked (used by the waiting area for real-time updates)
def check_confirmation_status(request, token):
    try:
        user = CustomUser.objects.get(reset_token=token)
        if user.reset_token == '':
            return JsonResponse({'confirmed': True})
        return JsonResponse({'confirmed': False})
    except CustomUser.DoesNotExist:
        return JsonResponse({'confirmed': False})

# Delete user and decrement the user count
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, f'User {user.email} deleted successfully.')
    return redirect('admin_view')

def delete_organization(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    organization.delete()
    messages.success(request, f'Organization {organization.company_name} deleted successfully.')
    return redirect('admin_view')

# Generate a 6-digit random OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Home page, shows count of registered users
@login_required(login_url='login')
def home(request):
    user_count = CustomUser.objects.count()  # Count users in CustomUser model
    org_count = Organization.objects.count()  # Count organizations in Organization model
    context = {
        'user_count': user_count,  # Include user count
        'org_count': org_count,     # Include organization count
    }
    return render(request, 'student_pages/student_dashboard.html', context)
# Index page
def index(request):
    return render(request, 'index.html')

# Initial registration page
def initial_registration(request):
    if request.method == 'POST':
        account_type = request.POST.get('account_type')
        if account_type == 'student':
            return redirect('student_register')
        elif account_type == 'organization':
            return redirect('organization_details')
    return render(request, 'initial_registration.html')

# Organization login decorator
def organization_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'organization_id' in request.session:
            return view_func(request, *args, **kwargs)
        return redirect('login')
    return _wrapped_view

# Organization dashboard
@organization_login_required
def org_dashboard(request):
    return render(request, 'organization_registration_folder/organization_dashboard.html')

# Organization registration process
def organization_registration(request):
    if request.method == 'POST':
        company_email = request.POST.get('company_email')
        company_name = request.POST.get('company_name')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        context = {
            'email': company_email,
            'company_name': company_name,
            'first_name': first_name,
            'last_name': last_name,
        }

        if not company_email:
            context['error_message'] = 'Company email is required.'
            return render(request, 'organization_registration_folder/organization_details.html', context)

        # OTP request
        if 'request_otp' in request.POST:
            otp = randint(100000, 999999)
            request.session['otp'] = otp
            request.session['company_email'] = company_email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}. It is valid for 10 minutes.',
                'your-email@gmail.com',
                [company_email],
                fail_silently=False,
            )
            context['otp_message'] = 'OTP has been sent to your email!'
            context['otp_requested'] = True
            return render(request, 'organization_registration_folder/organization_details.html', context)

        # OTP confirmation
        elif 'confirm_otp' in request.POST:
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('otp')
            if entered_otp == str(stored_otp):
                context['otp_confirmed'] = True
                context['otp_message'] = 'OTP confirmed. You can now create your password.'
            else:
                context['error_message'] = 'Invalid OTP. Please try again.'
                context['otp_requested'] = True
            return render(request, 'organization_registration_folder/organization_details.html', context)

        # Final registration after OTP confirmation
        elif 'register' in request.POST:
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            if password == confirm_password:
                hashed_password = make_password(password)
                Organization.objects.create(
                    company_name=company_name,
                    first_name=first_name,
                    last_name=last_name,
                    company_email=company_email,
                    password=hashed_password
                )
                return redirect('success')
            else:
                context['error_message'] = 'Passwords do not match.'
                context['otp_confirmed'] = True
                return render(request, 'organization_registration_folder/organization_details.html', context)

    return render(request, 'organization_registration_folder/organization_details.html')

# Organization registration template
def organization_template(request):
    return render(request, 'organization_registration_folder/organization_details.html')

# OTP verification
def otp_verify(request, token):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            user = CustomUser.objects.get(reset_token=token)
            if str(user.reset_otp) == entered_otp:
                return redirect('reset_password_confirm', token=token)
            else:
                messages.error(request, 'Invalid OTP entered. Please try again.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid reset token.')

    return render(request, 'reset_folder/otp_confirmation.html', {'token': token})

# Password reset request form
def request_form(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            token = get_random_string(length=32)
            user.reset_token = token
            user.reset_otp = random.randint(100000, 999999)
            user.save()

            send_mail(
                'Password Reset Request',
                f'Dear {user.email},\n\nDid you request a reset password? If not, ignore this email. If yes, please use the following OTP: {user.reset_otp}',
                'your_email@example.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, f"A password reset link has been sent to {email}. Please check your inbox.")
            return redirect('otp_verify', token=token)

        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')

    return render(request, 'reset_folder/reset_password_form.html')

# Confirm password reset
def reset_password_confirm(request, token):
    try:
        user = CustomUser.objects.get(reset_token=token)
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                user.set_password(new_password)
                user.reset_token = ''
                user.reset_otp = None
                user.save()
                messages.success(request, 'Your password has been successfully changed!')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        return render(request, 'reset_folder/reset_password_confirm.html', {'token': token})

    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid reset token.')
        return redirect('request_password_reset')

# Success page after organization registration
def success_view(request):
    return render(request, 'organization_registration_folder/success_page.html')

# Student registration
def student_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            visit, created = UserVisit.objects.get_or_create(id=1)
            visit.count += 1
            visit.save()

            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            messages.success(request, f'Account created for {email}')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'student_registration_folder/student_profile_details.html', {'form': form})

# User login

def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            # Handle login for CustomUser
            user = CustomUser.objects.get(email=email)
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password for student account.')

        except CustomUser.DoesNotExist:
            try:
                # Handle login for Organization
                organization = Organization.objects.get(company_email=email)
                if organization.check_password(password):  # Ensure this method is securely implemented
                    login(request, organization)
                    request.session['organization_id'] = organization.id
                    return redirect('organization_dashboard')
                else:
                    messages.error(request, 'Invalid email or password for organization account.')

            except Organization.DoesNotExist:
                messages.error(request, 'No account found with this email.')

    return render(request, 'reset_folder/login.html')

# User logout
@login_required(login_url='login')
def user_logout(request):
    logout(request)
    return redirect('login')

# Visit tracking
def visit_tracker(request):
    visit, created = UserVisit.objects.get_or_create(id=1)
    visit.count += 1
    visit.save()

    users = CustomUser.objects.all()
    return render(request, 'admin_folder/admin_view.html', {'visit_count': visit.count, 'users': users})


def student_internships(request):
    return render(request, 'student_pages/student_internships.html')

def student_status(request):
    return render(request, 'student_pages/student_status.html')

def about_us(request):
    return render(request, 'student_pages/about_us.html')

def student_dashboard(request):
    return render(request, 'student_pages/student_dashboard.html')