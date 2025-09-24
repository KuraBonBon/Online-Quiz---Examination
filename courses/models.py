from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class Department(models.Model):
    """Academic departments"""
    code = models.CharField(max_length=10, unique=True, help_text="e.g., CS, IT, ENG")
    name = models.CharField(max_length=100, help_text="e.g., Computer Science")
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'teacher'},
        related_name='headed_departments'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class AcademicYear(models.Model):
    """Academic year management"""
    year_start = models.IntegerField(help_text="e.g., 2024 for 2024-2025")
    year_end = models.IntegerField(help_text="e.g., 2025 for 2024-2025")
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['year_start', 'year_end']
        ordering = ['-year_start']
    
    def __str__(self):
        return f"{self.year_start}-{self.year_end}"
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Only one academic year can be current
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

class Semester(models.Model):
    """Semester management"""
    SEMESTER_CHOICES = (
        ('1st', '1st Semester'),
        ('2nd', '2nd Semester'),
        ('summer', 'Summer'),
    )
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['academic_year', 'semester']
        ordering = ['academic_year', 'semester']
    
    def __str__(self):
        return f"{self.academic_year} - {self.get_semester_display()}"
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Only one semester can be current
            Semester.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

class Curriculum(models.Model):
    """Curriculum templates for different programs"""
    code = models.CharField(max_length=20, unique=True, help_text="e.g., BSCS2024, BSIT2023")
    name = models.CharField(max_length=100, help_text="e.g., Bachelor of Science in Computer Science")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='curricula')
    year_introduced = models.IntegerField()
    total_units = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['department', '-year_introduced', 'name']
        verbose_name_plural = "Curricula"
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Course(models.Model):
    """Individual courses/subjects"""
    code = models.CharField(max_length=20, unique=True, help_text="e.g., CS101, MATH101")
    title = models.CharField(max_length=200, help_text="e.g., Introduction to Programming")
    description = models.TextField(blank=True)
    units = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='prerequisite_for')
    
    # Course type
    COURSE_TYPE_CHOICES = (
        ('core', 'Core/Major'),
        ('general', 'General Education'), 
        ('elective', 'Elective'),
        ('practicum', 'Practicum/OJT'),
        ('thesis', 'Thesis/Capstone'),
    )
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, default='core')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.title}"

class CurriculumCourse(models.Model):
    """Courses within a specific curriculum with year/semester placement"""
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='curriculum_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='in_curricula')
    
    YEAR_LEVEL_CHOICES = (
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
        (5, '5th Year'),
    )
    
    SEMESTER_CHOICES = (
        ('1st', '1st Semester'),
        ('2nd', '2nd Semester'),
        ('summer', 'Summer'),
    )
    
    year_level = models.IntegerField(choices=YEAR_LEVEL_CHOICES)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    is_required = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['curriculum', 'course']
        ordering = ['year_level', 'semester', 'course__code']
    
    def __str__(self):
        return f"{self.curriculum.code} - {self.course.code} (Y{self.year_level} {self.semester})"

