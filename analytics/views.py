from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Sum, Count, Q, F, Case, When, IntegerField, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
import json

from .models import SystemMetric, PerformanceMetric, UserActivityLog, AnalyticsReport, DashboardWidget
from assessments.models import Assessment, Question, StudentAttempt, StudentAnswer
from courses.models import Course, StudentEnrollment, CourseOffering, Semester
from accounts.models import StudentProfile, TeacherProfile

User = get_user_model()

@login_required
def analytics_dashboard(request):
    """Main analytics dashboard with comprehensive metrics"""
    
    # Check user permissions
    if not (request.user.is_staff or request.user.user_type in ['teacher', 'admin']):
        messages.error(request, 'Access denied. Analytics is available for teachers and administrators.')
        return redirect('accounts:student_dashboard')
    
    # Get time period filter
    period = request.GET.get('period', '30')  # Default to 30 days
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # System Overview Metrics
    system_metrics = get_system_overview_metrics(start_date, end_date)
    
    # User Performance Metrics
    user_metrics = get_user_performance_metrics(start_date, end_date)
    
    # Assessment Analytics
    assessment_metrics = get_assessment_analytics(start_date, end_date)
    
    # Course Analytics
    course_metrics = get_course_analytics(start_date, end_date)
    
    # Recent Activity
    recent_activities = UserActivityLog.objects.select_related('user').filter(
        timestamp__gte=start_date
    )[:20]
    
    # Top Performers
    top_students = get_top_performing_students(start_date, end_date, limit=10)
    
    # Assessment Statistics
    assessment_stats = get_assessment_statistics(start_date, end_date)
    
    # Growth Trends
    growth_trends = get_growth_trends(start_date, end_date)
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'system_metrics': system_metrics,
        'user_metrics': user_metrics,
        'assessment_metrics': assessment_metrics,
        'course_metrics': course_metrics,
        'recent_activities': recent_activities,
        'top_students': top_students,
        'assessment_stats': assessment_stats,
        'growth_trends': growth_trends,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
def student_analytics(request):
    """Detailed student performance analytics"""
    
    if not (request.user.is_staff or request.user.user_type in ['teacher', 'admin']):
        messages.error(request, 'Access denied.')
        return redirect('accounts:student_dashboard')
    
    # Get filtering parameters
    course_filter = request.GET.get('course')
    semester_filter = request.GET.get('semester')
    student_filter = request.GET.get('student')
    
    # Base queryset for student attempts
    attempts = StudentAttempt.objects.select_related(
        'student', 'assessment'
    ).filter(is_completed=True)
    
    # Apply filters
    if course_filter:
        attempts = attempts.filter(assessment__subject_category=course_filter)
    if semester_filter:
        attempts = attempts.filter(assessment__created_at__year=semester_filter)
    if student_filter:
        attempts = attempts.filter(student_id=student_filter)
    
    # Student Performance Summary
    student_performance = attempts.values(
        'student__id',
        'student__first_name',
        'student__last_name',
        'student__email'
    ).annotate(
        total_attempts=Count('id'),
        avg_score=Avg('percentage'),
        total_points=Sum('score'),
        passed_assessments=Count(Case(When(is_passed=True, then=1))),
        failed_assessments=Count(Case(When(is_passed=False, then=1)))
    ).order_by('-avg_score')
    
    # Paginate results
    paginator = Paginator(student_performance, 25)
    page_number = request.GET.get('page')
    student_page = paginator.get_page(page_number)
    
    # Assessment Difficulty Analysis
    assessment_difficulty = Assessment.objects.annotate(
        attempt_count=Count('attempts', filter=Q(attempts__is_completed=True)),
        avg_score=Avg('attempts__percentage', filter=Q(attempts__is_completed=True)),
        pass_rate=Avg(Case(When(attempts__is_passed=True, then=100), default=0))
    ).filter(attempt_count__gt=0).order_by('avg_score')[:10]
    
    # Grade Distribution
    grade_distribution = get_grade_distribution()
    
    # Performance by Question Type
    question_type_performance = get_question_type_performance()
    
    # Get available filters
    courses = Course.objects.filter(is_active=True)
    students = User.objects.filter(user_type='student', is_active=True)
    
    context = {
        'student_performance': student_page,
        'assessment_difficulty': assessment_difficulty,
        'grade_distribution': grade_distribution,
        'question_type_performance': question_type_performance,
        'courses': courses,
        'students': students,
        'current_filters': {
            'course': course_filter,
            'semester': semester_filter,
            'student': student_filter,
        }
    }
    
    return render(request, 'analytics/student_analytics.html', context)

