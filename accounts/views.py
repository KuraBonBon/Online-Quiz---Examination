from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
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
            return reverse_lazy('accounts:student_dashboard')
        elif user.user_type == 'teacher':
            return reverse_lazy('accounts:teacher_dashboard')
        return reverse_lazy('accounts:home')

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
            return redirect('accounts:login')
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
            return redirect('accounts:login')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'accounts/teacher_register.html', {'form': form})

@login_required
def dashboard_redirect_view(request):
    """Redirect users to appropriate dashboard based on user type"""
    if request.user.user_type == 'student':
        return redirect('accounts:student_dashboard')
    elif request.user.user_type == 'teacher':
        return redirect('accounts:teacher_dashboard')
    else:
        # For admin or other user types, redirect to admin or student dashboard as fallback
        return redirect('accounts:student_dashboard')

def student_dashboard_view(request):
    """Student dashboard"""
    if request.user.is_authenticated and request.user.user_type == 'student':
        return render(request, 'accounts/student_dashboard.html')
    return redirect('accounts:login')

def teacher_dashboard_view(request):
    """Teacher dashboard with optimized assessment loading"""
    if request.user.is_authenticated and request.user.user_type == 'teacher':
        from assessments.models import Assessment
        
        # Get recent assessments with efficient query
        recent_assessments = Assessment.objects.filter(
            creator=request.user
        ).order_by('-created_at')[:5]
        
        # Get assessment counts for dashboard stats
        assessment_stats = {
            'total_assessments': Assessment.objects.filter(creator=request.user).count(),
            'published_assessments': Assessment.objects.filter(
                creator=request.user, status='published'
            ).count(),
            'draft_assessments': Assessment.objects.filter(
                creator=request.user, status='draft'
            ).count(),
        }
        
        context = {
            'recent_assessments': recent_assessments,
            'assessment_stats': assessment_stats,
        }
        
        return render(request, 'accounts/teacher_dashboard.html', context)
    return redirect('accounts:login')
