from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .models import UserVisit, CustomUser 
from django.http import JsonResponse
import random

User = CustomUser  # Reference your CustomUser model

def request_form(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            token = get_random_string(length=32)
            user.reset_token = token
            user.reset_otp = random.randint(100000, 999999)  # Generate OTP
            user.save()

            send_mail(
                'Password Reset Request',
                f'Dear {user.email},\n\nDid you request a reset password? If not, ignore this email. If yes, please use the following OTP: {user.reset_otp}',
                'your_email@example.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, f"A password reset link has been sent to {email}. Please check your inbox.")
            return redirect('otp_verify', token=token)  # Redirect to OTP confirmation

        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            
    return render(request, 'registration/reset_password_form.html')  # Updated path



# Check if the email confirmation link has been clicked (used by the waiting area for real-time updates)
def check_confirmation_status(request, token):
    try:
        # Check if the token exists and if it has been cleared
        user = CustomUser.objects.get(reset_token=token)
        if user.reset_token == '':
            return JsonResponse({'confirmed': True})
        return JsonResponse({'confirmed': False})
    except CustomUser.DoesNotExist:
        # Token is invalid or doesn't exist
        return JsonResponse({'confirmed': False})

def index(request):
    return render(request, 'index.html')


@login_required(login_url='login')
def home(request):
    # Count the number of registered users
    user_count = CustomUser.objects.count()
    context = {
        'user_count': user_count,
    }
    return render(request, 'home.html', context)


def admin_2(request):
    return render(request, 'admin2.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()  # Save the new user

            # Increment the user count
            visit, created = UserVisit.objects.get_or_create(id=1)
            visit.count += 1
            visit.save()

            # Authenticate and log in the user
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            messages.success(request, f'Account created for {email}')
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
    return render(request, 'registration/login.html')  # Updated path


# User Logout
def user_logout(request):
    logout(request)
    return redirect('index')


# Admin view to list all users
def admin_users(request):
    users = CustomUser.objects.all()
    return render(request, 'admin_view.html', {'users': users})


# Delete user and decrement the user count
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()

    # Check the user count after deletion
    user_count = CustomUser.objects.count()

    messages.success(request, f'User {user.email} deleted successfully.')
    return redirect('admin_view')  # Redirect to the admin view or wherever appropriate

def reset_password_confirm(request, token):
    try:
        user = CustomUser.objects.get(reset_token=token)
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if new_password == confirm_password:
                user.set_password(new_password)
                user.reset_token = ''  # Clear the reset token after successful password change
                user.reset_otp = None  # Ensure OTP is cleared
                user.save()
                messages.success(request, 'Your password has been successfully changed!')
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')

        return render(request, 'registration/reset_password_confirm.html', {'token': token})

    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid reset token.')
        return redirect('request_password_reset')


def otp_verify(request, token):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        try:
            user = CustomUser.objects.get(reset_token=token)
            if str(user.reset_otp) == entered_otp:  # Validate OTP
                return redirect('reset_password_confirm', token=token)  # If OTP is correct, redirect to reset password page
            else:
                messages.error(request, 'Invalid OTP entered. Please try again.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid reset token.')

    return render(request, 'registration/otp_confirmation.html', {'token': token})