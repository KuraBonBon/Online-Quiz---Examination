from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import StudentRegistrationForm, TeacherRegistrationForm, CustomLoginForm
from .models import User

class CustomLoginView(LoginView):
    """Custom login view using email"""
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.user_type == 'student':
            return reverse_lazy('student_dashboard')
        elif user.user_type == 'teacher':
            return reverse_lazy('teacher_dashboard')
        return reverse_lazy('home')

def home_view(request):
    """Home page with portal selection"""
    return render(request, 'accounts/home.html')

def student_register_view(request):
    """Student registration view"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Student account created successfully! Please login.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'accounts/student_register.html', {'form': form})

def teacher_register_view(request):
    """Teacher registration view"""
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Teacher account created successfully! Please login.')
            return redirect('login')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'accounts/teacher_register.html', {'form': form})

def student_dashboard_view(request):
    """Student dashboard"""
    if request.user.is_authenticated and request.user.user_type == 'student':
        return render(request, 'accounts/student_dashboard.html')
    return redirect('login')

def teacher_dashboard_view(request):
    """Teacher dashboard"""
    if request.user.is_authenticated and request.user.user_type == 'teacher':
        return render(request, 'accounts/teacher_dashboard.html')
    return redirect('login')
#</content>
#</invoke>
