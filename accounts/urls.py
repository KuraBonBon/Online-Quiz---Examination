from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from . import views_profile
from . import views_calendar

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('', views.home_view, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('student/register/', views.student_register_view, name='student_register'),
    path('teacher/register/', views.teacher_register_view, name='teacher_register'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Admin Management URLs (placeholder views)
    path('admin/users/', views.user_management_view, name='user_management'),
    
    # Profile URLs
    path('profile/', views_profile.profile_view, name='profile'),
    path('profile/edit/', views_profile.profile_edit_view, name='profile_edit'),
    path('profile/settings/', views_profile.settings_view, name='settings'),
    path('profile/security/', views_profile.security_view, name='security'),
    path('profile/activity/', views_profile.activity_log_view, name='activity_log'),
    path('profile/change-password/', views_profile.change_password_view, name='change_password'),
    path('profile/avatar/upload/', views_profile.avatar_upload_view, name='avatar_upload'),
    path('profile/avatar/remove/', views_profile.remove_avatar_view, name='remove_avatar'),
    path('profile/deactivate/', views_profile.deactivate_account_view, name='deactivate_account'),
    path('profile/export-data/', views_profile.export_data_view, name='export_data'),
    
    # Calendar URLs
    path('calendar/', views_calendar.calendar_view, name='calendar_view'),
    path('calendar/create/', views_calendar.create_event, name='create_event'),
    path('calendar/event/<int:pk>/', views_calendar.event_detail, name='event_detail'),
    path('calendar/event/<int:pk>/edit/', views_calendar.edit_event, name='edit_event'),
    path('calendar/event/<int:pk>/delete/', views_calendar.delete_event, name='delete_event'),
    path('calendar/api/events/', views_calendar.calendar_api, name='events_api'),
    path('calendar/settings/', views_calendar.calendar_settings, name='calendar_settings'),
]
