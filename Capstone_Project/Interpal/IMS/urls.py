from django.urls import path
from . import views 

urlpatterns = [
    path('', views.index, name='index'),  # Create a simple home view
    path('home', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('index', views.index, name='index'),
    path('admin_view/', views.admin_users, name='admin_view'),  # Admin view for listing users
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),  # Delete user URL
    # Correct name for forgot password link
    path('forgot-password/', views.request_form, name='request_password_reset'),
    path('check-confirmation-status/<str:token>/', views.check_confirmation_status, name='check_confirmation_status'),
    path('reset-password/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    path('otp-verify/<str:token>/', views.otp_verify, name='otp_verify'),
]
