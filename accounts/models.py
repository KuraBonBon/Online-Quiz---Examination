from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import os

def user_avatar_path(instance, filename):
    """Generate file path for user avatars"""
    return f'avatars/{instance.user_type}/{instance.id}/{filename}'

class User(AbstractUser):
    """Custom user model with enhanced profile features"""
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    # Enhanced profile fields
    bio = models.TextField(max_length=500, blank=True, null=True, help_text="Tell us about yourself")
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True, help_text="Profile picture")
    date_updated = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    is_active_user = models.BooleanField(default=True, help_text="For soft delete")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_type})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_avatar_url(self):
        """Return avatar URL or use default"""
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except:
                pass
        # Return None to use CSS-generated avatar in template
        return None
    
    def get_avatar_initials(self):
        """Get user initials for avatar"""
        first_initial = self.first_name[0].upper() if self.first_name else ""
        last_initial = self.last_name[0].upper() if self.last_name else ""
        return f"{first_initial}{last_initial}" or "U"

class StudentProfile(models.Model):
    """Extended profile for students"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    course = models.CharField(max_length=100)
    year_level = models.CharField(max_length=20, choices=[
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('Graduate', 'Graduate'),
    ])
    date_enrolled = models.DateField(auto_now_add=True)
    
    # Additional student fields
    gpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.student_id}"

class TeacherProfile(models.Model):
    """Extended profile for teachers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    hire_date = models.DateField(auto_now_add=True)
    
    # Additional teacher fields
    office_room = models.CharField(max_length=50, blank=True, null=True)
    office_hours = models.CharField(max_length=200, blank=True, null=True)
    education_background = models.TextField(blank=True, null=True)
    research_interests = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.department}"

class UserSettings(models.Model):
    """User preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Theme preferences
    THEME_CHOICES = [
        ('auto', 'Auto (System)'),
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
    ]
    theme_preference = models.CharField(max_length=20, choices=THEME_CHOICES, default='auto')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    assignment_reminders = models.BooleanField(default=True)
    grade_notifications = models.BooleanField(default=True)
    course_updates = models.BooleanField(default=True)
    
    # Privacy settings
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('students_only', 'Students Only'),
        ('teachers_only', 'Teachers Only'),
        ('private', 'Private')
    ]
    profile_visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='students_only')
    show_email = models.BooleanField(default=False)
    show_phone = models.BooleanField(default=False)
    
    # Language and locale
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fil', 'Filipino'),
    ]
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    timezone = models.CharField(max_length=50, default='Asia/Manila')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"
    
    def __str__(self):
        return f"Settings for {self.user.get_full_name()}"

class UserActivityLog(models.Model):
    """Track user activities for security and analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action} at {self.timestamp}"
