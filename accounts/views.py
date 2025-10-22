from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db.models import Q
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
    if request.user.is_staff or request.user.is_superuser:
        return redirect('accounts:admin_dashboard')
    elif request.user.user_type == 'student':
        return redirect('accounts:student_dashboard')
    elif request.user.user_type == 'teacher':
        return redirect('accounts:teacher_dashboard')
    else:
        # For other user types, redirect to student dashboard as fallback
        return redirect('accounts:student_dashboard')

def student_dashboard_view(request):
    """Enhanced student dashboard with comprehensive assessment data"""
    if request.user.is_authenticated and request.user.user_type == 'student':
        from assessments.models import Assessment, StudentAttempt
        from courses.models import Course, StudentEnrollment
        from accounts.models import UserActivityLog
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import datetime
        
        # Determine greeting based on time of day
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good morning"
        elif current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        # Get student's enrolled courses
        enrolled_courses = StudentEnrollment.objects.filter(
            student=request.user, 
            status='enrolled'
        ).select_related('course_offering__course')
        
        # Get available assessments (published and available)
        available_assessments = Assessment.objects.filter(
            status='published'
        ).filter(
            Q(available_from__isnull=True) | Q(available_from__lte=timezone.now())
        ).filter(
            Q(available_until__isnull=True) | Q(available_until__gte=timezone.now())
        ).exclude(
            # Exclude assessments student has already completed
            attempts__student=request.user,
            attempts__is_completed=True
        ).select_related('creator').order_by('-created_at')
        
        # Get student's assessment attempts
        student_attempts = StudentAttempt.objects.filter(
            student=request.user
        ).select_related('assessment').order_by('-completed_at')
        
        # Get completed attempts (without slicing first for calculations)
        completed_attempts_queryset = student_attempts.filter(is_completed=True)
        completed_attempts = completed_attempts_queryset[:10]
        
        # Get pending/in-progress attempts
        pending_attempts = student_attempts.filter(is_completed=False)[:5]
        
        # Calculate statistics
        total_attempts = student_attempts.count()
        total_completed = completed_attempts_queryset.count()
        total_courses = enrolled_courses.count()
        
        # Calculate average score
        avg_score = completed_attempts_queryset.aggregate(avg=Avg('percentage'))['avg'] or 0
        
        # Get recent grades
        recent_grades = completed_attempts_queryset.filter(
            percentage__isnull=False
        ).order_by('-graded_at', '-completed_at')[:5]
        
        # Get upcoming assessments (within next 7 days)
        upcoming_assessments = Assessment.objects.filter(
            status='published',
            available_from__gt=timezone.now(),
            available_from__lte=timezone.now() + timezone.timedelta(days=7)
        ).exclude(
            attempts__student=request.user,
            attempts__is_completed=True
        ).select_related('creator').order_by('available_from')[:5]
        
        # Get recent activity logs (safely handle if table doesn't exist)
        try:
            recent_activities = UserActivityLog.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10]
        except:
            recent_activities = []
        
        # Performance analytics by subject category
        performance_by_course = {}
        if completed_attempts.exists():
            # Group by assessment subject category since we don't have direct course relationship
            subject_performance = {}
            for attempt in completed_attempts:
                subject = attempt.assessment.subject_category
                if subject not in subject_performance:
                    subject_performance[subject] = []
                subject_performance[subject].append(attempt.percentage or 0)
            
            for subject, scores in subject_performance.items():
                if scores:
                    performance_by_course[subject.title()] = {
                        'avg_score': sum(scores) / len(scores),
                        'attempts_count': len(scores),
                        'course': None  # No direct course relation in current model
                    }
        
        # Calculate progress circle offset (circumference = 326.73)
        # offset = circumference - (percentage * circumference / 100)
        progress_offset = 326.73 - (float(avg_score) * 3.2673)
        
        context = {
            'greeting': greeting,
            'enrolled_courses_count': total_courses,
            'available_tests_count': available_assessments.count(),
            'completed_tests_count': total_completed,
            'average_score': avg_score,
            'progress_offset': progress_offset,
            'available_assessments': available_assessments,
            'recent_activities': recent_activities,
            'enrolled_courses': enrolled_courses,
            'completed_attempts': completed_attempts,
            'pending_attempts': pending_attempts,
            'recent_grades': recent_grades,
            'upcoming_assessments': upcoming_assessments,
            'performance_by_course': performance_by_course,
            'student_stats': {
                'total_attempts': total_attempts,
                'total_completed': total_completed,
                'total_courses': total_courses,
                'avg_score': avg_score,
                'available_assessments_count': available_assessments.count(),
                'upcoming_assessments_count': upcoming_assessments.count(),
            }
        }
        
        return render(request, 'accounts/student_dashboard.html', context)
    return redirect('accounts:login')

