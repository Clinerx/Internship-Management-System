from django.urls import path
from . import views 

urlpatterns = [
    path('', views.index, name='index'),  # Create a simple home view
    
    path('student_register/', views.student_register, name='student_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('index', views.index, name='index'),
    path('admin_view/', views.admin_users, name='admin_view'),  # Admin view for listing users
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),  # Delete user URL
    path('admin/delete_organization/<int:organization_id>/', views.delete_organization, name='delete_organization'),
    path('admin', views.admin, name='admin'),
    # Correct name for forgot password link
    path('forgot-password/', views.request_form, name='request_password_reset'),
    path('check-confirmation-status/<str:token>/', views.check_confirmation_status, name='check_confirmation_status'),
    path('reset-password/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    path('otp-verify/<str:token>/', views.otp_verify, name='otp_verify'),
    path('intial_registration', views.initial_registration, name='initial_registration'),
    # path('org_details', views.org_details, name='org_details'),  
    path('organization_details', views.organization_registration, name='organization_details'),
    path('success/', views.success_view, name='success'),  # Add this line if not already present
    
    path('organization_dashboard/', views.org_dashboard, name='organization_dashboard'),
    path('organization_post/', views.organization_post, name='organization_post'),
    path('organization_interns/', views.organization_interns, name='organization_interns'),
    path('organization_applicant/', views.organization_applicant, name='organization_applicant'),
    path('about_us_org/', views.about_us_org, name='about_us_org'),
    
    
    path('home', views.home, name='home'),
    path('student_internships/', views.student_internships, name='student_internships'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student_status/', views.student_status, name='student_status'),
    path('about_us/', views.about_us, name='about_us'),
]