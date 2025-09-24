from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Main dashboard
    path('', views.course_management_dashboard, name='dashboard'),
    
    # Course management
    path('courses/', views.course_list_view, name='course_list'),
    path('courses/create/', views.course_create_view, name='course_create'),
    path('courses/<int:course_id>/', views.course_detail_view, name='course_detail'),
    
    # Curriculum management
    path('curricula/', views.curriculum_list_view, name='curriculum_list'),
    path('curricula/<int:curriculum_id>/', views.curriculum_detail_view, name='curriculum_detail'),
    
    # Course offerings
    path('offerings/', views.course_offering_list_view, name='course_offerings'),
    path('offerings/create/', views.create_course_offering_view, name='create_offering'),
    path('offerings/<int:offering_id>/', views.offering_detail_view, name='offering_detail'),
    path('offerings/<int:offering_id>/class-list/', views.class_list_view, name='class_list'),
    
    # Enrollment management
    path('enrollments/', views.enrollment_management_view, name='enrollment_management'),
    path('enrollments/bulk/', views.bulk_enrollment_view, name='bulk_enrollment'),
    path('enrollments/<int:enrollment_id>/approve/', views.approve_enrollment_view, name='approve_enrollment'),
    path('enrollments/export/', views.export_enrollments_csv, name='export_enrollments'),
    
    # Student enrollment
    path('my-enrollment/', views.student_enrollment_view, name='student_enrollment'),
    path('enroll/<int:offering_id>/', views.enroll_in_course_view, name='enroll_in_course'),
    path('offerings/<int:offering_id>/details/', views.course_offering_details_view, name='offering_details'),
    path('enrollments/<int:enrollment_id>/cancel/', views.cancel_enrollment_view, name='cancel_enrollment'),
    
    # Enrollment codes
    path('use-enrollment-code/', views.use_enrollment_code_view, name='use_enrollment_code'),
    path('manage-enrollment-codes/', views.manage_enrollment_codes_view, name='manage_enrollment_codes'),
]
