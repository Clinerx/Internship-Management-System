from django.urls import path
from . import views 

urlpatterns = [
    path('', views.index, name='index'),  # Create a simple home view
    
    path('student_register/', views.student_register, name='student_register'),
    path('login/', views.student_login, name='login'),
    path('organization_login', views.organization_login, name='organization_login'),
    path('logout/', views.user_logout, name='logout'),
    path('index', views.index, name='index'),
    path('admin_view/', views.admin_users, name='admin_view'),  # Admin view for listing users
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),  # Delete user URL
    path('admin/delete_organization/<int:organization_id>/', views.delete_organization, name='delete_organization'),
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
    path('post/edit/<int:internship_id>/', views.edit_internship, name='edit_internship'),
    path('delete_internship/<int:internship_id>/', views.delete_internship, name='delete_internship'),
    path('internship/<int:internship_id>/', views.view_internship, name='view_internship'),
    path('organization/application/<int:application_id>/update-status/', views.update_application_status, name='update_application_status'),
    path('organization/applications/<int:application_id>/view/', views.view_application, name='view_application'),
    path('organization/applications/<int:application_id>/delete/', views.delete_application, name='delete_application'), 
    path('application/<int:application_id>/status/', views.view_status, name='view_status'),
    # path('organization_applicant/', views.organization_applicant, name='organization_applicant'),
    
    path('about_us_org/', views.about_us_org, name='about_us_org'),
    path('about_us/', views.about_us, name='about_us'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    
    # * <<<<====================>>>>
    # ^ Student Dashboard
     
    path('home/', views.home, name='home'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # * <<<<====================>>>>
    # ^ Student Status
    
    path('student_status/', views.student_status, name='student_status'),
    path('delete_application/<int:application_id>/', views.delete_applications, name='delete_application_confirm'),
    path('delete_applications/', views.delete_applications, name='delete_selected_applications'),
    path('internships/view_status/<int:application_id>/', views.view_status, name='view_status'),

    
    # * <<<<====================>>>>
    # ^ Student Internship
    
    path('student_internships/', views.student_internships, name='student_internships'),
    path('student_internships/<int:internship_id>/apply/', views.internship_apply, name='internship_apply'),
    path('student_internships/<int:id>/', views.internship_detail, name='internship_detail'),
    # * <<<<====================>>>>
    
    
    # * <<<<====================>>>>
    # ^ Ajax URL
    path('get-applications/', views.get_applications, name='get_applications'),
    
    
    
    
    
    
    
    
    
    
    
    
    
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/student/<int:id>/view/', views.admin_view_student, name='admin_view_student'),
    path('admin/student/<int:id>/edit/', views.admin_edit_student, name='admin_edit_student'),
    path('admin/student/<int:id>/delete/', views.admin_delete_student, name='admin_delete_student'),
    
    
    path('admin/organization/<int:id>/view/',views.admin_view_organization, name='admin_view_organization'),
    path('admin/organization/<int:id>/edit/', views.admin_edit_organization, name='admin_edit_organization'),
    path('admin/organization/<int:id>/delete/', views.admin_delete_organization, name='admin_delete_organization'),
    
    path('base/', views.admin_base, name='admin_base'),
    path('departments/', views.admin_departments, name='admin_departments'),
    path('advisors/', views.admin_advisors, name='admin_advisors'),
    path('internship-dates/', views.admin_internship_dates, name='admin_internship_dates'),
    path('account-approve/', views.admin_account_approve, name='admin_account_approve'),
    path('account-decline/', views.admin_account_decline, name='admin_account_decline'),
    path('intern-transactions/', views.admin_intern_transactions, name='admin_intern_transactions'),
    path('view-internship/', views.admin_view_internship, name='admin_view_internship'),
    path('confirm-internship/', views.admin_confirm_internship, name='admin_confirm_internship'),
    
]