from django import forms
from django.contrib.auth import get_user_model
from .models_calendar import CalendarEvent, EventCategory, UserCalendarSettings
from assessments.models import Assessment

User = get_user_model()

class CalendarEventForm(forms.ModelForm):
    """Form for creating and editing calendar events"""
    
    class Meta:
        model = CalendarEvent
        fields = [
            'title', 'description', 'start_date', 'end_date', 
            'start_time', 'end_time', 'location', 'category',
            'priority', 'event_type', 'audience',
            'specific_courses', 'specific_year_levels',
            'linked_assessment', 'send_notifications', 'is_all_day'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter event title...',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-textarea',
                'placeholder': 'Describe the event...',
                'rows': 4
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event location...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'audience': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'specific_courses': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
            'specific_year_levels': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1,2,3,4'
            }),
            'linked_assessment': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'is_all_day': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'send_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'title': 'Event Title',
            'description': 'Description',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'start_time': 'Start Time',
            'end_time': 'End Time',
            'location': 'Location',
            'category': 'Category',
            'priority': 'Priority',
            'event_type': 'Event Type',
            'audience': 'Target Audience',
            'specific_courses': 'Specific Courses',
            'specific_year_levels': 'Year Levels',
            'linked_assessment': 'Related Assessment',
            'is_all_day': 'All Day Event',
            'send_notifications': 'Send Notification',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit related assessments based on user permissions
        if user:
            if user.user_type == 'teacher' and hasattr(user, 'teacherprofile'):
                # Teachers can link to their own assessments
                self.fields['linked_assessment'].queryset = Assessment.objects.filter(
                    course__teacher=user.teacherprofile
                )
            elif user.user_type == 'admin' or user.is_staff:
                # Admins can link to any assessment
                self.fields['linked_assessment'].queryset = Assessment.objects.all()
            else:
                # Students or users without teacher profile cannot link assessments
                self.fields['linked_assessment'].queryset = Assessment.objects.none()
                self.fields['linked_assessment'].widget = forms.HiddenInput()
        
        # Set empty label for optional fields
        self.fields['end_date'].required = False
        self.fields['linked_assessment'].required = False
        self.fields['linked_assessment'].empty_label = "No assessment"
        self.fields['specific_courses'].required = False
        self.fields['specific_year_levels'].required = False
        
        # Make certain fields required
        self.fields['title'].required = True
        self.fields['start_date'].required = True
        self.fields['category'].required = True
        self.fields['priority'].required = True
        self.fields['event_type'].required = True
        self.fields['audience'].required = True

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        is_all_day = cleaned_data.get('is_all_day')
        
        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date cannot be before start date.")
        
        # Validate time range for same-day events
        if start_date and end_date and start_date == end_date and not is_all_day:
            if start_time and end_time:
                if end_time <= start_time:
                    raise forms.ValidationError("End time must be after start time for same-day events.")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set end_date to start_date if not provided
        if not instance.end_date:
            instance.end_date = instance.start_date
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class EventCategoryForm(forms.ModelForm):
    """Form for creating and editing event categories"""
    
    class Meta:
        model = EventCategory
        fields = ['name', 'description', 'color', 'icon', 'is_active']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Category description...',
                'rows': 3
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FontAwesome icon class (e.g., fas fa-calendar)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class UserCalendarSettingsForm(forms.ModelForm):
    """Form for user calendar preferences"""
    
    class Meta:
        model = UserCalendarSettings
        fields = [
            'default_view', 'show_weekends', 'start_week_on_monday',
            'show_event_details', 'email_notifications', 
            'browser_notifications', 'notification_time',
            'hidden_categories'
        ]
        
        widgets = {
            'default_view': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'show_weekends': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'start_week_on_monday': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'show_event_details': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'browser_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notification_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'hidden_categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'default_view': 'Default Calendar View',
            'show_weekends': 'Show Weekends',
            'start_week_on_monday': 'Start Week on Monday',
            'show_event_details': 'Show Event Details',
            'email_notifications': 'Email Notifications',
            'browser_notifications': 'Browser Notifications',
            'notification_time': 'Notification Time',
            'hidden_categories': 'Hidden Categories',
        }


class EventFilterForm(forms.Form):
    """Form for filtering calendar events"""
    
    VIEW_CHOICES = [
        ('month', 'Month'),
        ('week', 'Week'),
        ('day', 'Day'),
    ]
    
    PRIORITY_CHOICES = CalendarEvent.PRIORITY_LEVELS
    EVENT_TYPE_CHOICES = CalendarEvent.EVENT_TYPES
    
    view = forms.ChoiceField(
        choices=VIEW_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-select'})
    )
    
    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    priority = forms.MultipleChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    event_type = forms.MultipleChoiceField(
        choices=EVENT_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    show_past_events = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_to < date_from:
                raise forms.ValidationError("End date cannot be before start date.")
        
        return cleaned_data


class QuickEventForm(forms.Form):
    """Simplified form for quick event creation"""
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Event title...',
            'required': True
        })
    )
    
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    
    time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'required': True
        })
    )
    
    audience_students = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    audience_teachers = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        audience_students = cleaned_data.get('audience_students')
        audience_teachers = cleaned_data.get('audience_teachers')
        
        if not audience_students and not audience_teachers:
            raise forms.ValidationError("Please select at least one audience.")
        
        return cleaned_data