from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
import csv

from .models import (
    Department, AcademicYear, Semester, Curriculum, Course, CurriculumCourse,
    CourseOffering, StudentEnrollment, StudentCurriculum, EnrollmentPeriod
)
from .forms import (
    DepartmentForm, CourseForm, CurriculumForm, CourseOfferingForm,
    StudentEnrollmentForm, BulkEnrollmentForm, CourseSearchForm,
    StudentEnrollmentSearchForm, CurriculumCourseFormSet
)

User = get_user_model()

def is_admin_or_teacher(user):
    """Check if user is admin or teacher"""
    return user.is_authenticated and (user.is_staff or user.user_type == 'teacher')

def is_student(user):
    """Check if user is student"""
    return user.is_authenticated and user.user_type == 'student'

@login_required
def course_management_dashboard(request):
    """Main dashboard for course management"""
    if not (request.user.is_staff or request.user.user_type == 'teacher'):
        messages.error(request, 'Access denied. Only teachers and administrators can access course management.')
        return redirect('teacher_dashboard' if request.user.user_type == 'teacher' else 'student_dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Dashboard statistics
    stats = {
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_students': User.objects.filter(user_type='student').count(),
        'current_enrollments': StudentEnrollment.objects.filter(
            course_offering__semester=current_semester,
            status='enrolled'
        ).count() if current_semester else 0,
        'active_offerings': CourseOffering.objects.filter(
            semester=current_semester,
            status__in=['open', 'ongoing']
        ).count() if current_semester else 0,
    }
    
    # Recent enrollments
    recent_enrollments = StudentEnrollment.objects.select_related(
        'student', 'course_offering__course', 'course_offering__semester'
    ).filter(
        course_offering__semester=current_semester
    ).order_by('-enrolled_at')[:10] if current_semester else []
    
    context = {
        'stats': stats,
        'current_semester': current_semester,
        'recent_enrollments': recent_enrollments,
    }
    
    return render(request, 'courses/dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def course_list_view(request):
    """List all courses with search and filter"""
    form = CourseSearchForm(request.GET)
    courses = Course.objects.select_related('department').annotate(
        offering_count=Count('offerings')
    )
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        department = form.cleaned_data.get('department')
        course_type = form.cleaned_data.get('course_type')
        units = form.cleaned_data.get('units')
        
        if search:
            courses = courses.filter(
                Q(code__icontains=search) | Q(title__icontains=search)
            )
        if department:
            courses = courses.filter(department=department)
        if course_type:
            courses = courses.filter(course_type=course_type)
        if units:
            courses = courses.filter(units=units)
    
    # Add ordering to fix pagination warning
    courses = courses.order_by('code')
    
    # Pagination
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'courses': page_obj,
    }
    
    return render(request, 'courses/course_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def course_create_view(request):
    """Create new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course}" created successfully!')
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = CourseForm()
    
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Create Course'})

@login_required
@user_passes_test(is_admin_or_teacher)
def course_detail_view(request, course_id):
    """Course detail with offerings and curriculum info"""
    course = get_object_or_404(Course, id=course_id)
    
    # Get current and upcoming offerings
    current_semester = Semester.objects.filter(is_current=True).first()
    offerings = CourseOffering.objects.filter(course=course).select_related(
        'semester__academic_year', 'instructor'
    ).order_by('-semester__academic_year__year_start', 'semester__semester', 'section')
    
    # Get curriculum associations
    curriculum_courses = CurriculumCourse.objects.filter(course=course).select_related(
        'curriculum'
    ).order_by('curriculum__code', 'year_level', 'semester')
    
    context = {
        'course': course,
        'offerings': offerings,
        'curriculum_courses': curriculum_courses,
        'current_semester': current_semester,
    }
    
    return render(request, 'courses/course_detail.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def curriculum_list_view(request):
    """List all curricula"""
    curricula = Curriculum.objects.select_related('department').annotate(
        course_count=Count('curriculum_courses'),
        student_count=Count('student_assignments', filter=Q(student_assignments__is_active=True))
    ).filter(is_active=True)
    
    context = {'curricula': curricula}
    return render(request, 'courses/curriculum_list.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def curriculum_detail_view(request, curriculum_id):
    """Curriculum detail with course mappings"""
    curriculum = get_object_or_404(Curriculum, id=curriculum_id)
    
    # Get courses organized by year and semester
    curriculum_courses = CurriculumCourse.objects.filter(
        curriculum=curriculum
    ).select_related('course').order_by('year_level', 'semester', 'course__code')
    
    # Organize by year and semester
    organized_courses = {}
    for cc in curriculum_courses:
        year = cc.year_level
        semester = cc.semester
        
        if year not in organized_courses:
            organized_courses[year] = {}
        if semester not in organized_courses[year]:
            organized_courses[year][semester] = []
        
        organized_courses[year][semester].append(cc)
    
    context = {
        'curriculum': curriculum,
        'organized_courses': organized_courses,
    }
    
    return render(request, 'courses/curriculum_detail.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def course_offering_list_view(request):
    """List course offerings for current semester"""
    current_semester = Semester.objects.filter(is_current=True).first()
    
    offerings = CourseOffering.objects.filter(
        semester=current_semester
    ).select_related(
        'course', 'instructor', 'semester'
    ).annotate(
        current_enrollment=Count('enrollments', filter=Q(enrollments__status='enrolled'))
    ).order_by('course__code', 'section') if current_semester else CourseOffering.objects.none()
    
    # Calculate statistics
    open_offerings_count = offerings.filter(status='open').count()
    total_enrollments = StudentEnrollment.objects.filter(
        course_offering__semester=current_semester,
        status='enrolled'
    ).count() if current_semester else 0
    my_offerings_count = offerings.filter(instructor=request.user).count()
    
    context = {
        'offerings': offerings,
        'current_semester': current_semester,
        'open_offerings_count': open_offerings_count,
        'total_enrollments': total_enrollments,
        'my_offerings_count': my_offerings_count,
    }
    
    return render(request, 'courses/course_offerings.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def create_course_offering_view(request):
    """Create new course offering"""
    if request.method == 'POST':
        form = CourseOfferingForm(request.POST)
        if form.is_valid():
            offering = form.save()
            messages.success(request, f'Course offering "{offering}" created successfully!')
            return redirect('courses:offering_list')
    else:
        form = CourseOfferingForm()
        # Set default semester to current
        current_semester = Semester.objects.filter(is_current=True).first()
        if current_semester:
            form.fields['semester'].initial = current_semester
    
    return render(request, 'courses/course_offering_form.html', {'form': form, 'title': 'Create Course Offering'})

@login_required
@user_passes_test(is_admin_or_teacher)
def enrollment_management_view(request):
    """Manage student enrollments"""
    form = StudentEnrollmentSearchForm(request.GET)
    enrollments = StudentEnrollment.objects.select_related(
        'student', 'course_offering__course', 'course_offering__semester'
    )
    
    # Get current semester enrollments by default
    current_semester = Semester.objects.filter(is_current=True).first()
    if current_semester:
        enrollments = enrollments.filter(course_offering__semester=current_semester)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        course_offering = form.cleaned_data.get('course_offering')
        status = form.cleaned_data.get('status')
        enrollment_type = form.cleaned_data.get('enrollment_type')
        
        if search:
            enrollments = enrollments.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(student__student_profile__student_id__icontains=search)
            )
        if course_offering:
            enrollments = enrollments.filter(course_offering=course_offering)
        if status:
            enrollments = enrollments.filter(status=status)
        if enrollment_type:
            enrollments = enrollments.filter(enrollment_type=enrollment_type)
    
    # Pagination
    paginator = Paginator(enrollments.order_by('-enrolled_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'enrollments': page_obj,
        'current_semester': current_semester,
    }
    
    return render(request, 'courses/enrollment_management.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def bulk_enrollment_view(request):
    """Bulk enrollment based on curriculum"""
    if request.method == 'POST':
        form = BulkEnrollmentForm(request.POST)
        if form.is_valid():
            curriculum = form.cleaned_data['curriculum']
            semester = form.cleaned_data['semester']
            year_level = form.cleaned_data['year_level']
            semester_filter = form.cleaned_data['semester_filter']
            enrollment_type = form.cleaned_data['enrollment_type']
            
            # Get students assigned to this curriculum at the specified year level
            student_curricula = StudentCurriculum.objects.filter(
                curriculum=curriculum,
                current_year_level=year_level,
                is_active=True
            ).select_related('student')
            
            # Get courses for this curriculum year/semester
            curriculum_courses = CurriculumCourse.objects.filter(
                curriculum=curriculum,
                year_level=year_level,
                semester=semester_filter,
                is_required=True
            ).select_related('course')
            
            enrolled_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                for student_curriculum in student_curricula:
                    student = student_curriculum.student
                    
                    for curriculum_course in curriculum_courses:
                        # Check if course offering exists
                        try:
                            course_offering = CourseOffering.objects.get(
                                course=curriculum_course.course,
                                semester=semester,
                                status__in=['open', 'planning']
                            )
                            
                            # Check if already enrolled
                            if not StudentEnrollment.objects.filter(
                                student=student,
                                course_offering=course_offering
                            ).exists():
                                # Create enrollment
                                StudentEnrollment.objects.create(
                                    student=student,
                                    course_offering=course_offering,
                                    enrollment_type=enrollment_type,
                                    status='pending',
                                    approved_by=request.user
                                )
                                enrolled_count += 1
                            else:
                                skipped_count += 1
                        
                        except CourseOffering.DoesNotExist:
                            skipped_count += 1
                            continue
            
            messages.success(request, 
                f'Bulk enrollment completed! {enrolled_count} enrollments created, {skipped_count} skipped.')
            return redirect('courses:enrollment_management')
    else:
        form = BulkEnrollmentForm()
    
    return render(request, 'courses/bulk_enrollment.html', {'form': form})

@login_required
def student_enrollment_view(request):
    """Student's own enrollment view"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get student's current enrollments
    current_enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        course_offering__semester=current_semester
    ).select_related('course_offering__course') if current_semester else []
    
    # Get enrollment history
    enrollment_history = StudentEnrollment.objects.filter(
        student=request.user
    ).select_related(
        'course_offering__course', 'course_offering__semester__academic_year'
    ).order_by('-course_offering__semester__academic_year__year_start', 'course_offering__course__code')
    
    # Get student's curriculum
    student_curriculum = StudentCurriculum.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('curriculum').first()
    
    # Get recommended courses (if curriculum assigned)
    recommended_courses = []
    if student_curriculum:
        curriculum_courses = CurriculumCourse.objects.filter(
            curriculum=student_curriculum.curriculum,
            year_level=student_curriculum.current_year_level
        ).select_related('course')
        
        # Get available offerings for recommended courses
        for cc in curriculum_courses:
            offerings = CourseOffering.objects.filter(
                course=cc.course,
                semester=current_semester,
                status='open'
            ) if current_semester else []
            
            for offering in offerings:
                # Check if already enrolled
                if not StudentEnrollment.objects.filter(
                    student=request.user,
                    course_offering=offering
                ).exists():
                    recommended_courses.append({
                        'curriculum_course': cc,
                        'offering': offering
                    })
    
    context = {
        'current_semester': current_semester,
        'current_enrollments': current_enrollments,
        'enrollment_history': enrollment_history,
        'student_curriculum': student_curriculum,
        'recommended_courses': recommended_courses,
    }
    
    return render(request, 'courses/student_enrollment.html', context)

@login_required
def enroll_in_course_view(request, offering_id):
    """Enroll student in a course"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied.')
        return redirect('teacher_dashboard')
    
    offering = get_object_or_404(CourseOffering, id=offering_id)
    
    # Check if enrollment is open
    if offering.status != 'open':
        messages.error(request, 'Enrollment is not open for this course.')
        return redirect('courses:student_enrollment')
    
    # Check if already enrolled
    if StudentEnrollment.objects.filter(student=request.user, course_offering=offering).exists():
        messages.warning(request, 'You are already enrolled in this course.')
        return redirect('courses:student_enrollment')
    
    # Check if course is full
    if offering.is_full:
        messages.error(request, 'This course is full.')
        return redirect('courses:student_enrollment')
    
    if request.method == 'POST':
        # Create enrollment
        enrollment = StudentEnrollment.objects.create(
            student=request.user,
            course_offering=offering,
            enrollment_type='regular',
            status='pending'
        )
        
        messages.success(request, f'Successfully enrolled in {offering.course.code}! Waiting for approval.')
        return redirect('courses:student_enrollment')
    
    context = {'offering': offering}
    return render(request, 'courses/enroll_confirmation.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def approve_enrollment_view(request, enrollment_id):
    """Approve student enrollment"""
    enrollment = get_object_or_404(StudentEnrollment, id=enrollment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            enrollment.status = 'enrolled'
            enrollment.approved_by = request.user
            enrollment.approved_at = timezone.now()
            enrollment.save()
            messages.success(request, f'Enrollment approved for {enrollment.student.get_full_name()}')
        
        elif action == 'reject':
            enrollment.status = 'dropped'
            enrollment.save()
            messages.warning(request, f'Enrollment rejected for {enrollment.student.get_full_name()}')
    
    return redirect('courses:enrollment_management')

@login_required
@user_passes_test(is_admin_or_teacher)
def export_enrollments_csv(request):
    """Export enrollments to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="enrollments.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 'Student ID', 'Course Code', 'Course Title', 
        'Section', 'Semester', 'Status', 'Enrollment Type', 'Enrolled At'
    ])
    
    current_semester = Semester.objects.filter(is_current=True).first()
    enrollments = StudentEnrollment.objects.filter(
        course_offering__semester=current_semester
    ).select_related(
        'student__student_profile', 'course_offering__course', 'course_offering__semester'
    ) if current_semester else []
    
    for enrollment in enrollments:
        profile = getattr(enrollment.student, 'student_profile', None)
        student_id = profile.student_id if profile else 'N/A'
        
        writer.writerow([
            enrollment.student.get_full_name(),
            student_id,
            enrollment.course_offering.course.code,
            enrollment.course_offering.course.title,
            enrollment.course_offering.section,
            str(enrollment.course_offering.semester),
            enrollment.get_status_display(),
            enrollment.get_enrollment_type_display(),
            enrollment.enrolled_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

@login_required
@user_passes_test(is_admin_or_teacher)
def offering_detail_view(request, offering_id):
    """View detailed information about a course offering"""
    offering = get_object_or_404(
        CourseOffering.objects.select_related('course', 'semester', 'instructor'),
        id=offering_id
    )
    
    # Check permissions - only instructor or admin can view
    if not (request.user.is_staff or offering.instructor == request.user):
        messages.error(request, 'You do not have permission to view this offering.')
        return redirect('courses:course_offerings')
    
    # Get enrolled students
    enrollments = StudentEnrollment.objects.filter(
        course_offering=offering
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    # Statistics
    enrollment_stats = {
        'total_enrolled': enrollments.filter(status='enrolled').count(),
        'pending_approvals': enrollments.filter(status='pending').count(),
        'dropped_students': enrollments.filter(status='dropped').count(),
        'completion_rate': 0,
    }
    
    if enrollments.exists():
        completed = enrollments.filter(status='completed').count()
        enrollment_stats['completion_rate'] = (completed / enrollments.count()) * 100
    
    context = {
        'offering': offering,
        'enrollments': enrollments,
        'enrollment_stats': enrollment_stats,
    }
    
    return render(request, 'courses/offering_detail.html', context)

@login_required
@user_passes_test(is_admin_or_teacher)
def class_list_view(request, offering_id):
    """View class list for a course offering"""
    offering = get_object_or_404(
        CourseOffering.objects.select_related('course', 'semester', 'instructor'),
        id=offering_id
    )
    
    # Check permissions - only instructor or admin can view
    if not (request.user.is_staff or offering.instructor == request.user):
        messages.error(request, 'You do not have permission to view this class list.')
        return redirect('courses:course_offerings')
    
    # Get enrolled students
    enrollments = StudentEnrollment.objects.filter(
        course_offering=offering,
        status='enrolled'
    ).select_related('student').order_by('student__last_name', 'student__first_name')
    
    # Handle export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{offering.course.code}_{offering.section}_class_list.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student ID', 'Last Name', 'First Name', 'Email', 
            'Enrollment Date', 'Status'
        ])
        
        for enrollment in enrollments:
            writer.writerow([
                enrollment.student.username,
                enrollment.student.last_name,
                enrollment.student.first_name,
                enrollment.student.email,
                enrollment.enrollment_date.strftime('%Y-%m-%d'),
                enrollment.get_status_display()
            ])
        
        return response
    
    total_students = enrollments.count()
    remaining_slots = offering.max_students - total_students
    
    context = {
        'offering': offering,
        'enrollments': enrollments,
        'total_students': total_students,
        'remaining_slots': remaining_slots,
    }
    
    return render(request, 'courses/class_list.html', context)