@login_required
def admin_dashboard_view(request):
    """Enhanced admin dashboard with comprehensive system oversight"""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        from assessments.models import Assessment, StudentAttempt, Question
        from courses.models import Course, StudentEnrollment
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        
        # System-wide statistics
        total_users = User.objects.count()
        total_students = User.objects.filter(user_type='student').count()
        total_teachers = User.objects.filter(user_type='teacher').count()
        total_assessments = Assessment.objects.count()
        total_attempts = StudentAttempt.objects.count()
        total_courses = Course.objects.count()
        total_enrollments = StudentEnrollment.objects.filter(status='enrolled').count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()
        recent_assessments = Assessment.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        recent_attempts = StudentAttempt.objects.filter(
            completed_at__gte=thirty_days_ago
        ).count()
        
        # System performance metrics
        completed_attempts = StudentAttempt.objects.filter(is_completed=True)
        avg_completion_rate = (completed_attempts.count() / max(total_attempts, 1)) * 100
        avg_system_score = completed_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
        
        # Recent user registrations
        recent_users = User.objects.select_related(
            'student_profile', 'teacher_profile'
        ).order_by('-date_joined')[:10]
        
        # Active assessments
        active_assessments = Assessment.objects.filter(
            status='published'
        ).select_related('creator').order_by('-created_at')[:10]
        
        # Popular courses (by enrollment)
        popular_courses = Course.objects.annotate(
            enrollment_count=Count('enrollments', filter=Q(enrollments__is_active=True))
        ).order_by('-enrollment_count')[:5]
        
        # System health indicators
        pending_grading = StudentAttempt.objects.filter(
            is_completed=True,
            percentage__isnull=True
        ).count()
        
        draft_assessments = Assessment.objects.filter(status='draft').count()
        
        context = {
            'system_stats': {
                'total_users': total_users,
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_assessments': total_assessments,
                'total_attempts': total_attempts,
                'total_courses': total_courses,
                'total_enrollments': total_enrollments,
                'recent_registrations': recent_registrations,
                'recent_assessments': recent_assessments,
                'recent_attempts': recent_attempts,
                'avg_completion_rate': avg_completion_rate,
                'avg_system_score': avg_system_score,
                'pending_grading': pending_grading,
                'draft_assessments': draft_assessments,
            },
            'recent_users': recent_users,
            'active_assessments': active_assessments,
            'popular_courses': popular_courses,
        }
        
        return render(request, 'accounts/admin_dashboard.html', context)
    return redirect('accounts:login')