@login_required
def teacher_analytics(request):
    """Teacher activity and effectiveness analytics"""
    
    if not (request.user.is_staff or request.user.user_type in ['teacher', 'admin']):
        messages.error(request, 'Access denied.')
        return redirect('accounts:student_dashboard')
    
    # Teacher Activity Metrics
    teacher_activities = User.objects.filter(
        user_type='teacher'
    ).annotate(
        assessments_created=Count('created_assessments'),
        total_questions=Count('created_assessments__questions'),
        students_taught=Count('created_assessments__attempts__student', distinct=True),
        avg_student_score=Avg('created_assessments__attempts__percentage')
    ).order_by('-assessments_created')
    
    # Assessment Creation Trends
    assessment_trends = get_assessment_creation_trends()
    
    # Teacher Workload Analysis
    teacher_workload = get_teacher_workload_analysis()
    
    # Question Type Usage by Teachers
    question_type_usage = get_question_type_usage_by_teachers()
    
    context = {
        'teacher_activities': teacher_activities,
        'assessment_trends': assessment_trends,
        'teacher_workload': teacher_workload,
        'question_type_usage': question_type_usage,
    }
    
    return render(request, 'analytics/teacher_analytics.html', context)

@login_required
def assessment_analytics(request):
    """Detailed assessment performance analytics"""
    
    if not (request.user.is_staff or request.user.user_type in ['teacher', 'admin']):
        messages.error(request, 'Access denied.')
        return redirect('accounts:student_dashboard')
    
    # Assessment Performance Overview
    assessments = Assessment.objects.annotate(
        attempt_count=Count('attempts', filter=Q(attempts__is_completed=True)),
        avg_score=Avg('attempts__percentage', filter=Q(attempts__is_completed=True)),
        calculated_completion_rate=Count('attempts', filter=Q(attempts__is_completed=True)) * 100.0 / Count('attempts'),
        pass_rate=Count('attempts', filter=Q(attempts__is_passed=True)) * 100.0 / Count('attempts', filter=Q(attempts__is_completed=True))
    ).filter(status='published').order_by('-attempt_count')
    
    # Question Difficulty Analysis
    question_difficulty = Question.objects.annotate(
        attempt_count=Count('studentanswer'),
        correct_count=Count('studentanswer', filter=Q(studentanswer__is_correct=True)),
        difficulty_score=Case(
            When(studentanswer__isnull=True, then=0),
            default=F('correct_count') * 100.0 / Count('studentanswer')
        )
    ).order_by('difficulty_score')
    
    # Time-based Performance
    time_performance = get_time_based_performance()
    
    # Assessment Type Comparison
    type_comparison = get_assessment_type_comparison()
    
    context = {
        'assessments': assessments,
        'question_difficulty': question_difficulty,
        'time_performance': time_performance,
        'type_comparison': type_comparison,
    }
    
    return render(request, 'analytics/assessment_analytics.html', context)

@login_required
def system_analytics(request):
    """System usage and performance analytics"""
    
    if not (request.user.is_staff or request.user.user_type != 'admin'):
        messages.error(request, 'Access denied. System analytics is available for administrators only.')
        return redirect('accounts:teacher_dashboard')
    
    # System Usage Metrics
    usage_metrics = get_system_usage_metrics()
    
    # User Activity Patterns
    activity_patterns = get_user_activity_patterns()
    
    # System Performance Metrics
    performance_metrics = get_system_performance_metrics()
    
    # Database Statistics
    db_stats = get_database_statistics()
    
    context = {
        'usage_metrics': usage_metrics,
        'activity_patterns': activity_patterns,
        'performance_metrics': performance_metrics,
        'db_stats': db_stats,
    }
    
    return render(request, 'analytics/system_analytics.html', context)

