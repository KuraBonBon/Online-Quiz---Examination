from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import StudentProfile, TeacherProfile
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class BaseProfileForm(forms.ModelForm):
    """Base form for common profile fields"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+63 XXX XXX XXXX'
            }),
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Philippine phone number validation
            phone_pattern = r'^(\+63|0)[9]\d{9}$'
            if not re.match(phone_pattern, phone.replace(' ', '').replace('-', '')):
                raise ValidationError('Please enter a valid Philippine mobile number (e.g., +639123456789 or 09123456789)')
        return phone

class StudentProfileUpdateForm(BaseProfileForm):
    """Form for students to update their profile"""
    course = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Bachelor of Science in Computer Science'
        })
    )
    year_level = forms.ChoiceField(
        choices=StudentProfile._meta.get_field('year_level').choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Additional profile fields
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tell us about yourself...',
            'maxlength': 500
        })
    )
    
    class Meta(BaseProfileForm.Meta):
        fields = BaseProfileForm.Meta.fields + ['bio']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate student profile fields if available
        if self.user and hasattr(self.user, 'student_profile'):
            profile = self.user.student_profile
            self.fields['course'].initial = profile.course
            self.fields['year_level'].initial = profile.year_level
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'student_profile'):
            profile = user.student_profile
            profile.course = self.cleaned_data['course']
            profile.year_level = self.cleaned_data['year_level']
            profile.save()
        return user

class TeacherProfileUpdateForm(BaseProfileForm):
    """Form for teachers to update their profile"""
    department = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Computer Science Department'
        })
    )
    specialization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Web Development, Data Science'
        })
    )
    
    # Additional profile fields
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Professional background and expertise...',
            'maxlength': 500
        })
    )
    
    office_hours = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., MWF 2:00-4:00 PM'
        })
    )
    
    class Meta(BaseProfileForm.Meta):
        fields = BaseProfileForm.Meta.fields + ['bio']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate teacher profile fields if available
        if self.user and hasattr(self.user, 'teacher_profile'):
            profile = self.user.teacher_profile
            self.fields['department'].initial = profile.department
            self.fields['specialization'].initial = profile.specialization
    
    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'teacher_profile'):
            profile = user.teacher_profile
            profile.department = self.cleaned_data['department']
            profile.specialization = self.cleaned_data['specialization']
            profile.save()
        return user

class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with better styling"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })

class NotificationSettingsForm(forms.Form):
    """Form for notification preferences"""
    email_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    assignment_reminders = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    grade_notifications = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    course_updates = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class PrivacySettingsForm(forms.Form):
    """Form for privacy settings"""
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('students_only', 'Students Only'),
        ('teachers_only', 'Teachers Only'),
        ('private', 'Private')
    ]
    
    profile_visibility = forms.ChoiceField(
        choices=VISIBILITY_CHOICES,
        initial='students_only',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    show_email = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    show_phone = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class AvatarUploadForm(forms.Form):
    """Form for profile picture upload"""
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError('Image file too large. Please keep it under 5MB.')
            if not avatar.content_type.startswith('image/'):
                raise ValidationError('Please upload a valid image file.')
        return avatar

class AccountDeactivationForm(forms.Form):
    """Form for account deactivation confirmation"""
    confirm_deactivation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional: Tell us why you are deactivating your account'
        })
    )
