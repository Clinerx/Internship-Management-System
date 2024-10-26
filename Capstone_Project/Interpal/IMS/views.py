import json
import random
from functools import wraps
from random import randint
import logging

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import AnonymousUser
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.crypto import get_random_string

from .forms import CustomUserCreationForm, InternshipForm, OrganizationRegistrationForm
from .models import CustomUser, Internship, Organization, UserVisit



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
def student_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')  # Get the email from POST data
        password = request.POST.get('password', '')  # Get the password from POST data

        try:
            # Check if the email exists in CustomUser model (which should be for students)
            user = CustomUser.objects.get(email=email)
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)  # Login the user
                return redirect('home')  # Redirect to the student dashboard (replace 'home' with the correct path)
            else:
                messages.error(request, 'Invalid email or password for student account.')

        except CustomUser.DoesNotExist:
            messages.error(request, 'No student account found with this email.')

        # Re-render the login form with the entered data and error message
        return render(request, 'reset_folder/student_login.html', {'email': email})

    # If the request is GET, render the student login page
    return render(request, 'reset_folder/student_login.html')



def organization_login(request):
    if request.method == 'POST':
        email = request.POST.get('company_email', '')
        password = request.POST.get('password', '')

        # Organization login logic
        try:
            organization = Organization.objects.get(company_email=email)
            if organization.check_password(password):  # Use secure password check
                # Set session variables for organization login
                request.session['organization_id'] = organization.id
                request.session['organization_name'] = organization.company_name
                return redirect('organization_dashboard')  # Redirect to organization dashboard
            else:
                messages.error(request, 'Invalid email or password for organization account.')

        except Organization.DoesNotExist:
            messages.error(request, 'No organization account found with this email.')

        # If login fails, re-render the form with the entered data
        return render(
            request, 
            'reset_folder/organization_login.html', 
            {'email': email}  # Pass the email back to the form
        )

    return render(request, 'reset_folder/organization_login.html')


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

# * Student Pages

@login_required(login_url='login')
def student_dashboard(request):
    users = CustomUser.objects.all()
    organizations = Organization.objects.all()
    org_count = Organization.objects.count()  # Count of registered organizations
    user_count = CustomUser.objects.filter(is_active=True).count()  # Count of registered active students
    context = {
        'org_count': org_count,
        'user_count': user_count,
        'dark_mode': request.session.get('dark_mode', False),  # Include dark_mode in the context
        'user': request.user,  # Pass the user object to the template
        'users': users,
        'organizations': organizations,
    }
    return render(request, 'student_pages/student_dashboard.html', context)

@login_required(login_url='login')
def student_internships(request):
    internships = Internship.objects.all().order_by('-created_at')
    org = Organization.objects.get(id=request.session['organization_id'])
    context = {
        'internships': internships,
        'org': org,
        'user': request.user,  # Pass user data to the template
        'dark_mode': request.session.get('dark_mode', False),  # Include dark_mode in the context
    }
    return render(request, 'student_pages/student_internships.html', context)

def student_status(request):
    context = {
        'dark_mode': request.session.get('dark_mode', False),  # Include dark_mode in the context
    }
    return render(request, 'student_pages/student_status.html', context)

def about_us(request):
    context = {
        'dark_mode': request.session.get('dark_mode', False),  # Include dark_mode in the context
    }
    return render(request, 'student_pages/about_us.html', context)


# View for internship detail (Visit)
def internship_detail(request, id):
    internship = get_object_or_404(Internship, id=id)
    context = {
        'internship': internship,
        'user': request.user,
    }
    return render(request, 'student_pages/internship_detail.html', context)

# View for applying to internship (Apply)
def internship_apply(request, id):
    internship = get_object_or_404(Internship, id=id)
    
    # Logic to handle application goes here. 
    # For now, we'll just render a confirmation page.
    
    context = {
        'internship': internship,
        'user': request.user,
    }
    return render(request, 'student_pages/internship_apply.html', context)


# ^ organization pages

