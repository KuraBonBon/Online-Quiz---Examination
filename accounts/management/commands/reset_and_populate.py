from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from assessments.models import *
from courses.models import *
from accounts.models import *
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset database and create fresh test data for SPIST School Management System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm database reset',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will DELETE ALL DATA and create fresh test accounts.\n'
                    'Run with --confirm to proceed.'
                )
            )
            return

        self.stdout.write('🗑️  Clearing existing data...')
        
        with transaction.atomic():
            # Clear all data
            User.objects.all().delete()
            Assessment.objects.all().delete()
            Course.objects.all().delete()
            StudentProfile.objects.all().delete()
            TeacherProfile.objects.all().delete()
            
            self.stdout.write('✅ Database cleared successfully')
            
            # Create fresh test data
            self.create_test_users()
            self.create_test_courses()
            self.create_test_assessments()
            
        self.stdout.write(
            self.style.SUCCESS(
                '🎉 Fresh test data created successfully!\n'
                '\n📋 Test Accounts Created:'
                '\n👨‍🎓 Students:'
                '\n  - juan.delacruz@spist.edu.ph / password123'
                '\n  - maria.santos@spist.edu.ph / password123'
                '\n  - carlos.reyes@spist.edu.ph / password123'
                '\n👨‍🏫 Teachers:'
                '\n  - prof.garcia@spist.edu.ph / password123'
                '\n  - dr.rodriguez@spist.edu.ph / password123'
                '\n👤 Admin:'
                '\n  - admin@spist.edu.ph / admin123'
                '\n\n🚀 System ready for testing!'
            )
        )

    def create_test_users(self):
        """Create comprehensive test user accounts"""
        self.stdout.write('👤 Creating test users...')
        
        # Create Admin User
        admin = User.objects.create_user(
            username='admin',
            email='admin@spist.edu.ph',
            password='admin123',
            first_name='System',
            last_name='Administrator',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Create Teacher Users
        teachers_data = [
            {
                'username': 'prof.garcia',
                'email': 'prof.garcia@spist.edu.ph',
                'first_name': 'Roberto',
                'last_name': 'Garcia',
                'department': 'Computer Science',
                'specialization': 'Software Engineering'
            },
            {
                'username': 'dr.rodriguez',
                'email': 'dr.rodriguez@spist.edu.ph',
                'first_name': 'Elena',
                'last_name': 'Rodriguez',
                'department': 'Mathematics',
                'specialization': 'Applied Mathematics'
            }
        ]
        
        for teacher_data in teachers_data:
            teacher = User.objects.create_user(
                username=teacher_data['username'],
                email=teacher_data['email'],
                password='password123',
                first_name=teacher_data['first_name'],
                last_name=teacher_data['last_name'],
                user_type='teacher'
            )
            
            TeacherProfile.objects.create(
                user=teacher,
                employee_id=f"T{random.randint(1000, 9999)}",
                department=teacher_data['department'],
                specialization=teacher_data['specialization'],
                office_room=f"Room {random.randint(100, 999)}",
                office_hours="MWF 2:00-4:00 PM, TTh 10:00-12:00 PM"
            )
        
        # Create Student Users
        students_data = [
            {
                'username': 'juan.delacruz',
                'email': 'juan.delacruz@spist.edu.ph',
                'first_name': 'Juan',
                'last_name': 'dela Cruz',
                'course': 'Bachelor of Science in Computer Science',
                'year_level': 3
            },
            {
                'username': 'maria.santos',
                'email': 'maria.santos@spist.edu.ph',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'course': 'Bachelor of Science in Information Technology',
                'year_level': 2
            },
            {
                'username': 'carlos.reyes',
                'email': 'carlos.reyes@spist.edu.ph',
                'first_name': 'Carlos',
                'last_name': 'Reyes',
                'course': 'Bachelor of Science in Computer Science',
                'year_level': 4
            }
        ]
        
        for student_data in students_data:
            student = User.objects.create_user(
                username=student_data['username'],
                email=student_data['email'],
                password='password123',
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                user_type='student'
            )
            
            # Convert year_level number to string format
            year_mapping = {1: '1st Year', 2: '2nd Year', 3: '3rd Year', 4: '4th Year'}
            year_string = year_mapping.get(student_data['year_level'], '4th Year')
            
            StudentProfile.objects.create(
                user=student,
                student_id=f"SPIST-{random.randint(10000, 99999)}",
                course=student_data['course'],
                year_level=year_string,
                address=f"{random.randint(100, 999)} Sample Street, Davao City",
                emergency_contact_name=f"Parent of {student_data['first_name']}",
                emergency_contact_phone=f"09{random.randint(100000000, 999999999)}"
            )

    def create_test_courses(self):
        """Create sample courses and departments"""
        self.stdout.write('📚 Creating test departments and courses...')
        
        # Create departments first
        departments_data = [
            {'code': 'CS', 'name': 'Computer Science'},
            {'code': 'MATH', 'name': 'Mathematics'},
            {'code': 'IT', 'name': 'Information Technology'}
        ]
        
        created_departments = {}
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'description': f"Department of {dept_data['name']}",
                    'is_active': True
                }
            )
            created_departments[dept_data['code']] = dept
        
        # Get teachers for department heads
        teachers = User.objects.filter(user_type='teacher')
        if teachers.exists():
            # Assign department heads
            created_departments['CS'].head_of_department = teachers[0]
            created_departments['CS'].save()
            if len(teachers) > 1:
                created_departments['MATH'].head_of_department = teachers[1]
                created_departments['MATH'].save()
        
        courses_data = [
            {
                'code': 'CS101',
                'title': 'Introduction to Programming',
                'description': 'Basic programming concepts using Python',
                'units': 3,
                'department': 'CS'
            },
            {
                'code': 'CS201',
                'title': 'Data Structures and Algorithms',
                'description': 'Advanced programming concepts and algorithm design',
                'units': 3,
                'department': 'CS'
            },
            {
                'code': 'MATH101',
                'title': 'College Algebra',
                'description': 'Fundamentals of algebra and mathematical reasoning',
                'units': 3,
                'department': 'MATH'
            },
            {
                'code': 'CS301',
                'title': 'Web Development',
                'description': 'Modern web development using HTML, CSS, and JavaScript',
                'units': 3,
                'department': 'CS'
            }
        ]
        
        for course_data in courses_data:
            Course.objects.create(
                code=course_data['code'],
                title=course_data['title'],
                description=course_data['description'],
                units=course_data['units'],
                department=created_departments[course_data['department']],
                is_active=True
            )

    def create_test_assessments(self):
        """Create sample assessments with questions"""
        self.stdout.write('📝 Creating test assessments...')
        
        teachers = User.objects.filter(user_type='teacher')
        courses = Course.objects.all()
        
        # Available subject categories from AssessmentTemplate
        # No need to create categories as they are predefined choices
        
        # Create sample assessments
        assessments_data = [
            {
                'title': 'Python Programming Basics Quiz',
                'description': 'Test your knowledge of Python programming fundamentals',
                'subject_category': 'programming',
                'duration': 60,
                'questions_data': [
                    {
                        'type': 'multiple_choice',
                        'text': 'Which of the following is the correct way to declare a variable in Python?',
                        'choices': ['var x = 5', 'x = 5', 'int x = 5', 'declare x = 5'],
                        'correct': 1
                    },
                    {
                        'type': 'true_false',
                        'text': 'Python is a case-sensitive programming language.',
                        'correct': True
                    },
                    {
                        'type': 'essay',
                        'text': 'Explain the difference between a list and a tuple in Python.',
                        'points': 10
                    }
                ]
            },
            {
                'title': 'Data Structures Midterm Exam',
                'description': 'Comprehensive test on arrays, linked lists, and trees',
                'subject_category': 'programming',
                'duration': 120,
                'questions_data': [
                    {
                        'type': 'multiple_choice',
                        'text': 'What is the time complexity of inserting an element at the beginning of an array?',
                        'choices': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'],
                        'correct': 1
                    },
                    {
                        'type': 'identification',
                        'text': 'What data structure uses LIFO (Last In, First Out) principle?',
                        'correct_answers': ['Stack', 'stack']
                    }
                ]
            }
        ]
        
        for i, assessment_data in enumerate(assessments_data):
            # Assign to teacher
            teacher = teachers[i % len(teachers)]
            
            assessment = Assessment.objects.create(
                title=assessment_data['title'],
                description=assessment_data['description'],
                creator=teacher,
                assessment_type='quiz',
                subject_category=assessment_data['subject_category'],
                time_limit=assessment_data['duration'],
                max_attempts=3,
                available_from=timezone.now() - timedelta(days=1),
                available_until=timezone.now() + timedelta(days=30),
                status='published',
                passing_score=60
            )
            
            # Create questions for the assessment
            for j, question_data in enumerate(assessment_data['questions_data']):
                question = Question.objects.create(
                    assessment=assessment,
                    question_type=question_data['type'],
                    question_text=question_data['text'],
                    points=question_data.get('points', 5),
                    order=j + 1
                )
                
                if question_data['type'] == 'multiple_choice':
                    for k, choice in enumerate(question_data['choices']):
                        Choice.objects.create(
                            question=question,
                            choice_text=choice,
                            is_correct=(k == question_data['correct']),
                            order=k
                        )
                elif question_data['type'] == 'true_false':
                    Choice.objects.create(
                        question=question,
                        choice_text='True',
                        is_correct=question_data['correct'],
                        order=0
                    )
                    Choice.objects.create(
                        question=question,
                        choice_text='False',
                        is_correct=not question_data['correct'],
                        order=1
                    )
                elif question_data['type'] == 'identification':
                    for answer in question_data['correct_answers']:
                        Choice.objects.create(
                            question=question,
                            choice_text=answer,
                            is_correct=True,
                            order=0
                        )

        self.stdout.write('✅ Test assessments created successfully')