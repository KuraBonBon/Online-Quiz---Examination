from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, StudentProfile, TeacherProfile

class StudentRegistrationForm(UserCreationForm):
    """Registration form for students"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    student_id = forms.CharField(max_length=20, required=True)
    course = forms.CharField(max_length=100, required=True)
    year_level = forms.ChoiceField(choices=[
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('Graduate', 'Graduate'),
    ], required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.user_type = 'student'
        
        if commit:
            user.save()
            # Create student profile
            StudentProfile.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                course=self.cleaned_data['course'],
                year_level=self.cleaned_data['year_level']
            )
        return user

class TeacherRegistrationForm(UserCreationForm):
    """Registration form for teachers"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    employee_id = forms.CharField(max_length=20, required=True)
    department = forms.CharField(max_length=100, required=True)
    specialization = forms.CharField(max_length=200, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.user_type = 'teacher'
        
        if commit:
            user.save()
            # Create teacher profile
            TeacherProfile.objects.create(
                user=user,
                employee_id=self.cleaned_data['employee_id'],
                department=self.cleaned_data['department'],
                specialization=self.cleaned_data['specialization']
            )
        return user

class CustomLoginForm(AuthenticationForm):
    """Custom login form that uses email instead of username"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'autofocus': True}),
        label='Email'
    )
    
    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email is not None and password:
            self.user_cache = authenticate(
                self.request, 
                username=email, 
                password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
