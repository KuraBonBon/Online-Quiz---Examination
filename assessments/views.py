from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.forms import formset_factory
import json

from .models import Assessment, Question, Choice, CorrectAnswer, StudentAttempt, StudentAnswer
from .forms import (
    AssessmentForm, AssessmentCreationForm, QuestionForm, ChoiceForm, CorrectAnswerForm,
    ChoiceFormSet, CorrectAnswerFormSet, AssessmentSelectionForm, TrueFalseForm,
    ReferenceAnswerForm, ReferenceAnswerFormSet
)

@login_required
def assessment_selection_view(request):
    """View for selecting assessment type (Quiz or Exam)"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Only teachers can create assessments.')
        return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        form = AssessmentSelectionForm(request.POST)
        if form.is_valid():
            assessment_type = form.cleaned_data['assessment_type']
            return redirect('assessments:create_assessment', assessment_type=assessment_type)
    else:
        form = AssessmentSelectionForm()
    
    return render(request, 'assessments/assessment_selection.html', {'form': form})

@login_required
def create_assessment_view(request, assessment_type):
    """View for creating a new assessment"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Only teachers can create assessments.')
        return redirect('teacher_dashboard')
    
    if assessment_type not in ['quiz', 'exam']:
        messages.error(request, 'Invalid assessment type.')
        return redirect('assessments:assessment_selection')
    
    if request.method == 'POST':
        form = AssessmentCreationForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.creator = request.user
            assessment.assessment_type = assessment_type
            assessment.save()
            
            messages.success(request, f'{assessment_type.title()} created successfully! Now add questions.')
            return redirect('assessments:add_question', assessment_id=assessment.id)
        else:
            # Add form error messages to help with debugging
            for field_name, field_errors in form.errors.items():
                for error in field_errors:
                    messages.error(request, f"{field_name}: {error}")
    else:
        form = AssessmentCreationForm()
    
    context = {
        'form': form,
        'assessment_type': assessment_type,
        'assessment_type_display': assessment_type.title()
    }
    return render(request, 'assessments/create_assessment.html', context)

