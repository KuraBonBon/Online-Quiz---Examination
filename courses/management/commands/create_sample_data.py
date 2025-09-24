from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import (
    Department, AcademicYear, Semester, Curriculum, Course, CurriculumCourse,
    CourseOffering, StudentCurriculum, EnrollmentPeriod
)
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample course data for testing enrollment system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample course data...'))
        
        # Create departments
        departments = [
            {'name': 'Computer Science', 'code': 'CS', 'description': 'Department of Computer Science'},
            {'name': 'Information Technology', 'code': 'IT', 'description': 'Department of Information Technology'},
            {'name': 'Engineering', 'code': 'ENGR', 'description': 'Department of Engineering'},
            {'name': 'Business Administration', 'code': 'BA', 'description': 'Department of Business Administration'},
        ]
        
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'description': dept_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')
        
        # Create academic year
        academic_year, created = AcademicYear.objects.get_or_create(
            year_start=2024,
            year_end=2025,
            defaults={'is_current': True}
        )
        if created:
            self.stdout.write(f'Created academic year: {academic_year}')
        
        # Create semesters
        first_semester, created = Semester.objects.get_or_create(
            academic_year=academic_year,
            semester='1st',
            defaults={
                'start_date': timezone.now().date(),
                'end_date': (timezone.now() + timedelta(days=120)).date(),
                'is_current': True
            }
        )
        if created:
            self.stdout.write(f'Created semester: {first_semester}')
        
        # Create enrollment period
        enrollment_period, created = EnrollmentPeriod.objects.get_or_create(
            semester=first_semester,
            defaults={
                'name': 'Regular Enrollment Period',
                'start_date': timezone.now() - timedelta(days=7),
                'end_date': timezone.now() + timedelta(days=30),
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created enrollment period: {enrollment_period}')
        
        # Create curricula
        cs_dept = Department.objects.get(code='CS')
        it_dept = Department.objects.get(code='IT')
        
        cs_curriculum, created = Curriculum.objects.get_or_create(
            code='BSCS',
            defaults={
                'name': 'Bachelor of Science in Computer Science',
                'department': cs_dept,
                'year_introduced': 2024,
                'total_units': 144,
                'description': 'Comprehensive Computer Science program',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created curriculum: {cs_curriculum}')
        
        it_curriculum, created = Curriculum.objects.get_or_create(
            code='BSIT',
            defaults={
                'name': 'Bachelor of Science in Information Technology',
                'department': it_dept,
                'year_introduced': 2024,
                'total_units': 144,
                'description': 'Comprehensive Information Technology program',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created curriculum: {it_curriculum}')
        
        # Create courses
        courses_data = [
            # CS Courses
            {'code': 'CS101', 'title': 'Introduction to Programming', 'units': 3, 'course_type': 'core', 'year': 1},
            {'code': 'CS102', 'title': 'Data Structures and Algorithms', 'units': 3, 'course_type': 'core', 'year': 2},
            {'code': 'CS103', 'title': 'Object-Oriented Programming', 'units': 3, 'course_type': 'core', 'year': 2},
            {'code': 'CS201', 'title': 'Database Systems', 'units': 3, 'course_type': 'core', 'year': 2},
            {'code': 'CS202', 'title': 'Web Development', 'units': 3, 'course_type': 'core', 'year': 3},
            {'code': 'CS301', 'title': 'Software Engineering', 'units': 3, 'course_type': 'core', 'year': 3},
            {'code': 'CS302', 'title': 'Computer Networks', 'units': 3, 'course_type': 'core', 'year': 3},
            {'code': 'CS401', 'title': 'Artificial Intelligence', 'units': 3, 'course_type': 'elective', 'year': 4},
            {'code': 'CS402', 'title': 'Machine Learning', 'units': 3, 'course_type': 'elective', 'year': 4},
            
            # IT Courses  
            {'code': 'IT101', 'title': 'Introduction to Information Technology', 'units': 3, 'course_type': 'core', 'year': 1},
            {'code': 'IT102', 'title': 'System Administration', 'units': 3, 'course_type': 'core', 'year': 2},
            {'code': 'IT201', 'title': 'Network Administration', 'units': 3, 'course_type': 'core', 'year': 2},
            {'code': 'IT202', 'title': 'Cybersecurity Fundamentals', 'units': 3, 'course_type': 'core', 'year': 3},
            {'code': 'IT301', 'title': 'Cloud Computing', 'units': 3, 'course_type': 'elective', 'year': 3},
            
            # General Education
            {'code': 'GE101', 'title': 'Mathematics in the Modern World', 'units': 3, 'course_type': 'general', 'year': 1},
            {'code': 'GE102', 'title': 'Purposive Communication', 'units': 3, 'course_type': 'general', 'year': 1},
            {'code': 'GE103', 'title': 'Understanding the Self', 'units': 3, 'course_type': 'general', 'year': 1},
            {'code': 'GE104', 'title': 'The Contemporary World', 'units': 3, 'course_type': 'general', 'year': 2},
            {'code': 'PE101', 'title': 'Physical Education 1', 'units': 2, 'course_type': 'general', 'year': 1},
            {'code': 'NSTP1', 'title': 'National Service Training Program 1', 'units': 3, 'course_type': 'general', 'year': 1},
        ]
        
        created_courses = []
        for course_data in courses_data:
            # Determine department based on course code
            if course_data['code'].startswith('CS'):
                dept = cs_dept
            elif course_data['code'].startswith('IT'):
                dept = it_dept  
            else:
                # General education courses - assign to CS dept for simplicity
                dept = cs_dept
                
            course, created = Course.objects.get_or_create(
                code=course_data['code'],
                defaults={
                    'title': course_data['title'],
                    'description': f"Description for {course_data['title']}",
                    'units': course_data['units'],
                    'department': dept,
                    'course_type': course_data['course_type'],
                    'is_active': True
                }
            )
            if created:
                created_courses.append((course, course_data['year']))
                self.stdout.write(f'Created course: {course.code} - {course.title}')
        
        # Add courses to curricula
        for course, year_level in created_courses:
            if course.code.startswith('CS') or course.code.startswith('GE') or course.code.startswith('PE') or course.code.startswith('NSTP'):
                curriculum_course, created = CurriculumCourse.objects.get_or_create(
                    curriculum=cs_curriculum,
                    course=course,
                    defaults={
                        'year_level': year_level,
                        'semester': '1st',
                        'is_required': course.course_type in ['core', 'general']
                    }
                )
                if created:
                    self.stdout.write(f'Added {course.code} to CS curriculum')
            
            if course.code.startswith('IT') or course.code.startswith('GE') or course.code.startswith('PE') or course.code.startswith('NSTP'):
                curriculum_course, created = CurriculumCourse.objects.get_or_create(
                    curriculum=it_curriculum,
                    course=course,
                    defaults={
                        'year_level': year_level,
                        'semester': '1st',
                        'is_required': course.course_type in ['core', 'general']
                    }
                )
                if created:
                    self.stdout.write(f'Added {course.code} to IT curriculum')
        
        # Create teacher if doesn't exist
        teacher_email = 'teacher@spist.edu.ph'
        teacher, created = User.objects.get_or_create(
            email=teacher_email,
            defaults={
                'username': 'teacher1',
                'first_name': 'John',
                'last_name': 'Doe',
                'user_type': 'teacher',
                'is_active': True
            }
        )
        if created:
            teacher.set_password('password123')
            teacher.save()
            self.stdout.write(f'Created teacher account: {teacher_email}')
        
        # Create course offerings for current semester
        courses_for_offerings = Course.objects.filter(
            code__in=['CS101', 'IT101', 'GE101', 'GE102', 'GE103', 'PE101', 'NSTP1']
        )
        
        for course in courses_for_offerings:
            # Create multiple sections for popular courses
            sections = ['A', 'B'] if course.course_type == 'general' else ['A']
            
            for section in sections:
                offering, created = CourseOffering.objects.get_or_create(
                    course=course,
                    semester=first_semester,
                    section=section,
                    defaults={
                        'instructor': teacher,
                        'max_students': random.randint(25, 40),
                        'schedule': f"MWF 10:00-11:30 AM",
                        'room': f"Room {random.randint(101, 205)}",
                        'status': 'open'
                    }
                )
                if created:
                    self.stdout.write(f'Created offering: {course.code} Section {section}')
        
        # Create sample student and assign curriculum
        student_email = 'student@spist.edu.ph'
        student, created = User.objects.get_or_create(
            email=student_email,
            defaults={
                'username': 'student1',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'user_type': 'student',
                'is_active': True
            }
        )
        if created:
            student.set_password('password123')
            student.save()
            self.stdout.write(f'Created student account: {student_email}')
        
        # Assign student to CS curriculum
        student_curriculum, created = StudentCurriculum.objects.get_or_create(
            student=student,
            curriculum=cs_curriculum,
            defaults={
                'year_started': academic_year.year_start,
                'current_year_level': 1,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Assigned student to curriculum: {cs_curriculum.name}')
        
        # Create sample enrollment codes for late enrollment
        from courses.models import EnrollmentCode
        sample_offerings = CourseOffering.objects.filter(course__code__in=['CS101', 'IT101'])
        
        for offering in sample_offerings:
            code_text = f"LATE{offering.course.code[-3:]}"  # e.g., LATE101
            enrollment_code, created = EnrollmentCode.objects.get_or_create(
                code=code_text,
                defaults={
                    'course_offering': offering,
                    'max_uses': 5,
                    'valid_from': timezone.now() - timedelta(days=1),
                    'valid_until': timezone.now() + timedelta(days=30),
                    'created_by': teacher,
                    'notes': f'Sample enrollment code for late enrollees in {offering.course.code}'
                }
            )
            if created:
                self.stdout.write(f'Created enrollment code: {code_text}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nSample data created successfully!\n'
                'Student login: student@spist.edu.ph / password123\n'
                'Teacher login: teacher@spist.edu.ph / password123\n'
                'Sample enrollment codes: LATE101 (for CS101), LATE101 (for IT101)'
            )
        )