@login_required
def export_analytics(request):
    """Export analytics data in various formats"""
    
    if not (request.user.is_staff or request.user.user_type in ['teacher', 'admin']):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    export_type = request.GET.get('type', 'student_performance')
    format_type = request.GET.get('format', 'json')
    
    try:
        if export_type == 'student_performance':
            data = export_student_performance_data()
        elif export_type == 'assessment_stats':
            data = export_assessment_statistics()
        elif export_type == 'teacher_activity':
            data = export_teacher_activity_data()
        else:
            return JsonResponse({'error': 'Invalid export type'}, status=400)
        
        if format_type == 'json':
            return JsonResponse(data, safe=False)
        elif format_type == 'csv':
            # Implement CSV export
            pass
        else:
            return JsonResponse({'error': 'Invalid format'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Helper Functions

def get_system_overview_metrics(start_date, end_date):
    """Get system-wide overview metrics"""
    return {
        'total_users': User.objects.count(),
        'active_students': User.objects.filter(user_type='student', is_active=True).count(),
        'active_teachers': User.objects.filter(user_type='teacher', is_active=True).count(),
        'total_assessments': Assessment.objects.count(),
        'published_assessments': Assessment.objects.filter(status='published').count(),
        'total_questions': Question.objects.count(),
        'completed_attempts': StudentAttempt.objects.filter(
            is_completed=True, 
            completed_at__range=[start_date, end_date]
        ).count(),
        'average_score': StudentAttempt.objects.filter(
            is_completed=True,
            completed_at__range=[start_date, end_date]
        ).aggregate(avg_score=Avg('percentage'))['avg_score'] or 0,
    }

def get_user_performance_metrics(start_date, end_date):
    """Get user performance metrics"""
    return {
        'active_users': UserActivityLog.objects.filter(
            timestamp__range=[start_date, end_date]
        ).values('user').distinct().count(),
        'new_registrations': User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).count(),
        'login_count': UserActivityLog.objects.filter(
            action_type='login',
            timestamp__range=[start_date, end_date]
        ).count(),
        'avg_session_duration': 45,  # Mock data - implement session tracking
    }

def get_assessment_analytics(start_date, end_date):
    """Get assessment analytics"""
    assessments_created = Assessment.objects.filter(
        created_at__range=[start_date, end_date]
    ).count()
    
    attempts_made = StudentAttempt.objects.filter(
        started_at__range=[start_date, end_date]
    ).count()
    
    completed_attempts = StudentAttempt.objects.filter(
        is_completed=True,
        completed_at__range=[start_date, end_date]
    ).count()
    
    return {
        'assessments_created': assessments_created,
        'attempts_made': attempts_made,
        'completed_attempts': completed_attempts,
        'completion_rate': (completed_attempts / attempts_made * 100) if attempts_made > 0 else 0,
        'avg_attempts_per_assessment': attempts_made / assessments_created if assessments_created > 0 else 0,
    }

def get_course_analytics(start_date, end_date):
    """Get course analytics"""
    return {
        'total_courses': Course.objects.filter(is_active=True).count(),
        'active_enrollments': StudentEnrollment.objects.filter(
            status='enrolled'
        ).count(),
        'new_enrollments': StudentEnrollment.objects.filter(
            enrolled_at__range=[start_date, end_date]
        ).count(),
        'avg_students_per_course': StudentEnrollment.objects.filter(
            status='enrolled'
        ).count() / Course.objects.filter(is_active=True).count() if Course.objects.filter(is_active=True).count() > 0 else 0,
    }

def get_top_performing_students(start_date, end_date, limit=10):
    """Get top performing students"""
    return StudentAttempt.objects.filter(
        is_completed=True,
        completed_at__range=[start_date, end_date]
    ).values(
        'student__first_name',
        'student__last_name',
        'student__email'
    ).annotate(
        avg_score=Avg('percentage'),
        total_attempts=Count('id')
    ).filter(total_attempts__gte=3).order_by('-avg_score')[:limit]

def get_assessment_statistics(start_date, end_date):
    """Get detailed assessment statistics"""
    return {
        'quiz_count': Assessment.objects.filter(
            assessment_type='quiz',
            created_at__range=[start_date, end_date]
        ).count(),
        'exam_count': Assessment.objects.filter(
            assessment_type='exam',
            created_at__range=[start_date, end_date]
        ).count(),
        'avg_quiz_score': StudentAttempt.objects.filter(
            assessment__assessment_type='quiz',
            is_completed=True,
            completed_at__range=[start_date, end_date]
        ).aggregate(avg=Avg('percentage'))['avg'] or 0,
        'avg_exam_score': StudentAttempt.objects.filter(
            assessment__assessment_type='exam',
            is_completed=True,
            completed_at__range=[start_date, end_date]
        ).aggregate(avg=Avg('percentage'))['avg'] or 0,
    }

def get_growth_trends(start_date, end_date):
    """Get growth trends over time"""
    # Calculate growth compared to previous period
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date
    
    current_users = User.objects.filter(date_joined__range=[start_date, end_date]).count()
    prev_users = User.objects.filter(date_joined__range=[prev_start, prev_end]).count()
    
    current_assessments = Assessment.objects.filter(created_at__range=[start_date, end_date]).count()
    prev_assessments = Assessment.objects.filter(created_at__range=[prev_start, prev_end]).count()
    
    return {
        'user_growth': calculate_growth_percentage(prev_users, current_users),
        'assessment_growth': calculate_growth_percentage(prev_assessments, current_assessments),
    }

def calculate_growth_percentage(previous, current):
    """Calculate growth percentage"""
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100

def get_grade_distribution():
    """Get grade distribution data"""
    return StudentAttempt.objects.filter(
        is_completed=True
    ).aggregate(
        a_grade=Count(Case(When(percentage__gte=90, then=1))),
        b_grade=Count(Case(When(percentage__gte=80, percentage__lt=90, then=1))),
        c_grade=Count(Case(When(percentage__gte=70, percentage__lt=80, then=1))),
        d_grade=Count(Case(When(percentage__gte=60, percentage__lt=70, then=1))),
        f_grade=Count(Case(When(percentage__lt=60, then=1))),
    )

def get_question_type_performance():
    """Get performance by question type"""
    return Question.objects.values('question_type').annotate(
        total_answers=Count('studentanswer'),
        correct_answers=Count('studentanswer', filter=Q(studentanswer__is_correct=True)),
        accuracy=Case(
            When(studentanswer__isnull=True, then=0),
            default=F('correct_answers') * 100.0 / F('total_answers')
        )
    )

def get_assessment_creation_trends():
    """Get assessment creation trends"""
    # Mock implementation - add actual trend calculation
    return []

def get_teacher_workload_analysis():
    """Get teacher workload analysis"""
    # Mock implementation - add actual workload calculation
    return []

def get_question_type_usage_by_teachers():
    """Get question type usage by teachers"""
    # Mock implementation - add actual usage calculation
    return []

def get_time_based_performance():
    """Get time-based performance data"""
    # Mock implementation - add actual time-based analysis
    return []

def get_assessment_type_comparison():
    """Get assessment type comparison"""
    # Mock implementation - add actual comparison
    return []

def get_system_usage_metrics():
    """Get system usage metrics"""
    # Mock implementation - add actual usage metrics
    return {}

def get_user_activity_patterns():
    """Get user activity patterns"""
    # Mock implementation - add actual pattern analysis
    return []

def get_system_performance_metrics():
    """Get system performance metrics"""
    # Mock implementation - add actual performance metrics
    return {}

def get_database_statistics():
    """Get database statistics"""
    return {
        'total_users': User.objects.count(),
        'total_assessments': Assessment.objects.count(),
        'total_questions': Question.objects.count(),
        'total_attempts': StudentAttempt.objects.count(),
        'total_answers': StudentAnswer.objects.count(),
    }

def export_student_performance_data():
    """Export student performance data"""
    # Mock implementation - add actual export logic
    return []

def export_assessment_statistics():
    """Export assessment statistics"""
    # Mock implementation - add actual export logic
    return []

def export_teacher_activity_data():
    """Export teacher activity data"""
    # Mock implementation - add actual export logic
    return []
