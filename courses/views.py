from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import csv

from .models import (
    Department, AcademicYear, Semester, Curriculum, Course, CurriculumCourse,
    CourseOffering, StudentEnrollment, StudentCurriculum, EnrollmentPeriod,
    EnrollmentCode, EnrollmentCodeUsage
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
        return redirect('accounts:teacher_dashboard' if request.user.user_type == 'teacher' else 'accounts:student_dashboard')
    
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
    """Enhanced student enrollment view with modern UI and features"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied.')
        return redirect('accounts:teacher_dashboard')
    
    # Get current semester and enrollment period
    current_semester = Semester.objects.filter(is_current=True).first()
    enrollment_period = EnrollmentPeriod.objects.filter(
        semester=current_semester,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
        is_active=True
    ).first() if current_semester else None
    
    # Get student's curriculum
    student_curriculum = StudentCurriculum.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('curriculum__department').first()
    
    # Get current enrollments with detailed info
    current_enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        course_offering__semester=current_semester
    ).select_related(
        'course_offering__course',
        'course_offering__instructor'
    ) if current_semester else StudentEnrollment.objects.none()
    
    # Calculate enrollment statistics
    enrolled_count = current_enrollments.filter(status='enrolled').count()
    pending_count = current_enrollments.filter(status='pending').count()
    waitlisted_count = current_enrollments.filter(status='waitlisted').count()
    total_units = sum(e.course_offering.course.units for e in current_enrollments.filter(status='enrolled'))
    
    # Get available courses for enrollment
    available_courses = []
    enrolled_offering_ids = []
    
    if student_curriculum and current_semester:
        # Get already enrolled offering IDs
        enrolled_offering_ids = list(current_enrollments.values_list('course_offering_id', flat=True))
        
        # Get curriculum courses for current year level
        curriculum_courses = CurriculumCourse.objects.filter(
            curriculum=student_curriculum.curriculum,
            year_level=student_curriculum.current_year_level
        ).select_related('course')
        
        # Get available course offerings
        for cc in curriculum_courses:
            offerings = CourseOffering.objects.filter(
                course=cc.course,
                semester=current_semester,
                status='open'
            ).select_related(
                'course',
                'instructor'
            ).exclude(
                id__in=enrolled_offering_ids
            )
            
            for offering in offerings:
                # The enrolled_count property is already available in the model
                # Just add the offering to available courses
                available_courses.append(offering)
        
        # Get general education and elective courses
        general_offerings = CourseOffering.objects.filter(
            semester=current_semester,
            status='open',
            course__course_type__in=['general', 'elective']
        ).select_related(
            'course',
            'instructor'
        ).exclude(
            id__in=enrolled_offering_ids
        )
        
        for offering in general_offerings:
            # The enrolled_count and is_full properties are already available in the model
            available_courses.append(offering)
    
    context = {
        'current_semester': current_semester,
        'enrollment_period': enrollment_period,
        'student_curriculum': student_curriculum,
        'current_enrollments': current_enrollments,
        'enrolled_count': enrolled_count,
        'pending_count': pending_count,
        'waitlisted_count': waitlisted_count,
        'total_units': total_units,
        'available_courses': available_courses,
        'enrolled_offering_ids': enrolled_offering_ids,
    }
    
    return render(request, 'courses/student_enrollment_new.html', context)

@login_required
def enroll_in_course_view(request, offering_id):
    """Enhanced course enrollment with AJAX support"""
    if request.user.user_type != 'student':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied.'})
        messages.error(request, 'Access denied.')
        return redirect('accounts:teacher_dashboard')
    
    offering = get_object_or_404(CourseOffering, id=offering_id)
    
    # Check enrollment period
    current_semester = Semester.objects.filter(is_current=True).first()
    enrollment_period = EnrollmentPeriod.objects.filter(
        semester=current_semester,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
        is_active=True
    ).first() if current_semester else None
    
    # Validation checks
    errors = []
    
    if offering.status != 'open':
        errors.append('Enrollment is not open for this course.')
    
    if StudentEnrollment.objects.filter(student=request.user, course_offering=offering).exists():
        errors.append('You are already enrolled in this course.')
    
    # Get enrollment count
    enrolled_count = StudentEnrollment.objects.filter(
        course_offering=offering,
        status__in=['enrolled', 'pending']
    ).count()
    
    is_full = enrolled_count >= offering.max_students
    
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return enrollment confirmation dialog
        if errors:
            return JsonResponse({'success': False, 'message': ' '.join(errors)})
        
        # Get prerequisites and other course info
        prerequisites = []
        if hasattr(offering.course, 'prerequisites'):
            prerequisites = offering.course.prerequisites.all()
        
        context = {
            'offering': offering,
            'is_full': is_full,
            'enrolled_count': enrolled_count,
            'prerequisites': prerequisites,
            'enrollment_period': enrollment_period,
        }
        
        html_content = f"""
        <div class="enrollment-confirmation">
            <div class="course-info mb-3">
                <h6 class="fw-bold text-primary">{offering.course.code} - {offering.course.title}</h6>
                <div class="row">
                    <div class="col-6">
                        <small class="text-muted">Section:</small>
                        <div class="fw-semibold">{offering.section}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Units:</small>
                        <div class="fw-semibold">{offering.course.units}</div>
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col-6">
                        <small class="text-muted">Instructor:</small>
                        <div class="fw-semibold">{offering.instructor.get_full_name() if offering.instructor else 'TBA'}</div>
                    </div>
                    <div class="col-6">
                        <small class="text-muted">Schedule:</small>
                        <div class="fw-semibold">{offering.schedule or 'TBA'}</div>
                    </div>
                </div>
                <div class="mt-2">
                    <small class="text-muted">Capacity:</small>
                    <div class="progress mt-1" style="height: 8px;">
                        <div class="progress-bar" style="width: {(enrolled_count/offering.max_students)*100}%"></div>
                    </div>
                    <small class="text-muted">{enrolled_count}/{offering.max_students} students enrolled</small>
                </div>
            </div>
            
            {"<div class='alert alert-warning'><i class='fas fa-exclamation-triangle me-2'></i>This course is full. You will be added to the waitlist.</div>" if is_full else ""}
            
            <div class="course-description">
                <small class="text-muted">Description:</small>
                <p class="mb-0">{offering.course.description or 'No description available.'}</p>
            </div>
        </div>
        """
        
        return JsonResponse({'success': True, 'html': html_content})
    
    if request.method == 'POST':
        # Final validation
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': ' '.join(errors)})
            for error in errors:
                messages.error(request, error)
            return redirect('courses:student_enrollment')
        
        # Determine enrollment status
        if not enrollment_period:
            status = 'pending'  # Late enrollment requires approval
        elif is_full:
            status = 'waitlisted'
        else:
            status = 'enrolled'  # Auto-approve during enrollment period
        
        try:
            with transaction.atomic():
                enrollment = StudentEnrollment.objects.create(
                    student=request.user,
                    course_offering=offering,
                    enrollment_type='regular',
                    status=status,
                    enrollment_date=timezone.now()
                )
            
            # Prepare success message
            if status == 'enrolled':
                message = f'Successfully enrolled in {offering.course.code}!'
            elif status == 'waitlisted':
                message = f'Added to waitlist for {offering.course.code}. You will be notified if a spot opens up.'
            else:
                message = f'Enrollment request submitted for {offering.course.code}. Waiting for approval.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': message})
            
            messages.success(request, message)
            return redirect('courses:student_enrollment')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'An error occurred during enrollment. Please try again.'})
            
            messages.error(request, 'An error occurred during enrollment. Please try again.')
            return redirect('courses:student_enrollment')
    
    context = {'offering': offering}
    return render(request, 'courses/enroll_confirmation.html', context)

@login_required
def course_offering_details_view(request, offering_id):
    """Get detailed course offering information via AJAX"""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    offering = get_object_or_404(CourseOffering, id=offering_id)
    
    # Get enrollment statistics
    enrollments = StudentEnrollment.objects.filter(course_offering=offering)
    enrolled_count = enrollments.filter(status='enrolled').count()
    pending_count = enrollments.filter(status='pending').count()
    waitlisted_count = enrollments.filter(status='waitlisted').count()
    
    # Get prerequisites
    prerequisites = []
    if hasattr(offering.course, 'prerequisites'):
        prerequisites = [p.code for p in offering.course.prerequisites.all()]
    
    html_content = f"""
    <div class="course-details-modal">
        <div class="row mb-3">
            <div class="col-md-8">
                <h5 class="text-primary mb-1">{offering.course.code} - {offering.course.title}</h5>
                <p class="text-muted mb-0">Section {offering.section}</p>
            </div>
            <div class="col-md-4 text-end">
                <span class="badge bg-primary fs-6">{offering.course.units} Units</span>
            </div>
        </div>
        
        <div class="course-info-grid mb-4">
            <div class="info-item">
                <label>Instructor:</label>
                <span>{offering.instructor.get_full_name() if offering.instructor else 'TBA'}</span>
            </div>
            <div class="info-item">
                <label>Department:</label>
                <span>{offering.instructor.teacher_profile.department.name if offering.instructor and hasattr(offering.instructor, 'teacher_profile') else 'N/A'}</span>
            </div>
            <div class="info-item">
                <label>Schedule:</label>
                <span>{offering.schedule or 'TBA'}</span>
            </div>
            <div class="info-item">
                <label>Room:</label>
                <span>{offering.room or 'TBA'}</span>
            </div>
        </div>
        
        <div class="enrollment-stats mb-4">
            <h6>Enrollment Statistics</h6>
            <div class="row text-center">
                <div class="col-3">
                    <div class="stat-box">
                        <h4 class="text-success mb-1">{enrolled_count}</h4>
                        <small class="text-muted">Enrolled</small>
                    </div>
                </div>
                <div class="col-3">
                    <div class="stat-box">
                        <h4 class="text-warning mb-1">{pending_count}</h4>
                        <small class="text-muted">Pending</small>
                    </div>
                </div>
                <div class="col-3">
                    <div class="stat-box">
                        <h4 class="text-info mb-1">{waitlisted_count}</h4>
                        <small class="text-muted">Waitlisted</small>
                    </div>
                </div>
                <div class="col-3">
                    <div class="stat-box">
                        <h4 class="text-primary mb-1">{offering.max_students}</h4>
                        <small class="text-muted">Capacity</small>
                    </div>
                </div>
            </div>
        </div>
        
        {"<div class='mb-3'><h6>Prerequisites</h6><ul class='list-inline'>" + "".join([f"<li class='list-inline-item'><span class='badge bg-secondary'>{p}</span></li>" for p in prerequisites]) + "</ul></div>" if prerequisites else ""}
        
        <div class="course-description">
            <h6>Course Description</h6>
            <p class="text-muted">{offering.course.description or 'No description available.'}</p>
        </div>
    </div>
    
    <style>
    .course-info-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }}
    
    .info-item {{
        display: flex;
        flex-direction: column;
    }}
    
    .info-item label {{
        font-weight: 600;
        color: #666;
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
    }}
    
    .info-item span {{
        font-weight: 500;
    }}
    
    .stat-box {{
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 0.25rem;
    }}
    
    @media (max-width: 768px) {{
        .course-info-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>
    """
    
    return JsonResponse({'success': True, 'html': html_content})

@login_required
def cancel_enrollment_view(request, enrollment_id):
    """Cancel student enrollment"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    enrollment = get_object_or_404(StudentEnrollment, id=enrollment_id)
    
    # Check if user can cancel this enrollment
    if enrollment.student != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    # Check if enrollment can be cancelled
    if enrollment.status in ['dropped', 'completed']:
        return JsonResponse({'success': False, 'message': 'This enrollment cannot be cancelled'})
    
    try:
        with transaction.atomic():
            enrollment.status = 'dropped'
            enrollment.dropped_at = timezone.now()
            enrollment.save()
            
            # If this was an enrolled student, move first waitlisted student to enrolled
            if enrollment.status == 'enrolled':
                next_waitlisted = StudentEnrollment.objects.filter(
                    course_offering=enrollment.course_offering,
                    status='waitlisted'
                ).order_by('enrollment_date').first()
                
                if next_waitlisted:
                    next_waitlisted.status = 'enrolled'
                    next_waitlisted.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully cancelled enrollment in {enrollment.course_offering.course.code}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while cancelling enrollment. Please try again.'
        })

