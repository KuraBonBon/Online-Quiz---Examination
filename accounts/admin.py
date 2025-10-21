from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from .models import User, StudentProfile, TeacherProfile
from .models_calendar import CalendarEvent, EventCategory, UserCalendarSettings

class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active')
    list_filter = ('user_type', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'is_verified')
        }),
    )

class StudentProfileAdmin(admin.ModelAdmin):
    """Admin for StudentProfile model"""
    list_display = ('user', 'student_id', 'course', 'year_level', 'date_enrolled')
    list_filter = ('course', 'year_level', 'date_enrolled')
    search_fields = ('user__first_name', 'user__last_name', 'student_id', 'course')

class TeacherProfileAdmin(admin.ModelAdmin):
    """Admin for TeacherProfile model"""
    list_display = ('user', 'employee_id', 'department', 'specialization', 'hire_date')
    list_filter = ('department', 'hire_date')
    search_fields = ('user__first_name', 'user__last_name', 'employee_id', 'department')

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    """Admin for EventCategory model"""
    list_display = ('name', 'color', 'icon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Display Settings', {
            'fields': ('color', 'icon')
        }),
    )

@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    """Admin for CalendarEvent model"""
    list_display = ('title', 'start_date', 'end_date', 'category', 'priority', 'event_type', 'created_by', 'created_at')
    list_filter = ('category', 'priority', 'event_type', 'start_date', 'created_at', 'audience', 'is_published')
    search_fields = ('title', 'description', 'location', 'created_by__first_name', 'created_by__last_name')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'category', 'priority', 'event_type')
        }),
        ('Date & Time', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time', 'is_all_day')
        }),
        ('Location & Links', {
            'fields': ('location', 'meeting_link', 'linked_assessment')
        }),
        ('Audience', {
            'fields': ('audience', 'specific_courses', 'specific_year_levels')
        }),
        ('Settings', {
            'fields': ('is_published', 'send_notifications', 'notification_days', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('created_by', 'linked_assessment')
    filter_horizontal = ('specific_courses',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new event
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see events they created or events visible to them
            if hasattr(request.user, 'user_type'):
                if request.user.user_type == 'teacher':
                    return qs.filter(
                        models.Q(created_by=request.user) |
                        models.Q(audience_all=True) |
                        models.Q(audience_teachers=True)
                    )
                elif request.user.user_type == 'student':
                    return qs.filter(
                        models.Q(created_by=request.user) |
                        models.Q(audience_all=True) |
                        models.Q(audience_students=True)
                    )
        return qs

@admin.register(UserCalendarSettings)
class UserCalendarSettingsAdmin(admin.ModelAdmin):
    """Admin for UserCalendarSettings model"""
    list_display = ('user', 'default_view', 'show_weekends', 'email_notifications', 'browser_notifications')
    list_filter = ('default_view', 'show_weekends', 'email_notifications', 'browser_notifications')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('View Preferences', {
            'fields': ('default_view', 'show_weekends', 'start_week_on_monday', 'show_event_details')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'browser_notifications', 'notification_time')
        }),
        ('Category Filters', {
            'fields': ('hidden_categories',)
        }),
    )
    
    filter_horizontal = ('hidden_categories',)
    raw_id_fields = ('user',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)

# Customize admin site header
admin.site.site_header = "SPIST School Management System"
admin.site.site_title = "SPIST Admin"
admin.site.index_title = "School Administration Dashboard"
