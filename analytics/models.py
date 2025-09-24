from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg, Sum, Count, Q
import json

User = get_user_model()

class SystemMetric(models.Model):
    """Track system-wide metrics"""
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} at {self.timestamp}"

class PerformanceMetric(models.Model):
    """Track performance metrics for users, courses, assessments"""
    METRIC_TYPES = [
        ('user', 'User Performance'),
        ('course', 'Course Performance'),
        ('assessment', 'Assessment Performance'),
        ('system', 'System Performance'),
    ]
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    object_id = models.PositiveIntegerField(null=True, blank=True)  # Generic reference
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    additional_data = models.JSONField(default=dict, blank=True)
    
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['metric_type', 'object_id']),
            models.Index(fields=['user', 'metric_name']),
        ]
    
    def __str__(self):
        return f"{self.metric_type}: {self.metric_name} = {self.metric_value}"

class UserActivityLog(models.Model):
    """Track user activities for analytics"""
    ACTION_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('assessment_create', 'Assessment Created'),
        ('assessment_start', 'Assessment Started'),
        ('assessment_complete', 'Assessment Completed'),
        ('question_add', 'Question Added'),
        ('course_enroll', 'Course Enrollment'),
        ('grade_view', 'Grade Viewed'),
        ('profile_update', 'Profile Updated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()}"

class AnalyticsReport(models.Model):
    """Store generated analytics reports"""
    REPORT_TYPES = [
        ('student_performance', 'Student Performance Report'),
        ('teacher_activity', 'Teacher Activity Report'),
        ('assessment_statistics', 'Assessment Statistics'),
        ('course_enrollment', 'Course Enrollment Report'),
        ('system_usage', 'System Usage Report'),
        ('grade_distribution', 'Grade Distribution Report'),
    ]
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    report_data = models.JSONField()
    
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.generated_at.strftime('%Y-%m-%d')}"

class DashboardWidget(models.Model):
    """Custom dashboard widgets for users"""
    WIDGET_TYPES = [
        ('chart', 'Chart Widget'),
        ('metric', 'Metric Widget'),
        ('list', 'List Widget'),
        ('progress', 'Progress Widget'),
        ('calendar', 'Calendar Widget'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    configuration = models.JSONField(default=dict)
    
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(default=1)
    height = models.PositiveIntegerField(default=1)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