@login_required
def use_enrollment_code_view(request):
    """Use enrollment code for late enrollment/transferees"""
    if request.user.user_type != 'student':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied.'})
        messages.error(request, 'Access denied.')
        return redirect('accounts:home')
    
    if request.method == 'POST':
        code_text = request.POST.get('enrollment_code', '').strip().upper()
        
        if not code_text:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please enter an enrollment code.'})
            messages.error(request, 'Please enter an enrollment code.')
            return redirect('courses:student_enrollment')
        
        try:
            # Find the enrollment code
            enrollment_code = EnrollmentCode.objects.get(code=code_text)
            
            # Check if code can be used
            can_use, message = enrollment_code.can_be_used_by(request.user)
            
            if not can_use:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': message})
                messages.error(request, message)
                return redirect('courses:student_enrollment')
            
            # Get client IP
            def get_client_ip(request):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                return ip
            
            # Create enrollment and track usage
            with transaction.atomic():
                enrollment = StudentEnrollment.objects.create(
                    student=request.user,
                    course_offering=enrollment_code.course_offering,
                    enrollment_type='late',  # Mark as late enrollment
                    status='enrolled',  # Direct enrollment for code-based enrollment
                    enrollment_date=timezone.now()
                )
                
                # Track code usage
                code_usage = EnrollmentCodeUsage.objects.create(
                    code=enrollment_code,
                    user=request.user,
                    enrollment=enrollment,
                    ip_address=get_client_ip(request)
                )
                
                # Update used count
                enrollment_code.used_count += 1
                enrollment_code.save()
            
            success_message = f'Successfully enrolled in {enrollment_code.course_offering.course.code} using enrollment code!'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': success_message})
            
            messages.success(request, success_message)
            return redirect('courses:student_enrollment')
            
        except EnrollmentCode.DoesNotExist:
            error_message = 'Invalid enrollment code. Please check the code and try again.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            return redirect('courses:student_enrollment')
        
        except Exception as e:
            error_message = 'An error occurred while processing the enrollment code. Please try again.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_message})
            messages.error(request, error_message)
            return redirect('courses:student_enrollment')
    
    # GET request - show enrollment code form
    return render(request, 'courses/use_enrollment_code.html')

