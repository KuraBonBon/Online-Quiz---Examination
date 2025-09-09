from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date
from courses.models import (
    Department, AcademicYear, Semester, Curriculum, Course, CurriculumCourse,
    CourseOffering, StudentCurriculum
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample course management data for SPIST'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample course management data...'))

        # Create Departments
        departments_data = [
            {'code': 'CS', 'name': 'Computer Science', 'description': 'Department of Computer Science'},
            {'code': 'IT', 'name': 'Information Technology', 'description': 'Department of Information Technology'},
            {'code': 'ENG', 'name': 'Engineering', 'description': 'Department of Engineering'},
            {'code': 'MATH', 'name': 'Mathematics', 'description': 'Department of Mathematics'},
            {'code': 'GE', 'name': 'General Education', 'description': 'General Education Department'},
        ]

        departments = {}
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            departments[dept.code] = dept
            if created:
                self.stdout.write(f'Created department: {dept}')

        # Create Academic Year and Semester
        academic_year, created = AcademicYear.objects.get_or_create(
            year_start=2024,
            year_end=2025,
            defaults={'is_current': True}
        )
        if created:
            self.stdout.write(f'Created academic year: {academic_year}')

        semester1, created = Semester.objects.get_or_create(
            academic_year=academic_year,
            semester='1st',
            defaults={
                'start_date': date(2024, 8, 15),
                'end_date': date(2024, 12, 15),
                'is_current': True
            }
        )
        if created:
            self.stdout.write(f'Created semester: {semester1}')
        
        semester2, created = Semester.objects.get_or_create(
            academic_year=academic_year,
            semester='2nd',
            defaults={
                'start_date': date(2025, 1, 15),
                'end_date': date(2025, 5, 15),
                'is_current': False
            }
        )
        if created:
            self.stdout.write(f'Created semester: {semester2}')

        # Create Courses
        courses_data = [
            # Computer Science Courses
            {'code': 'CS101', 'title': 'Introduction to Programming', 'units': 3, 'department': 'CS', 'course_type': 'core'},
            {'code': 'CS102', 'title': 'Object-Oriented Programming', 'units': 3, 'department': 'CS', 'course_type': 'core'},
            {'code': 'CS201', 'title': 'Data Structures and Algorithms', 'units': 3, 'department': 'CS', 'course_type': 'core'},
            {'code': 'CS301', 'title': 'Database Systems', 'units': 3, 'department': 'CS', 'course_type': 'core'},
            {'code': 'CS401', 'title': 'Software Engineering', 'units': 3, 'department': 'CS', 'course_type': 'core'},
            
            # Information Technology Courses
            {'code': 'IT101', 'title': 'Introduction to Information Technology', 'units': 3, 'department': 'IT', 'course_type': 'core'},
            {'code': 'IT201', 'title': 'Web Development', 'units': 3, 'department': 'IT', 'course_type': 'core'},
            {'code': 'IT301', 'title': 'Network Administration', 'units': 3, 'department': 'IT', 'course_type': 'core'},
            
            # Mathematics Courses
            {'code': 'MATH101', 'title': 'College Algebra', 'units': 3, 'department': 'MATH', 'course_type': 'general'},
            {'code': 'MATH102', 'title': 'Trigonometry', 'units': 3, 'department': 'MATH', 'course_type': 'general'},
            {'code': 'MATH201', 'title': 'Calculus I', 'units': 3, 'department': 'MATH', 'course_type': 'general'},
            {'code': 'MATH202', 'title': 'Calculus II', 'units': 3, 'department': 'MATH', 'course_type': 'general'},
            
            # General Education Courses
            {'code': 'GE101', 'title': 'English Communication', 'units': 3, 'department': 'GE', 'course_type': 'general'},
            {'code': 'GE102', 'title': 'Filipino Communication', 'units': 3, 'department': 'GE', 'course_type': 'general'},
            {'code': 'GE201', 'title': 'Philippine History', 'units': 3, 'department': 'GE', 'course_type': 'general'},
            {'code': 'PE101', 'title': 'Physical Education 1', 'units': 2, 'department': 'GE', 'course_type': 'general'},
        ]

        courses = {}
        for course_data in courses_data:
            dept_code = course_data.pop('department')
            course_data['department'] = departments[dept_code]
            
            course, created = Course.objects.get_or_create(
                code=course_data['code'],
                defaults=course_data
            )
            courses[course.code] = course
            if created:
                self.stdout.write(f'Created course: {course}')

        # Set up prerequisites
        prerequisites = [
            ('CS102', ['CS101']),
            ('CS201', ['CS102']),
            ('CS301', ['CS201']),
            ('CS401', ['CS301']),
            ('MATH201', ['MATH101', 'MATH102']),
            ('MATH202', ['MATH201']),
        ]

        for course_code, prereq_codes in prerequisites:
            if course_code in courses:
                course = courses[course_code]
                for prereq_code in prereq_codes:
                    if prereq_code in courses:
                        course.prerequisites.add(courses[prereq_code])

        # Create Curricula
        curricula_data = [
            {
                'code': 'BSCS2024',
                'name': 'Bachelor of Science in Computer Science',
                'department': departments['CS'],
                'year_introduced': 2024,
                'total_units': 120
            },
            {
                'code': 'BSIT2024',
                'name': 'Bachelor of Science in Information Technology',
                'department': departments['IT'],
                'year_introduced': 2024,
                'total_units': 120
            }
        ]

        curricula = {}
        for curriculum_data in curricula_data:
            curriculum, created = Curriculum.objects.get_or_create(
                code=curriculum_data['code'],
                defaults=curriculum_data
            )
            curricula[curriculum.code] = curriculum
            if created:
                self.stdout.write(f'Created curriculum: {curriculum}')

        # Create Curriculum Course mappings for BSCS
        bscs_courses = [
            # 1st Year, 1st Semester
            ('GE101', 1, '1st'), ('MATH101', 1, '1st'), ('CS101', 1, '1st'), ('PE101', 1, '1st'),
            # 1st Year, 2nd Semester
            ('GE102', 1, '2nd'), ('MATH102', 1, '2nd'), ('CS102', 1, '2nd'),
            # 2nd Year, 1st Semester
            ('GE201', 2, '1st'), ('MATH201', 2, '1st'), ('CS201', 2, '1st'),
            # 2nd Year, 2nd Semester
            ('MATH202', 2, '2nd'), ('CS301', 2, '2nd'),
            # 3rd Year, 1st Semester
            ('CS401', 3, '1st'),
        ]

        bscs_curriculum = curricula['BSCS2024']
        for course_code, year_level, semester in bscs_courses:
            if course_code in courses:
                CurriculumCourse.objects.get_or_create(
                    curriculum=bscs_curriculum,
                    course=courses[course_code],
                    defaults={
                        'year_level': year_level,
                        'semester': semester,
                        'is_required': True
                    }
                )

        # Create BSIT curriculum courses
        bsit_courses = [
            # 1st Year, 1st Semester
            ('GE101', 1, '1st'), ('MATH101', 1, '1st'), ('IT101', 1, '1st'), ('PE101', 1, '1st'),
            # 1st Year, 2nd Semester
            ('GE102', 1, '2nd'), ('MATH102', 1, '2nd'), ('CS101', 1, '2nd'),
            # 2nd Year, 1st Semester
            ('GE201', 2, '1st'), ('MATH201', 2, '1st'), ('IT201', 2, '1st'),
            # 2nd Year, 2nd Semester
            ('CS102', 2, '2nd'), ('IT301', 2, '2nd'),
        ]

        bsit_curriculum = curricula['BSIT2024']
        for course_code, year_level, semester in bsit_courses:
            if course_code in courses:
                CurriculumCourse.objects.get_or_create(
                    curriculum=bsit_curriculum,
                    course=courses[course_code],
                    defaults={
                        'year_level': year_level,
                        'semester': semester,
                        'is_required': True
                    }
                )

        # Create Course Offerings for current semester
        sample_offerings = [
            ('CS101', 'A'), ('CS101', 'B'), ('CS102', 'A'),
            ('GE101', 'A'), ('GE101', 'B'), ('MATH101', 'A'),
            ('IT101', 'A'), ('PE101', 'A'),
        ]

        teachers = User.objects.filter(user_type='teacher')
        
        for course_code, section in sample_offerings:
            if course_code in courses:
                instructor = teachers.first() if teachers.exists() else None
                
                CourseOffering.objects.get_or_create(
                    course=courses[course_code],
                    semester=semester1,  # Use semester1 object instead of semester
                    section=section,
                    defaults={
                        'instructor': instructor,
                        'schedule': 'MWF 9:00-10:00 AM',
                        'room': f'Room {section}01',
                        'max_students': 40,
                        'status': 'open',
                        'enrollment_start': timezone.now(),
                        'enrollment_end': timezone.now().replace(month=12, day=1),
                        'class_start': date(2024, 8, 15),
                        'class_end': date(2024, 12, 15),
                    }
                )

        # Assign students to curricula
        students = User.objects.filter(user_type='student')
        if students.exists():
            for i, student in enumerate(students[:10]):  # Assign first 10 students
                curriculum = bscs_curriculum if i % 2 == 0 else bsit_curriculum
                
                StudentCurriculum.objects.get_or_create(
                    student=student,
                    curriculum=curriculum,
                    defaults={
                        'year_started': 2024,
                        'current_year_level': 1,
                        'is_active': True
                    }
                )

        self.stdout.write(self.style.SUCCESS('Sample course management data created successfully!'))
        self.stdout.write(
            self.style.WARNING(
                'You can now:\n'
                '1. Visit /courses/ to access the course management dashboard\n'
                '2. Use the admin panel to modify course data\n'
                '3. Test student enrollment functionality\n'
                '4. Create course offerings for different semesters'
            )
        )
