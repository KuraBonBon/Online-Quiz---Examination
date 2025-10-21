from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Assessment selection and creation
    path('create/', views.assessment_selection_view, name='assessment_selection'),
    path('create/<str:assessment_type>/', views.create_assessment_view, name='create_assessment'),
    path('<int:assessment_id>/add-question/', views.add_question_view, name='add_question'),
    path('<int:assessment_id>/questions/', views.manage_questions_view, name='manage_questions'),
    path('question/<int:question_id>/edit/', views.edit_question_view, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question_view, name='delete_question'),
    
    # Assessment management
    path('my-assessments/', views.my_assessments_view, name='my_assessments'),
    path('<int:assessment_id>/', views.assessment_detail_view, name='assessment_detail'),
    path('<int:assessment_id>/edit/', views.edit_assessment_view, name='edit_assessment'),
    path('<int:assessment_id>/publish/', views.publish_assessment_view, name='publish_assessment'),
    path('<int:assessment_id>/delete/', views.delete_assessment_view, name='delete_assessment'),
    
    # Student views
    path('available/', views.available_assessments_view, name='available_assessments'),
    path('<int:assessment_id>/take/', views.take_assessment_view, name='take_assessment'),
    path('<int:assessment_id>/submit/', views.submit_assessment_view, name='submit_assessment'),
    # path('results/<int:attempt_id>/', views.assessment_results_view, name='assessment_results'), # Removed - replaced with assessment_result_view
    
    # Security AJAX endpoints
    path('<int:assessment_id>/track-violation/', views.track_violation_view, name='track_violation'),
    path('<int:assessment_id>/save-progress/', views.save_progress_view, name='save_progress'),
    path('result/<int:attempt_id>/', views.assessment_result_view, name='assessment_result'),
    
    # Teacher grading
    path('grade/<int:attempt_id>/', views.grade_assessment_view, name='grade_assessment'),
    path('<int:assessment_id>/export-grades/', views.export_grades_view, name='export_grades'),
    
    # Admin and additional management URLs
    path('available/', views.available_assessments_view, name='available_assessments'),
    path('<int:assessment_id>/results/', views.assessment_results_view, name='assessment_results'),
    path('<int:assessment_id>/view/', views.view_assessment_view, name='view_assessment'),
    path('grading-queue/', views.grading_queue_view, name='grading_queue'),
    path('admin/', views.admin_assessments_view, name='admin_assessments'),
]