class CourseOffering(models.Model):
    """Specific course offerings for a semester"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='course_offerings')
    section = models.CharField(max_length=10, help_text="e.g., A, B, C, 1A, 2B")
    instructor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'teacher'},
        related_name='taught_courses'
    )
    
    # Schedule details
    schedule = models.TextField(help_text="e.g., MWF 9:00-10:00 AM, TTh 1:00-2:30 PM")
    room = models.CharField(max_length=50, blank=True, help_text="e.g., Room 301, Lab A")
    
    # Enrollment limits
    max_students = models.PositiveIntegerField(default=40)
    
    # Status
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('open', 'Open for Enrollment'),
        ('closed', 'Enrollment Closed'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    # Important dates
    enrollment_start = models.DateTimeField(null=True, blank=True)
    enrollment_end = models.DateTimeField(null=True, blank=True)
    class_start = models.DateField(null=True, blank=True)
    class_end = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'semester', 'section']
        ordering = ['semester', 'course__code', 'section']
    
    def __str__(self):
        return f"{self.course.code} - {self.section} ({self.semester})"
    
    @property
    def enrolled_count(self):
        return self.enrollments.filter(status='enrolled').count()
    
    @property
    def available_slots(self):
        return self.max_students - self.enrolled_count
    
    @property
    def is_full(self):
        return self.enrolled_count >= self.max_students

class StudentEnrollment(models.Model):
    """Student enrollment in courses"""
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'student'},
        related_name='enrollments'
    )
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment details
    ENROLLMENT_STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('enrolled', 'Enrolled'),
        ('waitlisted', 'Waitlisted'),
        ('dropped', 'Dropped'),
        ('failed', 'Failed'),
        ('passed', 'Passed'),
        ('incomplete', 'Incomplete'),
    )
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS_CHOICES, default='pending')
    
    ENROLLMENT_TYPE_CHOICES = (
        ('regular', 'Regular Enrollment'),
        ('late', 'Late Enrollment'),
        ('cross_enrollment', 'Cross Enrollment'),
        ('makeup', 'Make-up Class'),
        ('overload', 'Overload'),
    )
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_TYPE_CHOICES, default='regular')
    
    # Grades
    midterm_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Important dates
    enrolled_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_enrollments',
        limit_choices_to={'user_type__in': ['teacher', 'admin']}
    )
    
    class Meta:
        unique_together = ['student', 'course_offering']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course_offering}"
    
    def clean(self):
        # Check prerequisites
        if self.status == 'enrolled':
            student_profile = getattr(self.student, 'student_profile', None)
            if student_profile:
                # Get passed courses
                passed_courses = StudentEnrollment.objects.filter(
                    student=self.student,
                    status='passed'
                ).values_list('course_offering__course', flat=True)
                
                # Check if prerequisites are met
                missing_prereqs = self.course_offering.course.prerequisites.exclude(
                    id__in=passed_courses
                )
                
                if missing_prereqs.exists():
                    raise ValidationError(
                        f"Missing prerequisites: {', '.join(missing_prereqs.values_list('code', flat=True))}"
                    )

class StudentCurriculum(models.Model):
    """Student assignment to curriculum (for automatic enrollment)"""
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'student'},
        related_name='curriculum_assignments'
    )
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='student_assignments')
    year_started = models.IntegerField()
    current_year_level = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='curriculum_assignments_made',
        limit_choices_to={'is_staff': True}
    )
    
    class Meta:
        unique_together = ['student', 'curriculum']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.curriculum.code}"

class EnrollmentPeriod(models.Model):
    """Enrollment periods for different student categories"""
    name = models.CharField(max_length=100, help_text="e.g., Regular Enrollment, Late Enrollment")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollment_periods')
    
    # Student categories
    STUDENT_CATEGORY_CHOICES = (
        ('all', 'All Students'),
        ('regular', 'Regular Students'),
        ('irregular', 'Irregular Students'),
        ('transferee', 'Transferees'),
        ('new', 'New Students'),
        ('senior', 'Senior Students'),
    )
    student_category = models.CharField(max_length=20, choices=STUDENT_CATEGORY_CHOICES, default='all')
    
    # Year levels affected
    year_levels = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Comma-separated year levels: 1,2,3,4 or leave blank for all"
    )
    
    # Period dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    priority_order = models.PositiveIntegerField(default=1, help_text="Lower numbers have higher priority")
    
    class Meta:
        ordering = ['semester', 'priority_order', 'start_date']
    
    def __str__(self):
        return f"{self.name} - {self.semester}"
    
    def is_open(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


class EnrollmentCode(models.Model):
    """Enrollment codes for late enrollees and transferees"""
    code = models.CharField(max_length=20, unique=True, help_text="Unique enrollment code")
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='enrollment_codes')
    
    # Code settings
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(default=1, help_text="Maximum number of times this code can be used")
    used_count = models.PositiveIntegerField(default=0)
    
    # Validity period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Created by (registrar/teacher)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_enrollment_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Usage tracking
    used_by = models.ManyToManyField(User, through='EnrollmentCodeUsage', related_name='used_enrollment_codes')
    
    # Notes
    notes = models.TextField(blank=True, help_text="Internal notes about this code")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.course_offering}"
    
    def is_valid(self):
        """Check if code is valid for use"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_until and
            self.used_count < self.max_uses
        )
    
    def can_be_used_by(self, user):
        """Check if code can be used by specific user"""
        if not self.is_valid():
            return False, "Enrollment code is not valid or has expired"
        
        # Check if user already used this code
        if EnrollmentCodeUsage.objects.filter(code=self, user=user).exists():
            return False, "You have already used this enrollment code"
        
        # Check if user is already enrolled
        if StudentEnrollment.objects.filter(
            student=user, 
            course_offering=self.course_offering
        ).exists():
            return False, "You are already enrolled in this course"
        
        return True, "Code is valid"


class EnrollmentCodeUsage(models.Model):
    """Track enrollment code usage"""
    code = models.ForeignKey(EnrollmentCode, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enrollment = models.OneToOneField(StudentEnrollment, on_delete=models.CASCADE, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['code', 'user']
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.code.code} used by {self.user.get_full_name()} at {self.used_at}"
