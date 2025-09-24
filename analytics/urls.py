from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('students/', views.student_analytics, name='student_analytics'),
    path('teachers/', views.teacher_analytics, name='teacher_analytics'),
    path('assessments/', views.assessment_analytics, name='assessment_analytics'),
    path('system/', views.system_analytics, name='system_analytics'),
    path('export/', views.export_analytics, name='export_analytics'),
]
