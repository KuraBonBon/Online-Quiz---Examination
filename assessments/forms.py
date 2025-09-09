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
            'answer_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter correct answer'}),
            'is_case_sensitive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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
