from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import os

from .models import User, UserSettings, UserActivityLog
from .forms_profile import (
    StudentProfileUpdateForm, TeacherProfileUpdateForm, CustomPasswordChangeForm,
    NotificationSettingsForm, PrivacySettingsForm, AvatarUploadForm, AccountDeactivationForm
)

def log_user_activity(user, action, request):
    """Helper function to log user activities"""
    UserActivityLog.objects.create(
        user=user,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

@login_required
def profile_view(request):
    """Main profile view"""
    user = request.user
    
    # Get or create user settings
    settings_obj, created = UserSettings.objects.get_or_create(user=user)
    
    # Get recent activity logs (last 10)
    recent_activities = UserActivityLog.objects.filter(user=user)[:10]
    
    context = {
        'user': user,
        'settings': settings_obj,
        'recent_activities': recent_activities,
    }
    
    # Add profile-specific data based on user type
    if user.user_type == 'student':
        context['profile'] = getattr(user, 'student_profile', None)
    elif user.user_type == 'teacher':
        context['profile'] = getattr(user, 'teacher_profile', None)
    
    return render(request, 'accounts/profile/profile_main.html', context)

@login_required
def profile_edit_view(request):
    """Edit profile information"""
    user = request.user
    
    if request.method == 'POST':
        if user.user_type == 'student':
            form = StudentProfileUpdateForm(request.POST, instance=user, user=user)
        else:
            form = TeacherProfileUpdateForm(request.POST, instance=user, user=user)
        
        if form.is_valid():
            form.save()
            log_user_activity(user, 'Profile updated', request)
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        if user.user_type == 'student':
            form = StudentProfileUpdateForm(instance=user, user=user)
        else:
            form = TeacherProfileUpdateForm(instance=user, user=user)
    
    context = {'form': form, 'user_type': user.user_type}
    return render(request, 'accounts/profile/profile_edit.html', context)

@login_required
def change_password_view(request):
    """Change user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            log_user_activity(user, 'Password changed', request)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/profile/change_password.html', {'form': form})

@login_required
def avatar_upload_view(request):
    """Handle avatar upload"""
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES)
        if form.is_valid():
            avatar = form.cleaned_data['avatar']
            if avatar:
                # Delete old avatar if exists
                if request.user.avatar:
                    old_avatar_path = request.user.avatar.path
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)
                
                # Save new avatar
                request.user.avatar = avatar
                request.user.save()
                log_user_activity(request.user, 'Profile picture updated', request)
                messages.success(request, 'Profile picture updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please select a valid image file.')
    
    return redirect('accounts:profile')

@login_required
@require_http_methods(["POST"])
def remove_avatar_view(request):
    """Remove user avatar"""
    user = request.user
    if user.avatar:
        # Delete avatar file
        avatar_path = user.avatar.path
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        
        # Clear avatar field
        user.avatar = None
        user.save()
        log_user_activity(user, 'Profile picture removed', request)
        messages.success(request, 'Profile picture removed successfully!')
    
    return redirect('accounts:profile')

@login_required
def settings_view(request):
    """User settings and preferences"""
    user = request.user
    settings_obj, created = UserSettings.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'notifications':
            form = NotificationSettingsForm(request.POST)
            if form.is_valid():
                settings_obj.email_notifications = form.cleaned_data['email_notifications']
                settings_obj.assignment_reminders = form.cleaned_data['assignment_reminders']
                settings_obj.grade_notifications = form.cleaned_data['grade_notifications']
                settings_obj.course_updates = form.cleaned_data['course_updates']
                settings_obj.save()
                log_user_activity(user, 'Notification settings updated', request)
                messages.success(request, 'Notification settings updated!')
        
        elif action == 'privacy':
            form = PrivacySettingsForm(request.POST)
            if form.is_valid():
                settings_obj.profile_visibility = form.cleaned_data['profile_visibility']
                settings_obj.show_email = form.cleaned_data['show_email']
                settings_obj.show_phone = form.cleaned_data['show_phone']
                settings_obj.save()
                log_user_activity(user, 'Privacy settings updated', request)
                messages.success(request, 'Privacy settings updated!')
        
        elif action == 'theme':
            theme = request.POST.get('theme_preference')
            if theme in ['auto', 'light', 'dark']:
                settings_obj.theme_preference = theme
                settings_obj.save()
                log_user_activity(user, f'Theme changed to {theme}', request)
                messages.success(request, 'Theme preference updated!')
        
        return redirect('accounts:settings')
    
    # Initialize forms with current settings
    notification_form = NotificationSettingsForm(initial={
        'email_notifications': settings_obj.email_notifications,
        'assignment_reminders': settings_obj.assignment_reminders,
        'grade_notifications': settings_obj.grade_notifications,
        'course_updates': settings_obj.course_updates,
    })
    
    privacy_form = PrivacySettingsForm(initial={
        'profile_visibility': settings_obj.profile_visibility,
        'show_email': settings_obj.show_email,
        'show_phone': settings_obj.show_phone,
    })
    
    context = {
        'settings': settings_obj,
        'notification_form': notification_form,
        'privacy_form': privacy_form,
    }
    
    return render(request, 'accounts/profile/settings.html', context)

@login_required
def activity_log_view(request):
    """View user activity history"""
    activities = UserActivityLog.objects.filter(user=request.user)
    
    # Pagination could be added here for large activity logs
    context = {'activities': activities[:50]}  # Show last 50 activities
    
    return render(request, 'accounts/profile/activity_log.html', context)

@login_required
def security_view(request):
    """Security settings and two-factor authentication setup"""
    user = request.user
    
    # Get login history (last 10 logins)
    login_activities = UserActivityLog.objects.filter(
        user=user, 
        action__icontains='login'
    )[:10]
    
    context = {
        'login_activities': login_activities,
        'last_login': user.last_login,
    }
    
    return render(request, 'accounts/profile/security.html', context)

@login_required
def deactivate_account_view(request):
    """Account deactivation (soft delete)"""
    if request.method == 'POST':
        form = AccountDeactivationForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm_deactivation']:
            user = request.user
            user.is_active_user = False
            user.is_active = False
            user.save()
            
            log_user_activity(user, f'Account deactivated. Reason: {form.cleaned_data.get("reason", "None")}', request)
            messages.success(request, 'Your account has been deactivated. Contact admin to reactivate.')
            
            from django.contrib.auth import logout
            logout(request)
            return redirect('home')
    else:
        form = AccountDeactivationForm()
    
    return render(request, 'accounts/profile/deactivate_account.html', {'form': form})

@login_required
def export_data_view(request):
    """Export user data (GDPR compliance)"""
    user = request.user
    
    # Collect user data
    user_data = {
        'personal_info': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
            'bio': user.bio,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'settings': {},
        'activities': []
    }
    
    # Add profile-specific data
    if hasattr(user, 'student_profile'):
        profile = user.student_profile
        user_data['profile'] = {
            'student_id': profile.student_id,
            'course': profile.course,
            'year_level': profile.year_level,
            'date_enrolled': profile.date_enrolled.isoformat(),
        }
    elif hasattr(user, 'teacher_profile'):
        profile = user.teacher_profile
        user_data['profile'] = {
            'employee_id': profile.employee_id,
            'department': profile.department,
            'specialization': profile.specialization,
            'hire_date': profile.hire_date.isoformat(),
        }
    
    # Add settings
    if hasattr(user, 'settings'):
        settings_obj = user.settings
        user_data['settings'] = {
            'theme_preference': settings_obj.theme_preference,
            'email_notifications': settings_obj.email_notifications,
            'profile_visibility': settings_obj.profile_visibility,
        }
    
    # Add recent activities
    activities = UserActivityLog.objects.filter(user=user)[:100]
    user_data['activities'] = [
        {
            'action': activity.action,
            'timestamp': activity.timestamp.isoformat(),
            'ip_address': activity.ip_address,
        } for activity in activities
    ]
    
    log_user_activity(user, 'Data export requested', request)
    
    # Return as JSON download
    response = JsonResponse(user_data, indent=2)
    response['Content-Disposition'] = f'attachment; filename="spist_user_data_{user.id}.json"'
    return response