@login_required
def add_question_view(request, assessment_id):
    """View for adding questions to an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id, creator=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.assessment = assessment
            
            # Set order for the question
            last_question = Question.objects.filter(assessment=assessment).order_by('-order').first()
            question.order = (last_question.order + 1) if last_question else 1
            
            question.save()
            
            # Handle choices for multiple choice and true/false questions
            if question.question_type in ['multiple_choice', 'true_false']:
                if question.question_type == 'true_false':
                    # Automatically create True/False choices with True as default correct answer
                    Choice.objects.create(question=question, choice_text='True', order=1, is_correct=True)
                    Choice.objects.create(question=question, choice_text='False', order=2, is_correct=False)
                    messages.success(request, 'True/False question added successfully! You can change the correct answer by editing the question.')
                else:
                    # Redirect to add choices for multiple choice
                    messages.success(request, 'Question added! Now add answer choices.')
                    return redirect('assessments:edit_question', question_id=question.id)
            
            # Handle correct answers for identification and enumeration
            elif question.question_type in ['identification', 'enumeration']:
                messages.success(request, 'Question added! Now add correct answers.')
                return redirect('assessments:edit_question', question_id=question.id)
            
            # Handle reference answers for essay questions
            elif question.question_type == 'essay':
                messages.success(request, 'Question added! Now add reference answers for grading guidance.')
                return redirect('assessments:edit_question', question_id=question.id)
            
            # Stay on the same page to add more questions
            return redirect('assessments:add_question', assessment_id=assessment.id)
    else:
        question_form = QuestionForm()
    
    questions = Question.objects.filter(assessment=assessment).order_by('order')
    
    context = {
        'assessment': assessment,
        'question_form': question_form,
        'questions': questions,
    }
    return render(request, 'assessments/add_question.html', context)

@login_required
def edit_question_view(request, question_id):
    """View for editing a question and its choices/answers"""
    question = get_object_or_404(Question, id=question_id, assessment__creator=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST, instance=question)
        
        if question_form.is_valid():
            question = question_form.save()
            
            # Handle choices for multiple choice questions
            if question.question_type == 'multiple_choice':
                choice_formset = ChoiceFormSet(request.POST, prefix='choice')
                if choice_formset.is_valid():
                    # Delete existing choices
                    question.choices.all().delete()
                    
                    # Create new choices
                    for i, form in enumerate(choice_formset):
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            choice = form.save(commit=False)
                            choice.question = question
                            choice.order = i + 1
                            choice.save()
                    
                    messages.success(request, 'Question and choices updated successfully!')
                    return redirect('assessments:manage_questions', assessment_id=question.assessment.id)
            
            # Handle correct answers for identification and enumeration
            elif question.question_type in ['identification', 'enumeration']:
                answer_formset = CorrectAnswerFormSet(request.POST, prefix='answer')
                if answer_formset.is_valid():
                    # Delete existing answers
                    question.correct_answers.all().delete()
                    
                    # Create new answers
                    for i, form in enumerate(answer_formset):
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            answer = form.save(commit=False)
                            answer.question = question
                            answer.order = i + 1
                            answer.save()
                    
                    messages.success(request, 'Question and answers updated successfully!')
                    return redirect('assessments:manage_questions', assessment_id=question.assessment.id)
            
            # Handle reference answers for essay questions
            elif question.question_type == 'essay':
                reference_formset = ReferenceAnswerFormSet(request.POST, prefix='reference')
                if reference_formset.is_valid():
                    # Delete existing answers
                    question.correct_answers.all().delete()
                    
                    # Create new reference answers
                    for i, form in enumerate(reference_formset):
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            answer = form.save(commit=False)
                            answer.question = question
                            answer.order = i + 1
                            answer.is_case_sensitive = False  # Essays are not case sensitive by default
                            answer.save()
                    
                    messages.success(request, 'Question and reference answers updated successfully!')
                    return redirect('assessments:manage_questions', assessment_id=question.assessment.id)
            
            # For true/false, handle correct answer selection
            elif question.question_type == 'true_false':
                true_false_form = TrueFalseForm(request.POST, prefix='truefalse')
                if true_false_form.is_valid():
                    correct_answer = true_false_form.cleaned_data['correct_answer']
                    
                    # Update the choices to reflect the correct answer
                    for choice in question.choices.all():
                        if choice.choice_text.lower() == correct_answer:
                            choice.is_correct = True
                        else:
                            choice.is_correct = False
                        choice.save()
                    
                    messages.success(request, 'Question and correct answer updated successfully!')
                    return redirect('assessments:manage_questions', assessment_id=question.assessment.id)
    
    else:
        question_form = QuestionForm(instance=question)
    
    # Prepare formsets based on question type
    choice_formset = None
    answer_formset = None
    reference_formset = None
    true_false_form = None
    
    if question.question_type == 'multiple_choice':
        existing_choices = question.choices.all()
        initial_choices = [
            {'choice_text': choice.choice_text, 'is_correct': choice.is_correct}
            for choice in existing_choices
        ]
        # Calculate extra forms needed (minimum 4 total, but allow for existing choices)
        extra_needed = max(0, 4 - len(initial_choices))
        ChoiceFormSetEdit = formset_factory(ChoiceForm, extra=extra_needed, max_num=10, can_delete=True)
        choice_formset = ChoiceFormSetEdit(prefix='choice', initial=initial_choices)
    
    elif question.question_type == 'true_false':
        # Determine which choice is currently marked as correct
        correct_choice = question.choices.filter(is_correct=True).first()
        initial_answer = 'true' if correct_choice and correct_choice.choice_text.lower() == 'true' else 'false'
        true_false_form = TrueFalseForm(prefix='truefalse', initial={'correct_answer': initial_answer})
    
    elif question.question_type in ['identification', 'enumeration']:
        existing_answers = question.correct_answers.all()
        initial_answers = [
            {'answer_text': answer.answer_text, 'is_case_sensitive': answer.is_case_sensitive}
            for answer in existing_answers
        ]
        # Only add one extra form if no existing answers, otherwise just show existing
        extra_needed = 1 if not initial_answers else 0
        CorrectAnswerFormSetEdit = formset_factory(CorrectAnswerForm, extra=extra_needed, max_num=20, can_delete=True)
        answer_formset = CorrectAnswerFormSetEdit(prefix='answer', initial=initial_answers)
    
    elif question.question_type == 'essay':
        existing_references = question.correct_answers.all()
        initial_references = [
            {'answer_text': answer.answer_text}
            for answer in existing_references
        ]
        # Only add one extra form if no existing references, otherwise just show existing
        extra_needed = 1 if not initial_references else 0
        ReferenceAnswerFormSetEdit = formset_factory(ReferenceAnswerForm, extra=extra_needed, max_num=5, can_delete=True)
        reference_formset = ReferenceAnswerFormSetEdit(prefix='reference', initial=initial_references)
    
    context = {
        'question': question,
        'question_form': question_form,
        'choice_formset': choice_formset,
        'answer_formset': answer_formset,
        'reference_formset': reference_formset,
        'true_false_form': true_false_form,
    }
    return render(request, 'assessments/edit_question.html', context)

@login_required
def manage_questions_view(request, assessment_id):
    """View for managing all questions in an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id, creator=request.user)
    questions = Question.objects.filter(assessment=assessment).order_by('order')
    
    context = {
        'assessment': assessment,
        'questions': questions,
    }
    return render(request, 'assessments/manage_questions.html', context)

