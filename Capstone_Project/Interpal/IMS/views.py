import random
import smtplib
import dns.resolver
from .utils import calculate_cosine_similarity
from cloudinary.utils import cloudinary_url
from functools import wraps
from random import randint
from django.views.decorators.cache import cache_control
from django.db.models.functions import TruncMonth
from mimetypes import guess_type
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
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
from django.db.models.functions import ExtractMonth
import cloudinary.uploader
from django.db.models import Q
from django.utils.timezone import now
from django.utils import timezone
from random import randint
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm
from .models import AccountApproval, UserVisit
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.crypto import get_random_string
from django.core.mail import EmailMessage


from collections import defaultdict

from .forms import CustomUserCreationForm, InternshipForm, ProfileForm, ProfileFormOrg, ApplicationForm
from .models import CustomUser, Internship, Organization, UserVisit, Application, OrganizationIntern, AccountApproval



User = CustomUser  # Reference your CustomUser model



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
        location = request.POST.get('location')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        context = {
            'email': company_email,
            'company_name': company_name,
            'location': location,
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
                'psuinterpal@gmail.com',
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
                    location=location,
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

def verify_email(email):
    domain = "psu.palawan.edu.ph"
    
    # Check if email belongs to the specific domain
    if not email.endswith(f"@{domain}"):
        return "Invalid domain for this email"
    
    try:
        # Check MX records for the domain
        mx_records = dns.resolver.resolve(domain, 'MX')
        mail_server = mx_records[0].exchange.to_text()
        
        # Perform SMTP check
        with smtplib.SMTP(mail_server, 25, timeout=10) as smtp:
            smtp.helo("example.com")  # Identify the client
            smtp.mail("test@example.com")  # Fake sender
            code, message = smtp.rcpt(email)  # Test recipient
            smtp.quit()
            if code == 250:
                return "Email exists"
            else:
                return "Email does not exist or is rejected"
    except Exception as e:
        return f"Error occurred: {e}"
    
    
def student_register(request):
    if request.method == 'POST':
        # Retrieve form data
        form = CustomUserCreationForm(request.POST, request.FILES)
        email = request.POST.get('email')

        # Context for the form and messages
        context = {'form': form}

        # Step 1: OTP Request
        if 'request_otp' in request.POST:
            if email:
                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    context['error_message'] = 'This email is already in use.'
                    return render(request, 'student_registration_folder/student_profile_details.html', context)
                
                # Validate domain and email existence
                email_check = verify_email(email)
                if email_check != "Email exists":
                    context['error_message'] = f'Invalid email: {email_check}'
                    return render(request, 'student_registration_folder/student_profile_details.html', context)

                otp = randint(100000, 999999)
                request.session['otp'] = otp
                request.session['email'] = email
                try:
                    send_mail(
                        'Your OTP Code',
                        f'Your OTP code is {otp}. It is valid for 10 minutes.',
                        'psuinterpal@gmail.com',
                        [email],
                        fail_silently=False,
                    )
                    context['otp_message'] = 'OTP has been sent to your email!'
                    context['otp_requested'] = True
                except Exception as e:
                    context['error_message'] = f'Failed to send OTP: {e}'
            else:
                context['error_message'] = 'Email is required to request an OTP.'
            return render(request, 'student_registration_folder/student_profile_details.html', context)

        # Step 2: OTP Confirmation
        elif 'confirm_otp' in request.POST:
            entered_otp = request.POST.get('otp')
            stored_otp = request.session.get('otp')
            if entered_otp == str(stored_otp):
                request.session['otp_confirmed'] = True  # Persist in session
                context['otp_confirmed'] = True
                context['otp_message'] = 'OTP confirmed. You can now complete the registration.'
            else:
                context['error_message'] = 'Invalid OTP. Please try again.'
                context['otp_requested'] = True
            return render(request, 'student_registration_folder/student_profile_details.html', context)

        # Step 3: Final Registration
        elif 'register' in request.POST:
            if form.is_valid() and request.session.get('otp_confirmed', False):
                try:
                    # Check if email already exists again for extra safety
                    if User.objects.filter(email=email).exists():
                        context['error_message'] = 'This email is already in use.'
                        context['otp_confirmed'] = True
                        return render(request, 'student_registration_folder/student_profile_details.html', context)

                    user = form.save(commit=False)
                    user.password = make_password(form.cleaned_data['password1'])
                    user.save()

                    # Create an AccountApproval instance for the new user
                    AccountApproval.objects.create(user=user, is_approved=False)

                    # Increment visit count
                    visit, created = UserVisit.objects.get_or_create(id=1)
                    visit.count += 1
                    visit.save()

                    # Notify admin about new registration
                    try:
                        send_mail(
                            'New Account Registration Awaiting Approval',
                            f'A new account with the email {email} has been registered and is awaiting approval.',
                            'psuinterpal@gmail.com',
                            ['psuinterpal@gmail.com'],  # Admin email
                            fail_silently=False,
                        )
                    except Exception as e:
                        context['error_message'] = f'Failed to notify admin: {e}'

                    # Clear session data
                    request.session.pop('otp', None)
                    request.session.pop('otp_confirmed', None)
                    request.session.pop('email', None)

                    messages.success(request, 'Account created successfully! Your account is awaiting approval. Please log in after approval.')
                    return redirect('login')
                except Exception as e:
                    context['error_message'] = f'Error during registration: {e}'
                    context['otp_confirmed'] = True
            else:
                context['error_message'] = 'Please complete the OTP confirmation or fix form errors.'
                context['otp_requested'] = True
            return render(request, 'student_registration_folder/student_profile_details.html', context)

    # GET request or initial load
    form = CustomUserCreationForm()
    return render(request, 'student_registration_folder/student_profile_details.html', {'form': form})




def student_login(request):
    # If the user is already authenticated, redirect them to the dashboard
    if request.user.is_authenticated:
        email = request.GET.get('email')
        if email and email != request.user.email:
            logout(request)  # Logout if the email in the query string differs
        else:
            return redirect('student_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Validate that both fields are entered
        if not email or not password:
            messages.error(request, 'Please enter both email and password.', extra_tags='login')
            return render(request, 'reset_folder/student_login.html', {'email': email})

        try:
            # Check if the email exists in the CustomUser model
            user = CustomUser.objects.get(email=email)
            
            # Authenticate the user
            user = authenticate(request, email=email, password=password)
            if user is not None:
                # Check account approval status
                try:
                    approval = AccountApproval.objects.get(user=user)
                    if not approval.is_approved:
                        messages.error(request, 'Your account is not approved yet. Please wait for approval.', extra_tags='login')
                        return render(request, 'reset_folder/student_login.html', {'email': email})
                except AccountApproval.DoesNotExist:
                    messages.error(request, 'Account approval pending.', extra_tags='login')
                    return render(request, 'reset_folder/student_login.html', {'email': email})
                
                # If approved, log in the user
                login(request, user)
                messages.success(request, 'Login successful! Redirecting to your dashboard...', extra_tags='login')
                return redirect('student_dashboard')  # Adjust to your actual dashboard route
            else:
                messages.error(request, 'Invalid email or password for student account.', extra_tags='login')

        except CustomUser.DoesNotExist:
            messages.error(request, 'No student account found with this email.', extra_tags='login')

    # Render the login page for GET requests or after errors
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
def user_logout(request):
    logout(request)
    return redirect('index')

# Visit tracking
def visit_tracker(request):
    visit, created = UserVisit.objects.get_or_create(id=1)
    visit.count += 1
    visit.save()

    users = CustomUser.objects.all()
    return render(request, 'admin_folder/admin_view.html', {'visit_count': visit.count, 'users': users})


# * Student Pages =============================
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@login_required(login_url='login')
def student_dashboard(request):
    # Basic counts
    users = CustomUser.objects.all()
    organizations = Organization.objects.all()
    org_count = Organization.objects.count()
    user_count = CustomUser.objects.filter(is_active=True).count()
    internship_count = Internship.objects.count()

    # Monthly registration data for the current year
    current_year = now().year
    org_data = (
        Organization.objects
        .filter(date_joined__year=current_year)
        .annotate(month=ExtractMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    user_data = (
        CustomUser.objects
        .filter(date_joined__year=current_year)
        .annotate(month=ExtractMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Prepare monthly data arrays
    org_counts = [0] * 12
    user_counts = [0] * 12
    for item in org_data:
        org_counts[item['month'] - 1] = item['count']
    for item in user_data:
        user_counts[item['month'] - 1] = item['count']

    # Calculate internship recommendations for the logged-in user
    recommendations = []
    if request.user.is_authenticated and not request.user.is_admin:
        relevant_internships = Internship.objects.filter(
            preferred_college=request.user.college,
            preferred_course=request.user.course
    )

    recommendations = [
        (internship, calculate_cosine_similarity(request.user, internship))
        for internship in relevant_internships
    ]
    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)

    # Context for template rendering
    context = {
        'org_count': org_count,
        'user_count': user_count,
        'internship_count': internship_count,
        'dark_mode': request.session.get('dark_mode', False),
        'user': request.user,
        'users': users,
        'organizations': organizations,
        'org_counts': org_counts,
        'user_counts': user_counts,
        'recommendations': recommendations[:5],  # Top 5 matches
    }
    
    return render(request, 'student_pages/student_dashboard.html', context)


# * <<<<<<<============================================>>>> 
# ^ Student Internship

@login_required(login_url='login')
def student_internships(request):
    internships_list = Internship.objects.all().order_by('-created_at')
    paginator = Paginator(internships_list, 9)  # Display 6 internships per page
    page_number = request.GET.get('page')
    internships = paginator.get_page(page_number)
    
    organization_id = request.session.get('organization_id')
    org = None

    if organization_id:
        org = get_object_or_404(Organization, id=organization_id)

    # Check for the application submission notification flag
    application_submitted = request.session.pop('application_submitted', False)  # Retrieve and clear flag

    # Get all applications for the current user
    user_applications = Application.objects.filter(student=request.user)
    applied_internship_ids = user_applications.values_list('internship_id', flat=True)

    context = {
        'internships': internships,  # Pass the paginated internships
        'org': org,
        'user': request.user,
        'dark_mode': request.session.get('dark_mode', False),
        'application_submitted': application_submitted,  # Pass flag to template
        'applied_internship_ids': applied_internship_ids  # Pass IDs of applied internships
    }
    return render(request, 'student_pages/student_internships.html', context)


# View for internship detail (Visit)
def internship_detail(request, id):
    internship = get_object_or_404(Internship, id=id)
    context = {
        'internship': internship,
        'user': request.user,
    }
    return render(request, 'student_pages/student_internship_content/internship_detail.html', context)

# * <<<<<<<============================================>>>>
# ^ Edit Profile

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_dashboard')
    else:
        form = ProfileForm(instance=request.user)

    context = {
        'form': form,
    }
    return render(request, 'student_pages/edit_profile.html', context)


@organization_login_required
def edit_profile_org(request):
    # Fetch the logged-in organization's profile using the organization_id from session
    organization_id = request.session.get('organization_id')
    if not organization_id:
        messages.error(request, 'Organization not found.')
        return redirect('login')
    
    try:
        org = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        messages.error(request, 'Organization not found.')
        return redirect('login')
    
    if request.method == 'POST':
        form = ProfileFormOrg(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('organization_dashboard')
    else:
        form = ProfileFormOrg(instance=org)

    context = {
        'form': form,
        'organization': org,
    }
    return render(request, 'organization_pages/edit_profile_org.html', context)




# * <<<<<<<============================================>>>> 
# ^ Student Status Content
def apply_to_internship(request):
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.student = request.user
            application.save()
            return redirect('success_page')  # Replace with your success page
    else:
        form = ApplicationForm()
    return render(request, 'apply.html', {'form': form})

@login_required(login_url='login')
def internship_apply(request, internship_id):
    internship = get_object_or_404(Internship, id=internship_id)
    student = request.user  # Assuming the user is authenticated as a student

    # Check if the student has already applied to this internship
    already_applied = Application.objects.filter(internship=internship, student=student).exists()

    # Count the number of applications the student has made to this organization
    applications_count = Application.objects.filter(
        student=student, internship__organization=internship.organization
    ).count()

    # Check if the student can apply
    can_apply = internship.max_applicants > 0 and not already_applied and applications_count < 3

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if can_apply and form.is_valid():
            # Save the application along with file uploads
            application = form.save(commit=False)
            application.internship = internship
            application.organization = internship.organization
            application.student = student
            application.save()

            # Reduce the number of available slots for the internship
            internship.max_applicants -= 1
            internship.save()

            # Notify success and redirect
            messages.success(request, "Your application has been submitted successfully.")
            return redirect('student_internships')
        else:
            # Notify why the application failed
            if not can_apply:
                messages.error(request, "You cannot apply for this internship due to application limits or availability.")
            elif not form.is_valid():
                messages.error(request, "There was an error with your submission. Please check your inputs.")
    else:
        form = ApplicationForm()

    # Context for the template
    context = {
        'internship': internship,
        'form': form,
        'already_applied': already_applied,
        'applications_count': applications_count,
        'can_apply': can_apply,
    }
    return render(request, 'student_pages/student_internship_content/internship_apply.html', context)


@login_required(login_url='login')
def student_status(request):
    search_query = request.GET.get('search', '')
    applications = Application.objects.filter(student=request.user).select_related('internship', 'internship__organization')

    if search_query:
        applications = applications.filter(
            Q(internship__title__icontains=search_query) |
            Q(internship__organization__company_name__icontains=search_query)
        )

    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'dark_mode': request.session.get('dark_mode', False),
        'applications': page_obj,
        'user': request.user,
        'search_query': search_query,
    }
    return render(request, 'student_pages/student_status_content/student_status.html', context)


@login_required(login_url='login')
def delete_applications(request, application_id=None):
    # Handle individual application deletion if application_id is provided
    if application_id:
        application = get_object_or_404(Application, id=application_id, student=request.user)
        
        if request.method == 'POST':
            internship = application.internship
            application.delete()
            internship.max_applicants += 1
            internship.save()
            messages.success(request, "Your application has been successfully deleted.")
            return redirect('student_status')

        return render(request, 'student_pages/student_status_content/delete_application_confirm.html', {'application': application})

    # Handle bulk deletion
    if request.method == 'POST':
        selected_application_ids = request.POST.getlist('application_ids')
        
        for app_id in selected_application_ids:
            application = get_object_or_404(Application, id=app_id, student=request.user)
            internship = application.internship
            application.delete()
            internship.max_applicants += 1
            internship.save()

        messages.success(request, "Selected applications have been successfully deleted.")
        return redirect('student_status')

    # Optionally handle GET requests if needed, or redirect
    return redirect('student_status')


def view_status(request, application_id):
    application = get_object_or_404(Application, id=application_id)

    # Define the base stages of the application process
    stages = ["Pending", "In Review", "Interview Scheduled", "Confirmation", "Hired"]

    # Replace "Phantom Hired" with the actual final status
    if application.status == "Hired":
        stages[-1] = "Hired"
    elif application.status == "Rejected":
        stages[-1] = "Rejected"

    # Determine the stages completed based on the current status
    if application.status in stages:
        completed_stages = stages[:stages.index(application.status) + 1]
    else:
        completed_stages = []

    # Add custom messages for the final stages
    if application.status == "Hired":
        status_message = "Congratulations! You have been hired for the position."
    elif application.status == "Rejected":
        status_message = "We regret to inform you that your application has been rejected."
    else:
        status_message = f"Your application is currently in the '{application.status}' stage."

    # Prepare status details for rendering
    status_details = {
        "status": application.status,
        "review_stage": application.review_stage,
        "submission_date": application.applied_at,
        "comments": application.comments,
        "completed_stages": completed_stages,
        "status_message": status_message,  # Custom message based on the current status
    }

    context = {
        'application': application,
        'status_details': status_details,
        'stages': stages,
    }
    return render(request, 'student_pages/student_status_content/view_status.html', context)







# * <<<<<<<============================================>>>> 
# ^ Student About Us

def about_us(request):
    context = {
        'dark_mode': request.session.get('dark_mode', False),  # Include dark_mode in the context
    }
    return render(request, 'student_pages/about_us.html', context)

# * <<<<<<<============================================>>>> 
# ^ organization pages ============================
# Define a posting limit (you can set this in settings.py)
# Set the posting limit from settings, with a default value of 5
POSTING_LIMIT = getattr(settings, 'INTERNSHIP_POSTING_LIMIT', 5)

@organization_login_required
def organization_post(request):
    # Get the organization ID from the session
    organization_id = request.session.get('organization_id')
    if not organization_id:
        messages.error(request, "No organization is currently logged in.")
        return redirect('login')  # Redirect to login if no organization is found

    # Fetch the organization object
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        messages.error(request, "The logged-in organization does not exist.")
        return redirect('login')  # Redirect to login if the organization is invalid

    # Check if a new internship was successfully posted
    internship_posted = request.session.pop('internship_posted', False)

    # Fetch all internships posted by this organization
    internships_list = Internship.objects.filter(organization=organization)
    current_postings_count = internships_list.count()

    # Calculate the remaining postings
    remaining_postings = POSTING_LIMIT - current_postings_count

    if request.method == 'POST':
        # Prevent new posts if the posting limit is reached
        if current_postings_count >= POSTING_LIMIT:
            messages.error(request, f"You have reached the posting limit of {POSTING_LIMIT} internships.")
            return redirect('organization_post')

        # Process the form submission
        form = InternshipForm(request.POST)
        if form.is_valid():
            internship = form.save(commit=False)
            internship.organization = organization
            internship.organization_name = organization.company_name
            internship.save()

            # Indicate successful posting
            request.session['internship_posted'] = True
            messages.success(request, "Internship posted successfully!")
            return redirect('organization_post')
        else:
            messages.error(request, "There was an error in your form submission.")
    else:
        form = InternshipForm()

    # Paginate the internships list
    paginator = Paginator(internships_list, 5)  # Show 5 internships per page
    page_number = request.GET.get('page')
    internships = paginator.get_page(page_number)
    start_number = (internships.number - 1) * paginator.per_page

    # Render the organization posting page
    return render(request, 'organization_pages/organization_posting.html', {
        'form': form,
        'internships': internships,
        'org': organization,
        'internship_posted': internship_posted,
        'start_number': start_number,
        'current_postings_count': current_postings_count,
        'posting_limit': POSTING_LIMIT,
        'remaining_postings': remaining_postings,
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
    # Check if 'organization_id' is in session
    organization_id = request.session.get('organization_id')
    if not organization_id:
        messages.error(request, "No organization is currently logged in.")
        return redirect('login')

    # Get the organization
    org = Organization.objects.get(id=organization_id)

    # Fetch interns and their related internship details
    interns = OrganizationIntern.objects.filter(hiring_organization=org).select_related('student', 'internship')

    context = {
        'interns': interns,
        'org': org,
    }
    return render(request, 'organization_pages/organization_interns.html', context)

@organization_login_required
def organization_applicant(request):
    # Retrieve the organization based on session or user
    org = None
    if 'organization_id' in request.session:
        org = get_object_or_404(Organization, id=request.session['organization_id'])
    elif hasattr(request.user, 'organization'):
        org = request.user.organization
    
    if not org:
        # Redirect to an error page if no organization is found
        return redirect('error_page')  # Replace with the actual error page

    # Fetch applications related to this organization
    applications = Application.objects.filter(
        internship__organization=org
    ).select_related('internship', 'student')

    # Group applications by internship and annotate details
    grouped_applications = {}
    for application in applications:
        # Check if the student is hired and get the hiring organization
        hired_application = Application.objects.filter(
            student=application.student, status="Hired"
        ).select_related('internship__organization').first()
        
        application.is_hired = bool(hired_application)
        application.hiring_organization = hired_application.internship.organization if hired_application else None

        # Calculate similarity score (ensure this function handles exceptions)
        try:
            student = application.student
            internship = application.internship
            application.similarity_score = calculate_cosine_similarity(student, internship) or 0
        except Exception as e:
            application.similarity_score = 0  # Fallback in case of error
            print(f"Error calculating similarity: {e}")

        # Group applications by internship
        if internship not in grouped_applications:
            grouped_applications[internship] = []
        grouped_applications[internship].append(application)

    context = {
        'grouped_applications': grouped_applications,
        'organization': org,
    }
    return render(request, 'organization_pages/organization_applicants.html', context)

@organization_login_required
def view_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, organization_id=request.session['organization_id'])

    # Define the base stages of the application process
    stages = ["Pending", "In Review", "Interview Scheduled", "Confirmation", "Hired"]

    # Update the final stage based on the application's status
    if application.status == "Hired":
        stages[-1] = "Hired"
    elif application.status == "Rejected":
        stages[-1] = "Rejected"

    # Determine the stages completed based on the current status
    completed_stages = stages[:stages.index(application.status) + 1] if application.status in stages else []

    # Custom status messages
    status_messages = {
        "Hired": "Congratulations! You have been hired for the position.",
        "Rejected": "We regret to inform you that your application has been rejected.",
    }
    status_message = status_messages.get(application.status, f"Your application is currently in the '{application.status}' stage.")

    # Handle POST requests for status updates
    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status == "Hired":
            application.status = "Hired"
            application.final_decision = "approved"
            application.save()

            # Handle the start and end dates when the status is "Hired"
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date and end_date:
                OrganizationIntern.objects.create(
                    organization_id=request.session['organization_id'],
                    student=application.student,
                    start_date=start_date,
                    end_date=end_date,
                )
                messages.success(request, f"The student {application.student.first_name} {application.student.last_name} has been approved and marked as hired.")
                messages.success(request, "Internship dates have been saved.")
            else:
                messages.error(request, "Please provide both start and end dates for the internship.")
            
            # Send email to the student about approval
            subject = "Congratulations! You have been hired"
            message = f"Dear {application.student.first_name},\n\nWe are pleased to inform you that you have been hired for the internship at {application.organization.company_name}. Your internship dates are from {start_date} to {end_date}.\n\nBest regards,\n{application.organization.company_name}\n {application.organization.company_email}"
            recipient = application.student.email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])

        elif new_status == "Rejected":
            application.status = "Rejected"
            application.final_decision = "declined"
            application.save()
            messages.success(request, f"The student {application.student.first_name} {application.student.last_name} has been declined.")
            
            # Send email to the student about rejection
            subject = "Application Status: Rejected"
            message = f"Dear {application.student.first_name},\n\nWe regret to inform you that your application has been rejected by {application.organization.name}. We wish you the best in your future endeavors.\n\nBest regards,\n{application.organization.name}"
            recipient = application.student.email
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])

        elif new_status in stages:
            application.status = new_status
            application.save()
            messages.success(request, "Application status updated successfully.")

        return redirect(reverse('view_application', args=[application_id]))

    # Helper function to check if a file is a PDF
    def is_pdf(file_url):
        mime_type, _ = guess_type(file_url)
        return mime_type == "application/pdf"

    # File details for previewing
    file_details = {
        'resume': {
            'url': application.resume.url if application.resume else None,
            'is_pdf': is_pdf(application.resume.url) if application.resume else False,
        },
        'application_letter': {
            'url': application.application_letter.url if application.application_letter else None,
            'is_pdf': is_pdf(application.application_letter.url) if application.application_letter else False,
        },
    }

    # Context for the template
    context = {
        'application': application,
        'status_details': {
            "status": application.status,
            "review_stage": application.review_stage,
            "submission_date": application.applied_at,
            "comments": application.comments,
            "completed_stages": completed_stages,
            "status_message": status_message,
        },
        'stages': stages,
        'completed_stages': completed_stages,
        'file_details': file_details,  # Pass file details for rendering in the template
    }
    return render(request, 'organization_pages/view_application.html', context)



@organization_login_required
def organization_interns(request):
    interns = OrganizationIntern.objects.filter(organization_id=request.session['organization_id'])

    context = {
        'interns': interns,
    }
    return render(request, 'organization_pages/organization_interns.html', context)


# View for updating the application status by organization
@organization_login_required
def update_application_status(request, application_id):
    application = get_object_or_404(Application, id=application_id, organization_id=request.session['organization_id'])
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):  # Ensure new_status is valid
            application.status = new_status
            application.save()
            messages.success(request, "Application status updated successfully.")
        else:
            messages.error(request, "Invalid status selected.")
    
    return redirect('view_application', application_id=application.id)

@organization_login_required
def delete_application(request, application_id):
    try:
        application = Application.objects.get(id=application_id, organization_id=request.session['organization_id'])
        application.delete()
        messages.success(request, "Application deleted successfully.")
    except Application.DoesNotExist:
        messages.error(request, "Application not found or you don't have permission to delete it.")
    return redirect('organization_applicant')


# * ================ Application =========================
@organization_login_required
def about_us_org(request):
    return render(request, 'organization_pages/about_us_org.html')

@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@organization_login_required
def org_dashboard(request):
    
    organization_id = request.session.get('organization_id')
    
    if organization_id:
        org = Organization.objects.filter(id=organization_id).first()
        
        if not org:
            messages.error(request, 'Organization not found. Please log in again.')
            return redirect('login')

        org_count = Organization.objects.count()
        user_count = CustomUser.objects.count()
        student_applicants = Application.objects.count()

        # Monthly internship counts per organization
        monthly_data = (Internship.objects
                        .annotate(month=TruncMonth('created_at'))
                        .values('month', 'organization__company_name')
                        .annotate(count=Count('id'))
                        .order_by('month', 'organization__company_name'))

        # Prepare data for consistent months across all organizations
        organization_data = defaultdict(lambda: {'months': [], 'counts': []})
        month_labels = []

        # Gather unique months across all organizations
        for entry in monthly_data:
            month_str = entry['month'].strftime('%B')
            if month_str not in month_labels:
                month_labels.append(month_str)

        # Populate organization data with counts per month, ensuring consistent months
        for entry in monthly_data:
            month_str = entry['month'].strftime('%B')
            organization_name = entry['organization__company_name']
            organization_data[organization_name]['months'] = month_labels
            for month in month_labels:
                if month == month_str:
                    organization_data[organization_name]['counts'].append(entry['count'])
                else:
                    organization_data[organization_name]['counts'].append(0)

        context = {
            'org': org,
            'student_applicants': student_applicants,
            'org_count': org_count,
            'user_count': user_count,
            'organization_name': org.company_name,
            'organization_data': dict(organization_data),  # Convert defaultdict to dict for JSON serialization
            'month_labels': month_labels,  # Add month labels for x-axis consistency
        }

        return render(request, 'organization_pages/organization_dashboard.html', context)
    
    else:
        messages.error(request, 'You must log in to access the dashboard.')
        return redirect('login')


# * Ajax Functions
def send_interview_email(request, application_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id)
        student_email = application.student.email  # Ensure your Application model has a reference to the Student
        organization_name = application.organization.company_name  # Get organization name
        organization_email = application.organization.company_email  # Get organization email
        email_message = request.POST.get('emailMessage', '')

        # Prepare the email message
        message = f"""
        Dear {application.student.first_name} {application.student.last_name},

        {email_message}

        This message is from {organization_name} ({organization_email}).
        Please reach out to the organization for further queries.

        Best regards,
        PSU InternPal Team
        """

        subject = f"Interview Invitation for {application.internship.title}"
        from_email = 'psuinterpal@gmail.com'  # Fixed email sender
        recipient_list = [student_email]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            messages.success(request, "Interview invitation email sent successfully to the student.")
        except Exception as e:
            messages.error(request, f"Failed to send email: {e}")
        
        return redirect('view_application', application_id=application_id)  # Redirect back to the application view
    
    return HttpResponse("Invalid request method.", status=405)
    

def get_applications(request):
    applications = Application.objects.all()  # Fetch the applications
    data = [{
        'student_name': f"{app.student.first_name} {app.student.last_name}",
        'internship_title': app.internship.title,
        'course': app.student.course,
        'college': app.student.college,
        'applied_on': app.applied_at.strftime("%B %d, %Y"),
        'application_id': app.id,
    } for app in applications]

    return JsonResponse(data, safe=False)


# * Admin Dashboard
@login_required(login_url='login')
def admin_dashboard(request):
    # Check if the logged-in user is an admin
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')  # Redirect to login or another page if not an admin

    # Fetch data for statistics
    total_users = CustomUser.objects.filter(is_active=True).count()  # Count active users
    total_organizations = Organization.objects.count()  # Count total organizations
    total_internships = Internship.objects.count()  # Count confirmed internships

    # Fetch data for tables
    users = CustomUser.objects.all()
    organizations = Organization.objects.all()

    context = {
        'total_users': total_users,
        'total_organizations': total_organizations,
        'total_internships': total_internships,
        'users': users,
        'organizations': organizations,
    }

    return render(request, 'admin_folder/admin_dashboard.html', context)


def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.is_admin:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid login credentials or not an admin.')

    return render(request, 'admin_folder/admin_login.html')
@login_required(login_url='login')
def admin_view_student(request, id):
    student = get_object_or_404(CustomUser, id=id)
    return render(request, 'admin_folder/admin_view.html', {'student': student})

# Edit student details
@login_required(login_url='login')
def admin_edit_student(request, id):
    student = get_object_or_404(CustomUser, id=id)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student details updated successfully.')
            return redirect('admin_dashboard')
    else:
        form = CustomUserCreationForm(instance=student)
    
    return render(request, 'admin_folder/admin_edit.html', {'form': form, 'student': student})

# Delete student
@login_required(login_url='login')
def admin_delete_student(request, id):
    student = get_object_or_404(CustomUser, id=id)
    student.delete()
    messages.success(request, 'Student deleted successfully.')
    return redirect('admin_dashboard')


# View organization details
@login_required(login_url='login')
def admin_view_organization(request, id):
    organization = get_object_or_404(Organization, id=id)
    return render(request, 'admin_folder/admin_view_organization.html', {'organization': organization})

# Edit organization details
@login_required(login_url='login')
def admin_edit_organization(request, id):
    organization = get_object_or_404(Organization, id=id)
    
    if request.method == 'POST':
        form = Organization(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organization details updated successfully.')
            return redirect('admin_dashboard')
    else:
        form = Organization(instance=organization)
    
    return render(request, 'admin_edit_organization.html', {'form': form, 'organization': organization})

# Delete organization
@login_required(login_url='login')
def admin_delete_organization(request, id):
    organization = get_object_or_404(Organization, id=id)
    organization.delete()
    messages.success(request, 'Organization deleted successfully.')
    return redirect('admin_dashboard')



# Admin Contents

@login_required(login_url='login')
def admin_base(request):
    return render(request, 'admin_folder/admin_dashboard.html')

@login_required(login_url='login')
def admin_departments(request):
    organizations = Organization.objects.all()  # Fetch all organizations
    return render(request, 'admin_folder/admin_departments.html', {'organizations': organizations})

@login_required(login_url='login')
def admin_advisors(request):
    return render(request, 'admin_folder/admin_advisors.html')

@login_required(login_url='login')
# Internship Dates View
def admin_internship_dates(request):
    return render(request, 'admin_folder/admin_internship_dates.html')

@login_required(login_url='login')
def admin_account_approve(request):
    pending_accounts = AccountApproval.objects.filter(is_approved=False)
    
    if request.method == 'POST':
        # Handle approve/decline action
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        # Get the AccountApproval instance for the given user
        try:
            account = AccountApproval.objects.get(user_id=user_id)
            if action == 'approve':
                account.is_approved = True
                account.save()
                return redirect('approve_list')  # Redirect to approved list
            elif action == 'decline':
                account.is_approved = False
                account.save()
                return redirect('decline_list')  # Redirect to declined list
        except AccountApproval.DoesNotExist:
            # Handle case where account does not exist
            messages.error(request, "Account not found.")
    
    # Render the admin approval template with pending accounts
    return render(request, 'admin_folder/approve_account/admin_account_approval.html', {
        'pending_accounts': pending_accounts
    })


@login_required(login_url='login')
def approve_list(request):
    approved_accounts = AccountApproval.objects.filter(is_approved=True)
    return render(request, 'admin_folder/approve_account/approve_list.html', {
        'approved_accounts': approved_accounts
    })


@login_required(login_url='login')
def decline_list(request):
    declined_accounts = AccountApproval.objects.filter(is_approved=False)
    return render(request, 'admin_folder/approve_account/decline_list.html', {
        'declined_accounts': declined_accounts
    })




@login_required(login_url='login')
def admin_account_decline(request):
    return render(request, 'admin_folder/admin_account_decline.html')

# Intern Transactions View
@login_required(login_url='login')
def admin_intern_transactions(request):
    return render(request, 'admin_folder/admin_intern_transactions.html')

# Internship Procedures Views
@login_required(login_url='login')
def admin_view_internship(request):
    return render(request, 'admin_folder/admin_view_internship.html')

@login_required(login_url='login')
def admin_confirm_internship(request):
    return render(request, 'admin_folder/admin_confirm_internship.html')


def admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.is_admin:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid login credentials or not an admin.')

    return render(request, 'admin_folder/admin_login.html')

def internship_procedures_view(request):
    return render(request, 'admin_folder/admin_internship_procedures.html')


# # Example for deleting a user
# def delete_user(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     user.delete()
#     return redirect('dashboard')

# # Example for viewing user details
# def view_user_details(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     return render(request, 'admin_folder/view_user_details.html', {'user': user})

# # Example for editing a user
# def edit_user(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     if request.method == 'POST':
#         # Update user details
#         user.first_name = request.POST['first_name']
#         user.last_name = request.POST['last_name']
#         user.save()
#         return redirect('dashboard')
#     return render(request, 'admin_folder/edit_user.html', {'user': user})