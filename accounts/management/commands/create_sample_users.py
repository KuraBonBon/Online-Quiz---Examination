from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, TeacherProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample users for testing'

    def handle(self, *args, **options):
        # Create sample student
        if not User.objects.filter(email='student@spist.edu').exists():
            student_user = User.objects.create_user(
                username='student_demo',
                email='student@spist.edu',
                password='password123',
                first_name='John',
                last_name='Doe',
                user_type='student',
                is_verified=True
            )
            
            StudentProfile.objects.create(
                user=student_user,
                student_id='2025001',
                course='Computer Science',
                year_level='3rd Year'
            )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created sample student: student@spist.edu (password: password123)')
            )
        
        # Create sample teacher
        if not User.objects.filter(email='teacher@spist.edu').exists():
            teacher_user = User.objects.create_user(
                username='teacher_demo',
                email='teacher@spist.edu',
                password='password123',
                first_name='Jane',
                last_name='Smith',
                user_type='teacher',
                is_verified=True
            )
            
            TeacherProfile.objects.create(
                user=teacher_user,
                employee_id='EMP001',
                department='Computer Science Department',
                specialization='Web Development and Database Systems'
            )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created sample teacher: teacher@spist.edu (password: password123)')
            )
        
        # Create admin user
        if not User.objects.filter(email='admin@spist.edu').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@spist.edu',
                password='admin123',
                first_name='Admin',
                last_name='User',
                user_type='teacher'
            )
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created admin user: admin@spist.edu (password: admin123)')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Sample data creation completed!')
        )
