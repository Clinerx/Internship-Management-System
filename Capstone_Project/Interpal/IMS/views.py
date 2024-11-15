import random
from functools import wraps
from random import randint

from django.views.decorators.cache import cache_control
from django.db.models.functions import TruncMonth
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
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils.crypto import get_random_string

from collections import defaultdict

from .forms import CustomUserCreationForm, InternshipForm, ProfileForm
from .models import CustomUser, Internship, Organization, UserVisit, Application



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
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the user
            user = form.save()

            # Upload profile picture to Cloudinary if available
            profile_picture = form.cleaned_data.get('profile_picture')
            if profile_picture:
                upload_result = cloudinary.uploader.upload(profile_picture, folder="student_profiles/")
                user.profile.image_url = upload_result.get('secure_url')
                user.profile.save()

            # Increment visit count
            visit, created = UserVisit.objects.get_or_create(id=1)
            visit.count += 1
            visit.save()

            # Authenticate and log the user in
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            messages.success(request, f'Account created for {email}')
            return redirect('login')
        else:
            messages.error(request, 'There was an error with your registration. Please try again.')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'student_registration_folder/student_profile_details.html', {'form': form})

def student_login(request):
    # Check if a user is already authenticated
    if request.user.is_authenticated:
        email = request.GET.get('email')
        if email and email != request.user.email:
            logout(request)
        else:
            return redirect('student_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        try:
            user = CustomUser.objects.get(email=email)
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful! Redirecting to your dashboard...')
                return render(request, 'reset_folder/student_login.html', {'email': email, 'redirect': True})
            else:
                messages.error(request, 'Invalid email or password for student account.')

        except CustomUser.DoesNotExist:
            messages.error(request, 'No student account found with this email.')

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
    return redirect('login')

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

    # Recommended internships logic
    user_applications = Application.objects.filter(student=request.user)
    applied_internship_ids = user_applications.values_list('internship_id', flat=True)

    # Example filter: recommend internships that the student hasn't applied to
    recommended_internships = Internship.objects.exclude(id__in=applied_internship_ids).order_by('-created_at')[:5]

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
        'recommended_internships': recommended_internships,  # Pass to the context
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



# * <<<<<<<============================================>>>> 
# ^ Student Status Content


@login_required(login_url='login')
def internship_apply(request, internship_id):
    internship = get_object_or_404(Internship, id=internship_id)

    # Check if the student already applied
    already_applied = Application.objects.filter(internship=internship, student=request.user).exists()

    # Check available slots before allowing application
    if internship.max_applicants > 0 and not already_applied:
        if request.method == 'POST':
            Application.objects.create(
                internship=internship,
                organization=internship.organization,
                student=request.user,
            )
            # Decrease max_applicants by 1
            internship.max_applicants -= 1
            internship.save()

            # Set session flag to show notification and redirect
            request.session['application_submitted'] = True
            return redirect('student_internships')
    elif already_applied:
        messages.info(request, "You have already applied for this internship.")
    else:
        messages.warning(request, "No available slots for this internship.")

    context = {
        'internship': internship,
        'already_applied': already_applied
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


# Student view to display the current status of their application
def view_status(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    # Determine completed stages up to the current status
    stages = ["Pending", "In Review", "Interview Scheduled", "Offer Extended", "Completed"]
    completed_stages = stages[:stages.index(application.status) + 1]
    
    status_details = {
        "status": application.status,
        "review_stage": application.review_stage,
        "submission_date": application.applied_at,
        "comments": application.comments,
        "completed_stages": completed_stages
    }
    
    context = {
        'application': application,
        'status_details': status_details,
        'stages': stages
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

@organization_login_required
def organization_post(request):
    # Check if 'organization_id' is in session
    organization_id = request.session.get('organization_id')
    if not organization_id:
        messages.error(request, "No organization is currently logged in.")
        return redirect('login')  # Redirect to login or an appropriate page

    # Fetch the organization object
    organization = Organization.objects.get(id=organization_id)
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
    # Check if 'organization_id' is in session
    organization_id = request.session.get('organization_id')
    if not organization_id:
        messages.error(request, "No organization is currently logged in.")
        return redirect('login')

    # Fetch organization and related users
    users = CustomUser.objects.all()
    org = Organization.objects.get(id=organization_id)

    context = {
        'users': users,
        'org': org,
    }
    return render(request, 'organization_pages/organization_interns.html', context)

# * ================ Application =========================

@organization_login_required
def organization_applicant(request):
    # Retrieve the organization either from the session or the logged-in user
    org = None
    if 'organization_id' in request.session:
        org = get_object_or_404(Organization, id=request.session['organization_id'])
    elif hasattr(request.user, 'organization'):
        org = request.user.organization
    
    if not org:
        # Redirect or handle error if organization cannot be determined
        return redirect('some_error_page')

    # Fetch applications related to this organization, grouped by internship
    applications = Application.objects.filter(internship__organization=org).select_related('internship', 'student')
    
    # Group applications by internship
    grouped_applications = {}
    for application in applications:
        if application.internship not in grouped_applications:
            grouped_applications[application.internship] = []
        grouped_applications[application.internship].append(application)

    context = {
        'grouped_applications': grouped_applications,
        'org': org,
    }
    return render(request, 'organization_pages/organization_applicants.html', context)

@organization_login_required
def view_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, organization_id=request.session['organization_id'])

    # Define the stages for the application process
    stages = ["Applied", "In Review", "Interview Scheduled", "Offer Extended", "Completed"]
    completed_stages = stages[:stages.index(application.status) + 1]

    if request.method == "POST":
        # Get the selected status from the form
        new_status = request.POST.get("status")
        if new_status in stages:
            # Update the application status and save it
            application.status = new_status
            application.save()
            messages.success(request, "Application status updated successfully.")
            return redirect(reverse('view_application', args=[application_id]))

    # Prepare context data for rendering
    context = {
        'application': application,
        'stages': stages,
        'completed_stages': completed_stages,
    }
    return render(request, 'organization_pages/view_application.html', context)

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
def admin_dashboard(request):
    # Check if the logged-in user is an admin
    if not request.user.is_admin:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('login')  # Redirect to login or another page if not an admin

    # Fetch all students and organizations
    users = CustomUser.objects.all()
    organizations = Organization.objects.all()

    context = {
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