@login_required
def delete_question_view(request, question_id):
    """View for deleting a question"""
    question = get_object_or_404(Question, id=question_id, assessment__creator=request.user)
    assessment_id = question.assessment.id
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
    
    return redirect('assessments:manage_questions', assessment_id=assessment_id)

@login_required
def my_assessments_view(request):
    """View for teachers to see their created assessments"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Only teachers can view this page.')
        return redirect('student_dashboard')
    
    assessments = Assessment.objects.filter(creator=request.user).order_by('-created_at')
    
    context = {
        'assessments': assessments,
    }
    return render(request, 'assessments/my_assessments.html', context)

@login_required
def assessment_detail_view(request, assessment_id):
    """View for viewing assessment details"""
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Check permissions
    if request.user.user_type == 'teacher' and assessment.creator != request.user:
        messages.error(request, 'You can only view your own assessments.')
        return redirect('assessments:my_assessments')
    
    questions = Question.objects.filter(assessment=assessment).order_by('order')
    
    context = {
        'assessment': assessment,
        'questions': questions,
    }
    return render(request, 'assessments/assessment_detail.html', context)

@login_required
def edit_assessment_view(request, assessment_id):
    """View for editing assessment settings"""
    assessment = get_object_or_404(Assessment, id=assessment_id, creator=request.user)
    
    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assessment updated successfully!')
            return redirect('assessments:assessment_detail', assessment_id=assessment.id)
    else:
        form = AssessmentForm(instance=assessment)
    
    context = {
        'form': form,
        'assessment': assessment,
    }
    return render(request, 'assessments/edit_assessment.html', context)

@login_required
def publish_assessment_view(request, assessment_id):
    """View for publishing an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id, creator=request.user)
    
    if request.method == 'POST':
        if assessment.questions.count() == 0:
            messages.error(request, 'Cannot publish assessment without questions.')
            return redirect('assessments:assessment_detail', assessment_id=assessment.id)
        
        assessment.status = 'published'
        assessment.save()
        messages.success(request, 'Assessment published successfully!')
    
    return redirect('assessments:assessment_detail', assessment_id=assessment.id)

@login_required
def delete_assessment_view(request, assessment_id):
    """View for deleting an assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id, creator=request.user)
    
    if request.method == 'POST':
        assessment.delete()
        messages.success(request, 'Assessment deleted successfully!')
        return redirect('assessments:my_assessments')
    
    return redirect('assessments:assessment_detail', assessment_id=assessment.id)

@login_required
def available_assessments_view(request):
    """View for students to see available assessments"""
    if request.user.user_type != 'student':
        messages.error(request, 'Only students can view this page.')
        return redirect('teacher_dashboard')
      # Get published assessments that are currently available
    now = timezone.now()
    assessments = Assessment.objects.filter(
        status='published'
    ).filter(
        Q(available_from__isnull=True) | Q(available_from__lte=now)
    ).filter(
        Q(available_until__isnull=True) | Q(available_until__gte=now)
    ).order_by('-created_at')
    
    context = {
        'assessments': assessments,
    }
    return render(request, 'assessments/available_assessments.html', context)

@login_required
def take_assessment_view(request, assessment_id):
    """View for students to take an assessment"""
    # This is a placeholder for the assessment taking functionality
    # Will be implemented in the next phase
    messages.info(request, 'Assessment taking feature will be implemented soon.')
    return redirect('assessments:available_assessments')

@login_required
def submit_assessment_view(request, assessment_id):
    """View for submitting an assessment"""
    # This is a placeholder for the assessment submission functionality
    # Will be implemented in the next phase
    messages.info(request, 'Assessment submission feature will be implemented soon.')
    return redirect('assessments:available_assessments')

@login_required
def assessment_results_view(request, attempt_id):
    """View for showing assessment results"""
    # This is a placeholder for the assessment results functionality
    # Will be implemented in the next phase
    messages.info(request, 'Assessment results feature will be implemented soon.')
    return redirect('assessments:available_assessments')