@login_required
@user_passes_test(is_admin_or_teacher)
def manage_enrollment_codes_view(request):
    """Manage enrollment codes for teachers/registrars"""
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get course offerings for current semester that the user can manage
    if request.user.is_staff:
        # Admin can manage all offerings
        course_offerings = CourseOffering.objects.filter(
            semester=current_semester
        ).select_related('course', 'instructor') if current_semester else CourseOffering.objects.none()
    else:
        # Teachers can only manage their own offerings
        course_offerings = CourseOffering.objects.filter(
            semester=current_semester,
            instructor=request.user
        ).select_related('course') if current_semester else CourseOffering.objects.none()
    
    # Get existing codes
    enrollment_codes = EnrollmentCode.objects.filter(
        course_offering__in=course_offerings
    ).select_related('course_offering__course', 'created_by')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_code':
            offering_id = request.POST.get('course_offering_id')
            max_uses = int(request.POST.get('max_uses', 1))
            valid_hours = int(request.POST.get('valid_hours', 24))
            notes = request.POST.get('notes', '')
            
            try:
                offering = get_object_or_404(CourseOffering, id=offering_id)
                
                # Generate unique code
                import string
                import random
                
                def generate_code():
                    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                code_text = generate_code()
                while EnrollmentCode.objects.filter(code=code_text).exists():
                    code_text = generate_code()
                
                # Create enrollment code
                enrollment_code = EnrollmentCode.objects.create(
                    code=code_text,
                    course_offering=offering,
                    max_uses=max_uses,
                    valid_from=timezone.now(),
                    valid_until=timezone.now() + timedelta(hours=valid_hours),
                    created_by=request.user,
                    notes=notes
                )
                
                messages.success(request, f'Enrollment code created: {code_text}')
                return redirect('courses:manage_enrollment_codes')
                
            except Exception as e:
                messages.error(request, 'Error creating enrollment code. Please try again.')
        
        elif action == 'deactivate_code':
            code_id = request.POST.get('code_id')
            try:
                enrollment_code = get_object_or_404(EnrollmentCode, id=code_id, created_by=request.user)
                enrollment_code.is_active = False
                enrollment_code.save()
                messages.success(request, 'Enrollment code deactivated successfully.')
            except Exception as e:
                messages.error(request, 'Error deactivating enrollment code.')
        
        return redirect('courses:manage_enrollment_codes')
    
    context = {
        'current_semester': current_semester,
        'course_offerings': course_offerings,
        'enrollment_codes': enrollment_codes,
    }
    
    return render(request, 'courses/manage_enrollment_codes.html', context)

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