@organization_login_required
def organization_post(request):
    organization = Organization.objects.get(id=request.session['organization_id'])
    internship_posted = request.session.pop('internship_posted', False)

    if request.method == 'POST':
        form = InternshipForm(request.POST)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.organization = organization
            internship.organization_name = organization.company_name
            internship.save()
            request.session['internship_posted'] = True
            return redirect('organization_post')
    else:
        form = InternshipForm()

    internships_list = Internship.objects.filter(organization=organization)
    paginator = Paginator(internships_list, 5)
    page_number = request.GET.get('page')
    internships = paginator.get_page(page_number)
    start_number = (internships.number - 1) * paginator.per_page

    return render(request, 'organization_pages/organization_posting.html', {
        'form': form,
        'internships': internships,
        'org': organization,
        'internship_posted': internship_posted,
        'start_number': start_number
    })

   

@organization_login_required
def view_internship(request, internship_id):
    try:
        # Fetch the internship object based on the provided ID
        internship = Internship.objects.get(id=internship_id)
        
        # Ensure that the internship belongs to the currently logged-in organization
        if internship.organization.id != request.session['organization_id']:
            # Return 403 Forbidden if the organization does not own this internship
            return HttpResponseForbidden("You are not allowed to view this internship.")

    except Internship.DoesNotExist:
        # If the internship does not exist, show a 404 page
        return HttpResponseNotFound("Internship not found.")
    
    # Render the internship details to a template
    return render(request, 'organization_pages/organization_view_page.html', {
        'internship': internship
    })

    
@organization_login_required
def edit_internship(request, internship_id):
    organization = Organization.objects.get(id=request.session['organization_id'])
    
    # Get the specific internship and make sure it belongs to the logged-in organization
    internship = Internship.objects.get(id=internship_id, organization=organization)
    
    if request.method == 'POST':
        form = InternshipForm(request.POST, instance=internship)
        if form.is_valid():
            form.save()  # Save the updated internship
            return redirect('organization_post')  # Redirect to the organization post view
    else:
        form = InternshipForm(instance=internship)  # Load the form with existing internship data
    
    return render(request, 'organization_pages/edit_internship.html', {'form': form, 'internship': internship})

@organization_login_required
def delete_internship(request, internship_id):
    organization = Organization.objects.get(id=request.session['organization_id'])

    # Get the specific internship and ensure it belongs to the logged-in organization
    internship = get_object_or_404(Internship, id=internship_id, organization=organization)

    if request.method == 'POST':
        internship.delete()  # Delete the internship
        return redirect('organization_post')  # Redirect after deletion

    return render(request, 'organization_pages/delete_internship.html', {'internship': internship})


@organization_login_required
def organization_interns(request):
    users = CustomUser.objects.all()
    org = Organization.objects.get(id=request.session['organization_id'])
    
    context = {
        'users': users,
        'org': org,
    }
    return render(request, 'organization_pages/organization_interns.html', context)

@organization_login_required
def organization_applicant(request):
    users = CustomUser.objects.all()
    org = Organization.objects.get(id=request.session['organization_id'])
    
    context = {
        'users': users,
        'org': org,
    }
    return render(request, 'organization_pages/organization_applicants.html', context)

@organization_login_required
def about_us_org(request):
    return render(request, 'organization_pages/about_us_org.html')

@organization_login_required
def org_dashboard(request):
    # Retrieve the organization ID from the session
    organization_id = request.session.get('organization_id')
    
    if organization_id:
        # Fetch the organization object using the ID from the session
        org = Organization.objects.filter(id=organization_id).first()

        # If the organization doesn't exist (for some reason), handle it
        if not org:
            messages.error(request, 'Organization not found. Please log in again.')
            return redirect('login')

        # Fetch additional counts if necessary
        org_count = Organization.objects.count()
        user_count = CustomUser.objects.count()  # Replace with your actual user model

        context = {
            'org': org,
            'org_count': org_count,
            'user_count': user_count,
            'organization_name': org.company_name,  # Optional, passing the organization name
        }

        return render(request, 'organization_pages/organization_dashboard.html', context)

    else:
        # If the organization ID is not in the session, redirect to login
        messages.error(request, 'You must log in to access the dashboard.')
        return redirect('login')
    