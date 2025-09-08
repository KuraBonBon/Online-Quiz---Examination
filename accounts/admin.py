from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile

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

admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(TeacherProfile, TeacherProfileAdmin)
