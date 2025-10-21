from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse

User = get_user_model()

class SchoolCalendar(models.Model):
    """Main calendar system for the school"""
    name = models.CharField(max_length=100, default="SPIST Academic Calendar")
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024-2025")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-academic_year']
    
    def __str__(self):
        return f"{self.name} ({self.academic_year})"

class EventCategory(models.Model):
    """Categories for different types of events"""
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#004d40", help_text="Hex color code")
    icon = models.CharField(max_length=50, default="fas fa-calendar", help_text="FontAwesome icon class")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Event Categories"
    
    def __str__(self):
        return self.name

class CalendarEvent(models.Model):
    """Individual calendar events"""
    EVENT_TYPES = (
        ('academic', 'Academic'),
        ('examination', 'Examination'),
        ('assessment', 'Assessment'),
        ('holiday', 'Holiday'),
        ('meeting', 'Meeting'),
        ('activity', 'School Activity'),
        ('deadline', 'Deadline'),
        ('other', 'Other'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    AUDIENCE_TYPES = (
        ('all', 'Everyone'),
        ('students', 'Students Only'),
        ('teachers', 'Teachers Only'),
        ('admin', 'Admin Only'),
        ('specific', 'Specific Groups'),
    )
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='other')
    
    # Date and Time
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_all_day = models.BooleanField(default=False)
    
    # Location and Details
    location = models.CharField(max_length=200, blank=True)
    meeting_link = models.URLField(blank=True, help_text="Online meeting link if applicable")
    
    # Audience and Permissions
    audience = models.CharField(max_length=20, choices=AUDIENCE_TYPES, default='all')
    specific_courses = models.ManyToManyField('courses.Course', blank=True, related_name='calendar_events')
    specific_year_levels = models.CharField(max_length=50, blank=True, help_text="Comma-separated: 1,2,3,4")
    
    # Priority and Status
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    is_published = models.BooleanField(default=True)
    is_recurring = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Assessment Integration
    linked_assessment = models.ForeignKey('assessments.Assessment', on_delete=models.CASCADE, null=True, blank=True, related_name='calendar_events')
    
    # Notifications
    send_notifications = models.BooleanField(default=True)
    notification_days = models.PositiveIntegerField(default=1, help_text="Days before event to send notification")
    
    class Meta:
        ordering = ['start_date', 'start_time']
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['event_type', 'is_published']),
            models.Index(fields=['audience', 'is_published']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    def get_absolute_url(self):
        return reverse('calendar:event_detail', kwargs={'pk': self.pk})
    
    @property
    def is_today(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now().date()
    
    @property
    def is_past(self):
        return self.end_date < timezone.now().date()
    
    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1
    
    def is_visible_to_user(self, user):
        """Check if event is visible to specific user"""
        if not self.is_published:
            return user.is_staff or user == self.created_by
        
        if self.audience == 'all':
            return True
        elif self.audience == 'students' and user.user_type == 'student':
            return True
        elif self.audience == 'teachers' and user.user_type == 'teacher':
            return True
        elif self.audience == 'admin' and (user.is_staff or user.user_type == 'admin'):
            return True
        elif self.audience == 'specific':
            # Check specific courses and year levels
            if user.user_type == 'student' and hasattr(user, 'student_profile'):
                profile = user.student_profile
                # Check year level
                if self.specific_year_levels:
                    year_levels = [level.strip() for level in self.specific_year_levels.split(',')]
                    if profile.year_level not in year_levels:
                        return False
                # Check courses (if any specified)
                if self.specific_courses.exists():
                    user_courses = profile.enrolled_courses.all() if hasattr(profile, 'enrolled_courses') else []
                    if not any(course in self.specific_courses.all() for course in user_courses):
                        return False
                return True
        
        return False

class EventReminder(models.Model):
    """Reminders for calendar events"""
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_reminders')
    reminder_date = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'user']
        ordering = ['reminder_date']
    
    def __str__(self):
        return f"Reminder: {self.event.title} for {self.user.get_full_name()}"

class UserCalendarSettings(models.Model):
    """User-specific calendar settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='calendar_settings')
    
    # View Preferences
    default_view = models.CharField(max_length=20, choices=[
        ('month', 'Month View'),
        ('week', 'Week View'),
        ('day', 'Day View'),
        ('agenda', 'Agenda View'),
    ], default='month')
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=True)
    notification_time = models.TimeField(default='09:00', help_text="Preferred time for daily notifications")
    
    # Display Preferences
    show_weekends = models.BooleanField(default=True)
    start_week_on_monday = models.BooleanField(default=True)
    show_event_details = models.BooleanField(default=True)
    
    # Hidden Categories
    hidden_categories = models.ManyToManyField(EventCategory, blank=True, related_name='hidden_by_users')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Calendar Settings for {self.user.get_full_name()}"