@login_required
def user_management_view(request):
    """User management for administrators"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('accounts:login')
    
    from django.core.paginator import Paginator
    
    # Get all users with profiles
    users = get_user_model().objects.select_related(
        'student_profile', 'teacher_profile'
    ).order_by('-date_joined')
    
    # Apply search filter if provided
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by user type if provided
    user_type_filter = request.GET.get('user_type', '')
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'total_users': users.count(),
    }
    
    return render(request, 'accounts/user_management.html', context)

def teacher_dashboard_view(request):
    """Enhanced teacher dashboard with comprehensive assessment management"""
    if request.user.is_authenticated and request.user.user_type == 'teacher':
        from assessments.models import Assessment, StudentAttempt, Question
        from courses.models import Course, CourseOffering
        from django.db.models import Count, Avg, Q, Case, When, IntegerField
        
        # Get teacher's courses
        teacher_courses = Course.objects.filter(
            offerings__teacher=request.user
        ).distinct().annotate(
            enrollment_count=Count('offerings__enrollments', distinct=True),
            assessment_count=Count('assessments', distinct=True)
        ).order_by('-created_at')
        
        # Get comprehensive assessment data
        assessments = Assessment.objects.filter(
            creator=request.user
        ).annotate(
            question_count=Count('questions'),
            attempt_count=Count('attempts'),
            completed_attempts=Count('attempts', filter=Q(attempts__is_completed=True)),
            calculated_avg_score=Avg('attempts__percentage', filter=Q(attempts__is_completed=True))
        ).order_by('-created_at')
        
        # Get recent assessments for quick access
        recent_assessments = assessments[:5]
        
        # Get assessments needing grading
        assessments_needing_grading = Assessment.objects.filter(
            creator=request.user,
            attempts__is_completed=True,
            questions__question_type__in=['identification', 'essay', 'enumeration']
        ).annotate(
            ungraded_count=Count('attempts__answers', filter=Q(
                attempts__answers__is_manually_graded=False,
                attempts__answers__question__question_type__in=['identification', 'essay', 'enumeration']
            ))
        ).filter(ungraded_count__gt=0).distinct()[:5]
        
        # Get recent student attempts
        recent_attempts = StudentAttempt.objects.filter(
            assessment__creator=request.user,
            is_completed=True
        ).select_related('student', 'assessment').order_by('-completed_at')[:10]
        
        # Calculate statistics
        total_assessments = assessments.count()
        total_attempts = StudentAttempt.objects.filter(assessment__creator=request.user).count()
        total_completed = StudentAttempt.objects.filter(
            assessment__creator=request.user, 
            is_completed=True
        ).count()
        total_questions = Question.objects.filter(assessment__creator=request.user).count()
        pending_grading_count = assessments_needing_grading.count()
        
        # Calculate average scores
        avg_score = StudentAttempt.objects.filter(
            assessment__creator=request.user,
            is_completed=True
        ).aggregate(avg=Avg('percentage'))['avg'] or 0
        
        # Calculate grade distribution
        completed_attempts_with_scores = StudentAttempt.objects.filter(
            assessment__creator=request.user,
            is_completed=True,
            percentage__isnull=False
        )
        
        total_graded = completed_attempts_with_scores.count()
        grade_distribution = {
            'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0
        }
        
        if total_graded > 0:
            for letter_grade in ['A', 'B', 'C', 'D', 'F']:
                if letter_grade == 'A':
                    count = completed_attempts_with_scores.filter(percentage__gte=90).count()
                elif letter_grade == 'B':
                    count = completed_attempts_with_scores.filter(percentage__gte=80, percentage__lt=90).count()
                elif letter_grade == 'C':
                    count = completed_attempts_with_scores.filter(percentage__gte=70, percentage__lt=80).count()
                elif letter_grade == 'D':
                    count = completed_attempts_with_scores.filter(percentage__gte=60, percentage__lt=70).count()
                else:  # F
                    count = completed_attempts_with_scores.filter(percentage__lt=60).count()
                
                grade_distribution[letter_grade] = round((count / total_graded) * 100, 1)
        
        # Get top performing students
        top_students = completed_attempts_with_scores.values(
            'student__id', 
            'student__first_name', 
            'student__last_name'
        ).annotate(
            avg_score=Avg('percentage')
        ).order_by('-avg_score')[:10]
        
        # Get assessment stats
        assessment_stats = {
            'total_assessments': total_assessments,
            'published_assessments': Assessment.objects.filter(
                creator=request.user, status='published'
            ).count(),
            'draft_assessments': Assessment.objects.filter(
                creator=request.user, status='draft'
            ).count(),
        }
        
        context = {
            'total_assessments': total_assessments,
            'total_attempts': total_attempts,
            'pending_grading_count': pending_grading_count,
            'average_class_score': avg_score,
            'grade_distribution': grade_distribution,
            'top_students': top_students,
            'teacher_courses': teacher_courses,
            'grading_queue': assessments_needing_grading,
            'recent_attempts': recent_attempts,
            'active_assessments_list': recent_assessments,
            'assessment_stats': assessment_stats,
        }
        
        return render(request, 'accounts/teacher_dashboard.html', context)
    return redirect('accounts:login')
