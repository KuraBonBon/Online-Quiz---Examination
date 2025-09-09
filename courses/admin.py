from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department, AcademicYear, Semester, Curriculum, Course, CurriculumCourse,
    CourseOffering, StudentEnrollment, StudentCurriculum, EnrollmentPeriod
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'head_of_department', 'course_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    list_editable = ['is_active']
    ordering = ['name']
    
    def course_count(self, obj):
        return obj.courses.filter(is_active=True).count()
    course_count.short_description = 'Active Courses'

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_current', 'semester_count']
    list_filter = ['is_current']
    ordering = ['-year_start']
    
    def semester_count(self, obj):
        return obj.semesters.count()
    semester_count.short_description = 'Semesters'

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'start_date', 'end_date', 'is_current', 'enrollment_periods_count']
    list_filter = ['is_current', 'semester', 'academic_year']
    ordering = ['-academic_year__year_start', 'semester']
    
    def enrollment_periods_count(self, obj):
        return obj.enrollment_periods.count()
    enrollment_periods_count.short_description = 'Enrollment Periods'

class CurriculumCourseInline(admin.TabularInline):
    model = CurriculumCourse
    extra = 0
    fields = ['course', 'year_level', 'semester', 'is_required']
    autocomplete_fields = ['course']

@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'year_introduced', 'total_units', 'course_count', 'student_count', 'is_active']
    list_filter = ['department', 'is_active', 'year_introduced']
    search_fields = ['code', 'name', 'description']
    list_editable = ['is_active']
    inlines = [CurriculumCourseInline]
    
    def course_count(self, obj):
        return obj.curriculum_courses.count()
    course_count.short_description = 'Courses'
    
    def student_count(self, obj):
        return obj.student_assignments.filter(is_active=True).count()
    student_count.short_description = 'Students'

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'department', 'units', 'course_type', 'prerequisite_count', 'offering_count', 'is_active']
    list_filter = ['department', 'course_type', 'units', 'is_active']
    search_fields = ['code', 'title', 'description']
    list_editable = ['is_active']
    filter_horizontal = ['prerequisites']
    
    def prerequisite_count(self, obj):
        return obj.prerequisites.count()
    prerequisite_count.short_description = 'Prerequisites'
    
    def offering_count(self, obj):
        return obj.offerings.count()
    offering_count.short_description = 'Offerings'

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ['course', 'section', 'semester', 'instructor', 'enrollment_info', 'status']
    list_filter = ['semester', 'status', 'course__department']
    search_fields = ['course__code', 'course__title', 'section', 'instructor__first_name', 'instructor__last_name']
    list_editable = ['status']
    autocomplete_fields = ['course', 'instructor']
    
    def enrollment_info(self, obj):
        enrolled = obj.enrolled_count
        total = obj.max_students
        percentage = (enrolled / total * 100) if total > 0 else 0
        
        color = 'green' if percentage < 80 else 'orange' if percentage < 100 else 'red'
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color, enrolled, total, int(percentage)
        )
    enrollment_info.short_description = 'Enrollment'

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'course_info', 'status', 'enrollment_type', 'grade_display', 'enrolled_at']
    list_filter = ['status', 'enrollment_type', 'course_offering__semester', 'course_offering__course__department']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_profile__student_id', 'course_offering__course__code']
    list_editable = ['status']
    autocomplete_fields = ['student', 'course_offering']
    
    def student_name(self, obj):
        profile = getattr(obj.student, 'student_profile', None)
        student_id = profile.student_id if profile else 'N/A'
        return f"{obj.student.get_full_name()} ({student_id})"
    student_name.short_description = 'Student'
    
    def course_info(self, obj):
        return f"{obj.course_offering.course.code} - {obj.course_offering.section}"
    course_info.short_description = 'Course'
    
    def grade_display(self, obj):
        if obj.final_grade:
            return f"Final: {obj.final_grade}"
        elif obj.midterm_grade:
            return f"Midterm: {obj.midterm_grade}"
        return "No grades"
    grade_display.short_description = 'Grades'

@admin.register(StudentCurriculum)
class StudentCurriculumAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'curriculum', 'year_started', 'current_year_level', 'is_active', 'assigned_at']
    list_filter = ['curriculum', 'current_year_level', 'is_active', 'year_started']
    search_fields = ['student__first_name', 'student__last_name', 'student__student_profile__student_id', 'curriculum__code']
    list_editable = ['current_year_level', 'is_active']
    autocomplete_fields = ['student', 'curriculum']
    
    def student_name(self, obj):
        profile = getattr(obj.student, 'student_profile', None)
        student_id = profile.student_id if profile else 'N/A'
        return f"{obj.student.get_full_name()} ({student_id})"
    student_name.short_description = 'Student'

@admin.register(EnrollmentPeriod)
class EnrollmentPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'semester', 'student_category', 'year_levels', 'period_display', 'is_open_now', 'is_active', 'priority_order']
    list_filter = ['semester', 'student_category', 'is_active']
    search_fields = ['name']
    list_editable = ['priority_order', 'is_active']
    
    def period_display(self, obj):
        return f"{obj.start_date.strftime('%m/%d/%Y %H:%M')} - {obj.end_date.strftime('%m/%d/%Y %H:%M')}"
    period_display.short_description = 'Period'
    
    def is_open_now(self, obj):
        is_open = obj.is_open()
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if is_open else 'red',
            'Open' if is_open else 'Closed'
        )
    is_open_now.short_description = 'Status'

# Custom admin actions
@admin.action(description='Approve selected enrollments')
def approve_enrollments(modeladmin, request, queryset):
    updated = queryset.filter(status='pending').update(status='enrolled', approved_by=request.user)
    modeladmin.message_user(request, f'{updated} enrollments were approved.')

@admin.action(description='Mark as current semester')
def mark_current_semester(modeladmin, request, queryset):
    if queryset.count() == 1:
        semester = queryset.first()
        Semester.objects.filter(is_current=True).update(is_current=False)
        semester.is_current = True
        semester.save()
        modeladmin.message_user(request, f'{semester} is now the current semester.')
    else:
        modeladmin.message_user(request, 'Please select exactly one semester.', level='ERROR')

# Add actions to admin classes
StudentEnrollmentAdmin.actions = [approve_enrollments]
SemesterAdmin.actions = [mark_current_semester]
