from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from analytics.models import (
    SystemMetric, PerformanceMetric, UserActivityLog, 
    AnalyticsReport, DashboardWidget
)
from assessments.models import Assessment, StudentAttempt, Question
from courses.models import Course, StudentEnrollment
import random
from datetime import datetime, timedelta
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate analytics with sample data for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all analytics data before populating',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting analytics data...')
            self.reset_analytics_data()

        self.stdout.write('Populating analytics with sample data...')
        
        with transaction.atomic():
            self.create_system_metrics()
            self.create_performance_metrics()
            self.create_user_activity_logs()
            self.create_analytics_reports()
            self.create_dashboard_widgets()

        self.stdout.write(
            self.style.SUCCESS('Successfully populated analytics with sample data!')
        )

    def reset_analytics_data(self):
        """Reset all analytics data"""
        SystemMetric.objects.all().delete()
        PerformanceMetric.objects.all().delete()
        UserActivityLog.objects.all().delete()
        AnalyticsReport.objects.all().delete()
        DashboardWidget.objects.all().delete()

    def create_system_metrics(self):
        """Create sample system metrics"""
        metrics = [
            ('total_users', 'Total Registered Users', User.objects.count()),
            ('total_students', 'Total Students', User.objects.filter(user_type='student').count()),
            ('total_teachers', 'Total Teachers', User.objects.filter(user_type='teacher').count()),
            ('total_assessments', 'Total Assessments', Assessment.objects.count()),
            ('total_questions', 'Total Questions', Question.objects.count()),
            ('total_courses', 'Total Courses', Course.objects.count()),
            ('active_assessments', 'Active Assessments', Assessment.objects.filter(status='published').count()),
        ]

        for metric_type, name, value in metrics:
            SystemMetric.objects.create(
                metric_name=name,
                metric_value=value,
                timestamp=timezone.now()
            )

        # Create historical data for the last 30 days
        for i in range(30):
            date = timezone.now() - timedelta(days=i)
            
            # Daily user registrations
            SystemMetric.objects.create(
                metric_name='Daily User Registrations',
                metric_value=random.randint(1, 10),
                timestamp=date
            )
            
            # Daily logins
            SystemMetric.objects.create(
                metric_name='Daily User Logins',
                metric_value=random.randint(15, 50),
                timestamp=date
            )
            
            # Daily assessments taken
            SystemMetric.objects.create(
                metric_name='Daily Assessments Taken',
                metric_value=random.randint(5, 25),
                timestamp=date
            )

        self.stdout.write('Created system metrics')

    def create_performance_metrics(self):
        """Create sample performance metrics"""
        students = User.objects.filter(user_type='student')[:10]
        assessments = Assessment.objects.all()[:5]
        
        for student in students:
            for assessment in assessments:
                # Create performance metric for each student-assessment combination
                score = random.uniform(60, 100)
                time_taken = random.randint(300, 1800)  # 5-30 minutes
                
                PerformanceMetric.objects.create(
                    metric_type='assessment',
                    user=student,
                    object_id=assessment.id,
                    metric_name='Assessment Score',
                    metric_value=score,
                    additional_data={
                        'time_taken': time_taken,
                        'questions_correct': int((score/100) * assessment.questions.count()),
                        'questions_total': assessment.questions.count(),
                        'assessment_type': assessment.assessment_type
                    },
                    period_start=timezone.now() - timedelta(days=random.randint(1, 30)),
                    period_end=timezone.now(),
                    created_at=timezone.now() - timedelta(days=random.randint(1, 30))
                )

        # Course performance metrics
        courses = Course.objects.all()[:5]
        for student in students:
            for course in courses:
                if random.choice([True, False]):  # Random enrollment
                    avg_score = random.uniform(70, 95)
                    PerformanceMetric.objects.create(
                        metric_type='course',
                        user=student,
                        object_id=course.id,
                        metric_name='Course Average',
                        metric_value=avg_score,
                        additional_data={
                            'assessments_completed': random.randint(3, 8),
                            'total_assessments': random.randint(5, 10),
                            'improvement_rate': random.uniform(-5, 15)
                        },
                        period_start=timezone.now() - timedelta(days=30),
                        period_end=timezone.now(),
                        created_at=timezone.now()
                    )

        self.stdout.write('Created performance metrics')

    def create_user_activity_logs(self):
        """Create sample user activity logs"""
        users = User.objects.all()[:20]
        activities = [
            'login', 'logout', 'assessment_start', 'assessment_complete',
            'course_view', 'profile_update', 'password_change', 'dashboard_view'
        ]
        
        for i in range(500):  # Create 500 activity logs
            user = random.choice(users)
            activity = random.choice(activities)
            
            metadata = {}
            if activity == 'assessment_start':
                metadata = {
                    'assessment_id': random.choice(Assessment.objects.all()).id if Assessment.objects.exists() else 1,
                    'device': random.choice(['desktop', 'mobile', 'tablet']),
                    'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
                }
            elif activity == 'login':
                metadata = {
                    'ip_address': f'192.168.1.{random.randint(1, 255)}',
                    'device': random.choice(['desktop', 'mobile', 'tablet']),
                    'location': random.choice(['Manila', 'Cebu', 'Davao', 'Quezon City'])
                }
            
            UserActivityLog.objects.create(
                user=user,
                action_type=activity,
                metadata=metadata,
                timestamp=timezone.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            )

        self.stdout.write('Created user activity logs')

    def create_analytics_reports(self):
        """Create sample analytics reports"""
        reports = [
            {
                'title': 'Monthly Student Performance Report',
                'report_type': 'student_performance',
                'generated_by': User.objects.filter(user_type='teacher').first(),
                'report_data': {
                    'total_students': 150,
                    'average_score': 82.5,
                    'pass_rate': 85.2,
                    'top_performers': ['John Doe', 'Jane Smith', 'Bob Johnson'],
                    'improvement_needed': ['Alice Brown', 'Charlie Wilson']
                }
            },
            {
                'title': 'Assessment Difficulty Analysis',
                'report_type': 'assessment_statistics',
                'generated_by': User.objects.filter(user_type='teacher').first(),
                'report_data': {
                    'total_assessments': 45,
                    'average_completion_time': 25.5,
                    'difficulty_distribution': {
                        'Easy': 15,
                        'Medium': 20,
                        'Hard': 10
                    },
                    'success_rates': {
                        'Easy': 92.1,
                        'Medium': 78.5,
                        'Hard': 65.3
                    }
                }
            },
            {
                'title': 'System Usage Statistics',
                'report_type': 'system_usage',
                'generated_by': User.objects.filter(is_staff=True).first(),
                'report_data': {
                    'total_logins': 1250,
                    'unique_users': 180,
                    'peak_hours': ['10:00-11:00', '14:00-15:00', '19:00-20:00'],
                    'device_breakdown': {
                        'Desktop': 65,
                        'Mobile': 25,
                        'Tablet': 10
                    }
                }
            }
        ]

        for report_data in reports:
            if report_data['generated_by']:  # Only create if user exists
                AnalyticsReport.objects.create(
                    title=report_data['title'],
                    report_type=report_data['report_type'],
                    generated_by=report_data['generated_by'],
                    report_data=report_data['report_data'],
                    period_start=timezone.now() - timedelta(days=30),
                    period_end=timezone.now(),
                    generated_at=timezone.now() - timedelta(days=random.randint(1, 7))
                )

        self.stdout.write('Created analytics reports')

    def create_dashboard_widgets(self):
        """Create sample dashboard widgets"""
        users = User.objects.all()[:5]  # Get some users to assign widgets to
        
        widgets = [
            {
                'title': 'Student Performance Overview',
                'widget_type': 'chart',
                'configuration': {
                    'chart_type': 'line',
                    'data_source': 'student_performance',
                    'time_range': '30_days',
                    'colors': ['#007bff', '#28a745', '#ffc107']
                }
            },
            {
                'title': 'Recent Activities',
                'widget_type': 'list',
                'configuration': {
                    'item_count': 10,
                    'data_source': 'user_activities',
                    'show_timestamps': True
                }
            },
            {
                'title': 'Assessment Statistics',
                'widget_type': 'metric',
                'configuration': {
                    'metrics': ['total_assessments', 'avg_score', 'completion_rate'],
                    'update_frequency': 'hourly'
                }
            },
            {
                'title': 'Grade Distribution',
                'widget_type': 'chart',
                'configuration': {
                    'chart_type': 'pie',
                    'data_source': 'grade_distribution',
                    'colors': ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
                }
            }
        ]

        for i, widget_data in enumerate(widgets):
            for user in users:
                DashboardWidget.objects.create(
                    user=user,
                    widget_type=widget_data['widget_type'],
                    title=widget_data['title'],
                    configuration=widget_data['configuration'],
                    position_x=i % 2,
                    position_y=i // 2,
                    width=1,
                    height=1,
                    is_active=True
                )

        self.stdout.write('Created dashboard widgets')
