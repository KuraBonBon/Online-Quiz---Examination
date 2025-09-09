from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import (
    Department, AcademicYear, Semester, Curriculum, Course, CurriculumCourse,
    CourseOffering, StudentEnrollment, StudentCurriculum, EnrollmentPeriod
)

User = get_user_model()

class DepartmentForm(forms.ModelForm):
    """Form for creating/editing departments"""
    class Meta:
        model = Department
        fields = ['code', 'name', 'description', 'head_of_department', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS, IT, ENG'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'head_of_department': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head_of_department'].queryset = User.objects.filter(user_type='teacher')

class AcademicYearForm(forms.ModelForm):
    """Form for creating/editing academic years"""
    class Meta:
        model = AcademicYear
        fields = ['year_start', 'year_end', 'is_current']
        widgets = {
            'year_start': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2024'}),
            'year_end': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2025'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SemesterForm(forms.ModelForm):
    """Form for creating/editing semesters"""
    class Meta:
        model = Semester
        fields = ['academic_year', 'semester', 'start_date', 'end_date', 'is_current']
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CurriculumForm(forms.ModelForm):
    """Form for creating/editing curricula"""
    class Meta:
        model = Curriculum
        fields = ['code', 'name', 'department', 'year_introduced', 'total_units', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BSCS2024'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Program Name'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'year_introduced': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2024'}),
            'total_units': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '120'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'units', 'department', 'prerequisites', 'course_type', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS101'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'units': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'prerequisites': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 4}),
            'course_type': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prerequisites'].queryset = Course.objects.filter(is_active=True)
        if self.instance.pk:
            # Exclude self from prerequisites
            self.fields['prerequisites'].queryset = self.fields['prerequisites'].queryset.exclude(pk=self.instance.pk)

class CurriculumCourseForm(forms.ModelForm):
    """Form for adding courses to curriculum"""
    class Meta:
        model = CurriculumCourse
        fields = ['course', 'year_level', 'semester', 'is_required']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'year_level': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CourseOfferingForm(forms.ModelForm):
    """Form for creating course offerings"""
    class Meta:
        model = CourseOffering
        fields = [
            'course', 'semester', 'section', 'instructor', 'schedule', 'room',
            'max_students', 'status', 'enrollment_start', 'enrollment_end',
            'class_start', 'class_end'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., A, B, 1A'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'schedule': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g., MWF 9:00-10:00 AM'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Room 301, Lab A'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'enrollment_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'enrollment_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'class_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'class_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = User.objects.filter(user_type='teacher')

class StudentEnrollmentForm(forms.ModelForm):
    """Form for enrolling students"""
    class Meta:
        model = StudentEnrollment
        fields = ['student', 'course_offering', 'enrollment_type', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course_offering': forms.Select(attrs={'class': 'form-control'}),
            'enrollment_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(user_type='student')

class StudentCurriculumForm(forms.ModelForm):
    """Form for assigning students to curriculum"""
    class Meta:
        model = StudentCurriculum
        fields = ['student', 'curriculum', 'year_started', 'current_year_level']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'curriculum': forms.Select(attrs={'class': 'form-control'}),
            'year_started': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2024'}),
            'current_year_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(user_type='student')

class EnrollmentPeriodForm(forms.ModelForm):
    """Form for managing enrollment periods"""
    class Meta:
        model = EnrollmentPeriod
        fields = [
            'name', 'semester', 'student_category', 'year_levels',
            'start_date', 'end_date', 'is_active', 'priority_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Regular Enrollment'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'student_category': forms.Select(attrs={'class': 'form-control'}),
            'year_levels': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1,2,3,4 or leave blank for all'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'priority_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class BulkEnrollmentForm(forms.Form):
    """Form for bulk enrollment of students based on curriculum"""
    curriculum = forms.ModelChoiceField(
        queryset=Curriculum.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select curriculum for automatic enrollment"
    )
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Target semester for enrollment"
    )
    year_level = forms.IntegerField(
        min_value=1, max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Year level to enroll"
    )
    semester_filter = forms.ChoiceField(
        choices=[('1st', '1st Semester'), ('2nd', '2nd Semester'), ('summer', 'Summer')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Curriculum semester to enroll"
    )
    enrollment_type = forms.ChoiceField(
        choices=StudentEnrollment.ENROLLMENT_TYPE_CHOICES,
        initial='regular',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['semester'].queryset = Semester.objects.filter(is_current=True)

class CourseSearchForm(forms.Form):
    """Form for searching/filtering courses"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by course code or title...'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    course_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(Course.COURSE_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    units = forms.IntegerField(
        required=False,
        min_value=1, max_value=6,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Units'})
    )

class StudentEnrollmentSearchForm(forms.Form):
    """Form for searching student enrollments"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by student name or ID...'
        })
    )
    course_offering = forms.ModelChoiceField(
        queryset=CourseOffering.objects.all(),
        required=False,
        empty_label="All Courses",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(StudentEnrollment.ENROLLMENT_STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    enrollment_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(StudentEnrollment.ENROLLMENT_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# Formsets for curriculum course management
CurriculumCourseFormSet = inlineformset_factory(
    Curriculum, 
    CurriculumCourse,
    form=CurriculumCourseForm,
    extra=1,
    can_delete=True,
    fields=['course', 'year_level', 'semester', 'is_required']
)
