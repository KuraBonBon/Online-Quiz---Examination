from django import forms
from django.forms import formset_factory
from .models import Assessment, Question, Choice, CorrectAnswer

class AssessmentForm(forms.ModelForm):
    """Form for creating and editing assessments (includes assessment_type)"""
    
    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'assessment_type', 'time_limit',
            'show_correct_answers', 'randomize_questions', 'randomize_choices',
            'max_attempts', 'passing_score', 'available_from', 'available_until'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter assessment title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
            'assessment_type': forms.Select(attrs={'class': 'form-control'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes (optional)'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'available_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'available_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom styling to checkboxes
        for field_name in ['show_correct_answers', 'randomize_questions', 'randomize_choices']:
            self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})

class AssessmentCreationForm(forms.ModelForm):
    """Form for creating assessments (excludes assessment_type since it's set by URL)"""
    
    class Meta:
        model = Assessment
        fields = [
            'title', 'description', 'time_limit',
            'show_correct_answers', 'randomize_questions', 'randomize_choices',
            'max_attempts', 'passing_score', 'available_from', 'available_until'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter assessment title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes (optional)'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'available_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'available_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add custom styling to checkboxes
        for field_name in ['show_correct_answers', 'randomize_questions', 'randomize_choices']:
            self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})

class QuestionForm(forms.ModelForm):
    """Form for creating and editing questions"""
    
    class Meta:
        model = Question
        fields = ['question_type', 'question_text', 'points', 'expected_answers_count']
        widgets = {
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'expected_answers_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expected_answers_count'].help_text = "Only for enumeration questions"

class ChoiceForm(forms.ModelForm):
    """Form for multiple choice options"""
    
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter choice'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CorrectAnswerForm(forms.ModelForm):
    """Form for correct answers (identification, enumeration)"""
    
    class Meta:
        model = CorrectAnswer
        fields = ['answer_text', 'is_case_sensitive']
        widgets = {
            'answer_text': forms.TextInput(attrs={
                'class': 'form-control answer-input',
                'placeholder': 'Enter correct answer',
                'autocomplete': 'off',
                'maxlength': '500'
            }),
            'is_case_sensitive': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_answer_text(self):
        answer_text = self.cleaned_data.get('answer_text', '').strip()
        if not answer_text:
            raise forms.ValidationError("Answer text cannot be empty.")
        if len(answer_text) > 500:
            raise forms.ValidationError("Answer text cannot exceed 500 characters.")
        
        # Remove extra whitespace and normalize
        answer_text = ' '.join(answer_text.split())
        return answer_text

class EnhancedCorrectAnswerForm(forms.ModelForm):
    """Enhanced form for correct answers with better validation and UX"""
    
    class Meta:
        model = CorrectAnswer
        fields = ['answer_text', 'is_case_sensitive']
        widgets = {
            'answer_text': forms.TextInput(attrs={
                'class': 'form-control enhanced-answer-input',
                'placeholder': 'Enter correct answer',
                'autocomplete': 'off',
                'maxlength': '500',
                'data-live-validation': 'true'
            }),
            'is_case_sensitive': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answer_text'].label = "Answer"
        self.fields['is_case_sensitive'].label = "Case Sensitive"
        self.fields['answer_text'].help_text = "Enter a possible correct answer"
        
    def clean_answer_text(self):
        answer_text = self.cleaned_data.get('answer_text', '').strip()
        
        # Validation
        if not answer_text:
            raise forms.ValidationError("Answer text cannot be empty.")
        
        if len(answer_text) > 500:
            raise forms.ValidationError("Answer text cannot exceed 500 characters.")
        
        if len(answer_text) < 1:
            raise forms.ValidationError("Answer must be at least 1 character long.")
        
        # Normalize whitespace
        answer_text = ' '.join(answer_text.split())
        
        # Check for potentially problematic characters
        problematic_chars = ['<', '>', '&', '"', "'"]
        if any(char in answer_text for char in problematic_chars):
            import html
            answer_text = html.escape(answer_text)
        
        return answer_text

class ReferenceAnswerForm(forms.ModelForm):
    """Form for reference answers (essay questions)"""
    
    class Meta:
        model = CorrectAnswer
        fields = ['answer_text']
        widgets = {
            'answer_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter reference answer or key points for grading guidance',
                'rows': 4
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['answer_text'].label = "Reference Answer"
        self.fields['answer_text'].help_text = "Provide key points or sample answers for grading guidance"

class TrueFalseForm(forms.Form):
    """Form for selecting correct answer in True/False questions"""
    correct_answer = forms.ChoiceField(
        choices=[('true', 'True'), ('false', 'False')],
        widget=forms.RadioSelect,
        label="Select the correct answer"
    )

# Formsets for handling multiple choices and answers
ChoiceFormSet = formset_factory(ChoiceForm, extra=4, max_num=10, can_delete=True)
CorrectAnswerFormSet = formset_factory(CorrectAnswerForm, extra=1, max_num=20, can_delete=True)
EnhancedCorrectAnswerFormSet = formset_factory(
    EnhancedCorrectAnswerForm, 
    extra=1, 
    min_num=1,
    max_num=25, 
    can_delete=True,
    validate_min=True
)
ReferenceAnswerFormSet = formset_factory(ReferenceAnswerForm, extra=1, max_num=5, can_delete=True)

class AssessmentSelectionForm(forms.Form):
    """Form for selecting assessment type"""
    ASSESSMENT_CHOICES = (
        ('quiz', 'Quiz'),
        ('exam', 'Exam'),
    )
    
    assessment_type = forms.ChoiceField(
        choices=ASSESSMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Select Assessment Type"
    )

class AssessmentFilterForm(forms.Form):
    """Form for filtering assessments in My Assessments page"""
    
    SORT_CHOICES = (
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
        ('title', 'Title A-Z'),
        ('-title', 'Title Z-A'),
        ('status', 'Status'),
        ('-status', 'Status (Desc)'),
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search assessments...',
            'style': 'padding-left: 2.5rem;'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(Assessment.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    assessment_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(Assessment.ASSESSMENT_TYPES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    subject_category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Subjects')] + [
            ('math', 'Mathematics'),
            ('science', 'Science'),
            ('english', 'English'),
            ('history', 'History'),
            ('programming', 'Programming'),
            ('general', 'General'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=SORT_CHOICES,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from GET parameters
        if 'data' not in kwargs and hasattr(self, 'request'):
            initial = {}
            for field_name in self.fields:
                value = self.request.GET.get(field_name)
                if value:
                    initial[field_name] = value
            if initial:
                for field_name, value in initial.items():
                    self.fields[field_name].initial = value
