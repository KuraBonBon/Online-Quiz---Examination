from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.db import models, transaction
from django.forms import formset_factory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from .models import Assessment, Question, Choice, CorrectAnswer, StudentAttempt, StudentAnswer
from .forms import (
    AssessmentForm, AssessmentCreationForm, QuestionForm, ChoiceForm, CorrectAnswerForm,
    ChoiceFormSet, CorrectAnswerFormSet, EnhancedCorrectAnswerFormSet, AssessmentSelectionForm, TrueFalseForm,
    ReferenceAnswerForm, ReferenceAnswerFormSet, EnhancedCorrectAnswerForm, AssessmentFilterForm
)
from accounts.feature_utils import feature_not_implemented

@login_required
def assessment_selection_view(request):
    """View for selecting assessment type (Quiz or Exam)"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Only teachers can create assessments.')
        return redirect('accounts:teacher_dashboard')
    
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
        return redirect('accounts:teacher_dashboard')
    
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
    
    # Optimize query with prefetch_related for related objects
    questions = Question.objects.filter(assessment=assessment).prefetch_related(
        'choices', 'correct_answers'
    ).order_by('order')
    
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
    """Enhanced view for teachers to see their created assessments with filtering and pagination"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Only teachers can view this page.')
        return redirect('accounts:student_dashboard')
    
    # Initialize filter form with GET data
    filter_form = AssessmentFilterForm(request.GET or None)
    
    # Get base queryset
    assessments = Assessment.objects.filter(creator=request.user).select_related('creator').annotate(
        question_count=models.Count('questions'),
        attempt_count=models.Count('attempts'),
        avg_score=models.Avg('attempts__percentage')
    ).order_by('-created_at')
    
    # Apply filters if form is valid
    if filter_form.is_valid():
        cleaned_data = filter_form.cleaned_data
        
        if cleaned_data.get('status'):
            assessments = assessments.filter(status=cleaned_data['status'])
        
        if cleaned_data.get('assessment_type'):
            assessments = assessments.filter(assessment_type=cleaned_data['assessment_type'])
        
        if cleaned_data.get('search'):
            search_query = cleaned_data['search']
            assessments = assessments.filter(
                models.Q(title__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        # Sort
        sort_by = cleaned_data.get('sort_by', '-created_at')
        valid_sorts = ['-created_at', 'created_at', 'title', '-title', 'status', '-status']
        if sort_by in valid_sorts:
            assessments = assessments.order_by(sort_by)
    
    # Calculate statistics  
    user_assessments = Assessment.objects.filter(creator=request.user)
    stats = {
        'total': user_assessments.count(),
        'published': user_assessments.filter(status='published').count(),
        'draft': user_assessments.filter(status='draft').count(),
        'total_attempts': user_assessments.aggregate(
            total=models.Count('attempts')
        )['total'] or 0,
        # Template compatibility
        'total_assessments': user_assessments.count(),
        'published_assessments': user_assessments.filter(status='published').count(),
        'draft_assessments': user_assessments.filter(status='draft').count(),
    }
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(assessments, 12)  # Show 12 assessments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Handle bulk actions
    if request.method == 'POST' and request.POST.get('bulk_action'):
        return handle_bulk_assessment_actions(request)
    
    context = {
        'assessments': assessments,  # For backward compatibility
        'page_obj': page_obj,
        'filter_form': filter_form,
        'stats': stats,
        'current_filters': {
            'status': request.GET.get('status'),
            'type': request.GET.get('assessment_type'), 
            'search': request.GET.get('search'),
            'sort_by': request.GET.get('sort_by', '-created_at')
        },
        'status_choices': Assessment.STATUS_CHOICES,
        'type_choices': Assessment.ASSESSMENT_TYPES,
    }
    return render(request, 'assessments/my_assessments.html', context)

def handle_bulk_assessment_actions(request):
    """Handle bulk actions for assessments (publish, archive, duplicate, delete)"""
    try:
        action = request.POST.get('action')
        assessment_ids = request.POST.get('assessment_ids', '').split(',')
        assessment_ids = [int(id) for id in assessment_ids if id.isdigit()]
        
        if not assessment_ids:
            messages.error(request, 'No assessments selected.')
            return redirect('assessments:my_assessments')
        
        # Get assessments belonging to the current user
        assessments = Assessment.objects.filter(
            id__in=assessment_ids, 
            creator=request.user
        )
        
        if not assessments.exists():
            messages.error(request, 'No valid assessments found.')
            return redirect('assessments:my_assessments')
        
        count = assessments.count()
        
        if action == 'publish':
            assessments.update(status='published')
            messages.success(request, f'Successfully published {count} assessment(s).')
        
        elif action == 'archive':
            assessments.update(status='archived')
            messages.success(request, f'Successfully archived {count} assessment(s).')
        
        elif action == 'duplicate':
            for assessment in assessments:
                try:
                    new_assessment = assessment.duplicate()
                    new_assessment.title = f"{assessment.title} (Copy)"
                    new_assessment.save()
                except Exception as e:
                    messages.warning(request, f'Could not duplicate "{assessment.title}": {str(e)}')
            messages.success(request, f'Successfully duplicated {count} assessment(s).')
        
        elif action == 'delete':
            assessment_titles = [a.title for a in assessments[:3]]  # Get first 3 titles for feedback
            assessments.delete()
            if count <= 3:
                title_list = ', '.join(assessment_titles)
                messages.success(request, f'Successfully deleted: {title_list}')
            else:
                messages.success(request, f'Successfully deleted {count} assessments.')
        
        else:
            messages.error(request, 'Invalid action.')
            
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('assessments:my_assessments')

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
        return redirect('accounts:teacher_dashboard')
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

# ==========================================
# SECURITY-ENHANCED ASSESSMENT TAKING VIEWS
# ==========================================

@login_required
def take_assessment_view(request, assessment_id):
    """Security-enhanced view for taking an assessment"""
    if request.user.user_type != 'student':
        messages.error(request, 'Only students can take assessments.')
        return redirect('accounts:student_dashboard')
    
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Check if assessment is available
    if assessment.status != 'published':
        messages.error(request, 'This assessment is not available.')
        return redirect('assessments:available_assessments')
    
    # Check if student has already completed the assessment
    existing_attempt = StudentAttempt.objects.filter(
        student=request.user,
        assessment=assessment,
        is_completed=True
    ).first()
    
    if existing_attempt:
        messages.info(request, 'You have already completed this assessment.')
        return redirect('assessments:assessment_result', attempt_id=existing_attempt.id)
    
    # Get or create current attempt
    current_attempt, created = StudentAttempt.objects.get_or_create(
        student=request.user,
        assessment=assessment,
        is_completed=False,
        defaults={
            'started_at': timezone.now(),
            'violation_flags': {},
            'tab_switches': 0,
            'copy_paste_attempts': 0
        }
    )
    
    # Check time limit
    if assessment.time_limit and current_attempt.started_at:
        time_elapsed = timezone.now() - current_attempt.started_at
        if time_elapsed.total_seconds() > (assessment.time_limit * 60):
            current_attempt.is_completed = True
            current_attempt.completed_at = timezone.now()
            current_attempt.is_auto_submitted = True
            # Store the reason in violation_flags
            violation_flags = current_attempt.violation_flags or {}
            violation_flags['auto_submit_reason'] = 'Time expired'
            current_attempt.violation_flags = violation_flags
            current_attempt.save()
            messages.warning(request, 'Assessment time has expired.')
            return redirect('assessments:assessment_result', attempt_id=current_attempt.id)
    
    questions = assessment.questions.all().order_by('id')
    
    context = {
        'assessment': assessment,
        'questions': questions,
        'attempt': current_attempt,
        'time_remaining': None
    }
    
    # Calculate remaining time
    if assessment.time_limit and current_attempt.started_at:
        time_elapsed = timezone.now() - current_attempt.started_at
        time_remaining = (assessment.time_limit * 60) - time_elapsed.total_seconds()
        context['time_remaining'] = max(0, int(time_remaining / 60))
    
    return render(request, 'assessments/take_assessment.html', context)

@login_required
@require_http_methods(["POST"])
def track_violation_view(request, assessment_id):
    """AJAX endpoint for tracking security violations"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        violation_type = data.get('violation_type')
        timestamp = data.get('timestamp')
        violations = data.get('violations', {})
        
        # Get current attempt
        attempt = StudentAttempt.objects.filter(
            student=request.user,
            assessment_id=assessment_id,
            is_completed=False
        ).first()
        
        if not attempt:
            return JsonResponse({'error': 'No active attempt found'}, status=404)
        
        # Update violation tracking
        if violation_type == 'tab_switches':
            attempt.tab_switches += 1
        elif violation_type in ['copy_attempts', 'paste_attempts']:
            attempt.copy_paste_attempts += 1
        
        # Update violation flags
        violation_flags = attempt.violation_flags or {}
        violation_flags[timestamp] = {
            'type': violation_type,
            'total_violations': sum(violations.values())
        }
        attempt.violation_flags = violation_flags
        
        attempt.save()
        
        return JsonResponse({
            'success': True,
            'total_violations': sum(violations.values())
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def save_progress_view(request, assessment_id):
    """AJAX endpoint for saving assessment progress"""
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        assessment = get_object_or_404(Assessment, id=assessment_id)
        
        # Get current attempt
        attempt = StudentAttempt.objects.filter(
            student=request.user,
            assessment=assessment,
            is_completed=False
        ).first()
        
        if not attempt:
            return JsonResponse({'error': 'No active attempt found'}, status=404)
        
        # Save current answers
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.split('_')[1]
                if question_id.isdigit():
                    question = get_object_or_404(Question, id=question_id)
                    
                    # Update or create student answer
                    answer, created = StudentAnswer.objects.update_or_create(
                        attempt=attempt,
                        question=question,
                        defaults={'answer_text': value}
                    )
        
        # Update violations if provided
        violations_data = request.POST.get('violations')
        if violations_data:
            violations = json.loads(violations_data)
            attempt.tab_switches = violations.get('tab_switches', 0)
            attempt.copy_paste_attempts = violations.get('copy_attempts', 0) + violations.get('paste_attempts', 0)
        
        attempt.last_activity = timezone.now()
        attempt.save()
        
        return JsonResponse({'success': True, 'message': 'Progress saved successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def submit_assessment_view(request, assessment_id):
    """Enhanced view for submitting an assessment with security tracking"""
    if request.user.user_type != 'student':
        messages.error(request, 'Only students can submit assessments.')
        return redirect('accounts:student_dashboard')
    
    if request.method != 'POST':
        return redirect('assessments:take_assessment', assessment_id=assessment_id)
    
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Get current attempt
    attempt = StudentAttempt.objects.filter(
        student=request.user,
        assessment=assessment,
        is_completed=False
    ).first()
    
    if not attempt:
        messages.error(request, 'No active assessment attempt found.')
        return redirect('assessments:available_assessments')
    
    # Process violation data
    violation_data = request.POST.get('violation_data')
    if violation_data:
        try:
            violation_info = json.loads(violation_data)
            violations = violation_info.get('violations', {})
            
            attempt.tab_switches = violations.get('tab_switches', 0)
            attempt.copy_paste_attempts = (
                violations.get('copy_attempts', 0) + 
                violations.get('paste_attempts', 0)
            )
            
            # Store additional violation info
            attempt.violation_flags = attempt.violation_flags or {}
            attempt.violation_flags['submission'] = {
                'auto_submit_reason': violation_info.get('auto_submit_reason'),
                'time_spent': violation_info.get('time_spent'),
                'total_violations': sum(violations.values())
            }
            
        except json.JSONDecodeError:
            pass
    
    # Process question sequence data
    question_sequence = request.POST.get('question_sequence')
    if question_sequence:
        try:
            sequence_data = json.loads(question_sequence)
            attempt.violation_flags = attempt.violation_flags or {}
            attempt.violation_flags['question_sequence'] = sequence_data
        except json.JSONDecodeError:
            pass
    
    # Save all answers and calculate score
    total_score = 0
    max_score = 0
    
    for question in assessment.questions.all():
        max_score += question.points
        student_answer = None
        points_earned = 0
        
        if question.question_type == 'enumeration':
            # Handle enumeration questions
            enumeration_answers = []
            for i in range(1, 6):  # Up to 5 items
                item_key = f'question_{question.id}_item_{i}'
                if item_key in request.POST and request.POST[item_key].strip():
                    enumeration_answers.append(request.POST[item_key].strip())
            
            if enumeration_answers:
                student_answer, created = StudentAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'enumeration_answers': enumeration_answers,
                        'text_answer': '; '.join(enumeration_answers),
                        'points_earned': 0  # Manual grading required
                    }
                )
                
        else:
            # Handle other question types
            answer_key = f'question_{question.id}'
            answer_text = request.POST.get(answer_key, '').strip()
            
            if answer_text:
                # Calculate points based on question type
                if question.question_type == 'multiple_choice':
                    try:
                        choice_id = int(answer_text)
                        correct_choice = question.choices.filter(is_correct=True).first()
                        if correct_choice and correct_choice.id == choice_id:
                            points_earned = question.points
                    except (ValueError, TypeError):
                        points_earned = 0
                        
                elif question.question_type == 'true_false':
                    correct_answer = question.correct_answers.first()
                    if correct_answer and correct_answer.answer_text.lower() == answer_text.lower():
                        points_earned = question.points
                    else:
                        points_earned = 0
                        
                # For identification and essay, set to 0 (manual grading required)
                elif question.question_type in ['identification', 'essay']:
                    points_earned = 0
                
                # Create or update student answer
                student_answer, created = StudentAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'text_answer': answer_text,
                        'points_earned': points_earned,
                        'is_correct': points_earned > 0
                    }
                )
        
        # Add to total score (only for auto-gradable questions)
        if student_answer and question.question_type in ['multiple_choice', 'true_false']:
            total_score += student_answer.points_earned
    
    # Complete the attempt
    attempt.is_completed = True
    attempt.completed_at = timezone.now()
    attempt.is_submitted = True
    attempt.score = total_score
    attempt.max_score = max_score
    attempt.percentage = (total_score / max_score * 100) if max_score > 0 else 0
    attempt.is_passed = attempt.percentage >= assessment.passing_score
    attempt.save()
    
    # Success message with security summary
    violation_summary = ""
    if attempt.tab_switches > 0 or attempt.copy_paste_attempts > 0:
        violation_summary = f" (Security violations detected: {attempt.tab_switches} tab switches, {attempt.copy_paste_attempts} copy/paste attempts)"
    
    messages.success(request, f'Assessment submitted successfully! Score: {attempt.percentage:.1f}%{violation_summary}')
    return redirect('assessments:assessment_result', attempt_id=attempt.id)

@login_required
def assessment_result_view(request, attempt_id):
    """View for displaying assessment results with security report"""
    attempt = get_object_or_404(StudentAttempt, id=attempt_id)
    
    # Check if user can view this result
    if request.user != attempt.student and request.user != attempt.assessment.creator:
        messages.error(request, 'You are not authorized to view this result.')
        return redirect('accounts:dashboard')
    
    student_answers = attempt.answers.all().select_related('question')
    
    # Prepare security report
    security_report = {
        'tab_switches': attempt.tab_switches,
        'copy_paste_attempts': attempt.copy_paste_attempts,
        'violation_flags': attempt.violation_flags or {},
        'total_violations': attempt.tab_switches + attempt.copy_paste_attempts,
        'risk_level': 'Low'
    }
    
    # Determine risk level
    total_violations = security_report['total_violations']
    if total_violations >= 5:
        security_report['risk_level'] = 'High'
    elif total_violations >= 2:
        security_report['risk_level'] = 'Medium'
    
    context = {
        'attempt': attempt,
        'student_answers': student_answers,
        'security_report': security_report,
        'is_teacher_view': request.user == attempt.assessment.creator
    }
    
    return render(request, 'assessments/assessment_result.html', context)

# Removed old assessment_results_view - replaced with assessment_result_view above

@login_required
def grade_assessment_view(request, attempt_id):
    """Comprehensive manual grading interface for teachers"""
    attempt = get_object_or_404(StudentAttempt, id=attempt_id)
    
    # Check if user is the assessment creator (teacher)
    if request.user != attempt.assessment.creator:
        messages.error(request, 'You are not authorized to grade this assessment.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_draft':
            # Save grading progress without finalizing
            return _save_grading_draft(request, attempt)
        elif action == 'grade_assessment':
            # Finalize grading
            return _finalize_grading(request, attempt)
    
    # Get all student answers with related questions
    student_answers = attempt.answers.all().select_related('question').order_by('question__order')
    
    # Calculate scoring breakdown
    auto_graded_score = 0
    auto_graded_total = 0
    manual_score = 0
    manual_total = 0
    
    for answer in student_answers:
        if answer.question.question_type in ['multiple_choice', 'true_false']:
            auto_graded_score += answer.points_earned or 0
            auto_graded_total += answer.question.points
        else:
            manual_score += answer.points_earned or 0
            manual_total += answer.question.points
    
    context = {
        'attempt': attempt,
        'student_answers': student_answers,
        'auto_graded_score': auto_graded_score,
        'auto_graded_total': auto_graded_total,
        'manual_score': manual_score,
        'manual_total': manual_total,
    }
    
    return render(request, 'assessments/grade_assessment.html', context)

def _save_grading_draft(request, attempt):
    """Save grading progress as draft"""
    try:
        updated_answers = 0
        
        for key, value in request.POST.items():
            if key.startswith('points_'):
                answer_id = key.replace('points_', '')
                try:
                    answer = StudentAnswer.objects.get(id=answer_id, attempt=attempt)
                    points = float(value) if value else 0
                    
                    # Validate points don't exceed maximum
                    if points > answer.question.points:
                        points = answer.question.points
                    
                    answer.points_earned = points
                    answer.is_correct = points > 0
                    answer.save()
                    updated_answers += 1
                except (StudentAnswer.DoesNotExist, ValueError):
                    continue
            
            elif key.startswith('feedback_'):
                answer_id = key.replace('feedback_', '')
                try:
                    answer = StudentAnswer.objects.get(id=answer_id, attempt=attempt)
                    answer.feedback = value.strip()
                    answer.save()
                except StudentAnswer.DoesNotExist:
                    continue
        
        # Save overall feedback
        overall_feedback = request.POST.get('overall_feedback', '').strip()
        if overall_feedback:
            attempt.overall_feedback = overall_feedback
            attempt.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Draft saved! Updated {updated_answers} answers.',
            'updated_count': updated_answers
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def _finalize_grading(request, attempt):
    """Finalize the grading process"""
    try:
        total_score = 0
        max_score = 0
        graded_answers = 0
        
        # Process all answer scores and feedback
        for key, value in request.POST.items():
            if key.startswith('points_'):
                answer_id = key.replace('points_', '')
                try:
                    answer = StudentAnswer.objects.get(id=answer_id, attempt=attempt)
                    points = float(value) if value else 0
                    
                    # Validate points don't exceed maximum
                    if points > answer.question.points:
                        points = answer.question.points
                    
                    answer.points_earned = points
                    answer.is_correct = points > 0
                    answer.is_graded = True
                    answer.graded_at = timezone.now()
                    answer.graded_by = request.user
                    answer.save()
                    
                    total_score += points
                    graded_answers += 1
                    
                except (StudentAnswer.DoesNotExist, ValueError):
                    continue
            
            elif key.startswith('feedback_'):
                answer_id = key.replace('feedback_', '')
                try:
                    answer = StudentAnswer.objects.get(id=answer_id, attempt=attempt)
                    answer.feedback = value.strip()
                    answer.save()
                except StudentAnswer.DoesNotExist:
                    continue
        
        # Calculate total possible score
        for answer in attempt.answers.all():
            max_score += answer.question.points
        
        # Update attempt with final scores
        attempt.score = total_score
        attempt.max_score = max_score
        attempt.percentage = (total_score / max_score * 100) if max_score > 0 else 0
        attempt.is_passed = attempt.percentage >= attempt.assessment.passing_score
        attempt.is_graded = True
        attempt.graded_at = timezone.now()
        attempt.graded_by = request.user
        
        # Save overall feedback
        overall_feedback = request.POST.get('overall_feedback', '').strip()
        if overall_feedback:
            attempt.overall_feedback = overall_feedback
        
        attempt.save()
        
        # Send notification to student (if notification system exists)
        messages.success(request, f'Assessment graded successfully! Student score: {attempt.percentage:.1f}% ({graded_answers} answers graded)')
        
        return redirect('assessments:assessment_detail', assessment_id=attempt.assessment.id)
        
    except Exception as e:
        messages.error(request, f'Error finalizing grades: {str(e)}')
        return redirect('assessments:grade_assessment', attempt_id=attempt.id)

@login_required
def export_grades_view(request, assessment_id):
    """Export assessment grades to CSV"""
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Check if user is the assessment creator
    if request.user != assessment.creator:
        messages.error(request, 'You are not authorized to export grades for this assessment.')
        return redirect('accounts:dashboard')
    
    import csv
    from django.http import HttpResponse
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{assessment.title}_grades.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Student ID',
        'Student Name',
        'Email',
        'Score',
        'Max Score',
        'Percentage',
        'Grade',
        'Status',
        'Submitted At',
        'Graded At',
        'Time Taken (minutes)',
        'Tab Switches',
        'Copy/Paste Attempts',
        'Overall Feedback'
    ])
    
    # Write student data
    attempts = StudentAttempt.objects.filter(
        assessment=assessment,
        is_submitted=True
    ).select_related('student', 'student__student_profile').order_by(
        'student__student_profile__student_id'
    )
    
    for attempt in attempts:
        time_taken = ''
        if attempt.started_at and attempt.completed_at:
            time_diff = attempt.completed_at - attempt.started_at
            time_taken = round(time_diff.total_seconds() / 60, 2)
        
        writer.writerow([
            attempt.student.student_profile.student_id if hasattr(attempt.student, 'student_profile') else '',
            attempt.student.get_full_name(),
            attempt.student.email,
            attempt.score,
            attempt.max_score,
            f"{attempt.percentage:.1f}%",
            'A' if attempt.percentage >= 90 else 'B' if attempt.percentage >= 80 else 'C' if attempt.percentage >= 70 else 'D' if attempt.percentage >= 60 else 'F',
            'PASSED' if attempt.is_passed else 'FAILED',
            attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.completed_at else '',
            attempt.graded_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.graded_at else '',
            time_taken,
            attempt.tab_switches,
            attempt.copy_paste_attempts,
            attempt.overall_feedback or ''
        ])
    
    return response

# Additional views for dashboard functionality
@login_required
def available_assessments_view(request):
    """View available assessments for students"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard_redirect')
    
    # This would be implemented with proper course enrollment logic
    assessments = Assessment.objects.filter(
        status='published',
        available_from__lte=timezone.now()
    ).order_by('-created_at')
    
    return render(request, 'assessments/available_assessments.html', {
        'assessments': assessments
    })

@login_required
def assessment_results_view(request, assessment_id):
    """View results for a specific assessment"""
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Check if user has permission to view results
    if not (request.user == assessment.creator or request.user.is_staff):
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard_redirect')
    
    attempts = StudentAttempt.objects.filter(
        assessment=assessment,
        is_completed=True
    ).select_related('student').order_by('-completed_at')
    
    # Calculate statistics
    total_attempts = StudentAttempt.objects.filter(assessment=assessment).count()
    completed_attempts_count = attempts.count()
    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    pass_rate = attempts.filter(percentage__gte=60).count() / max(attempts.count(), 1) * 100
    
    return render(request, 'assessments/assessment_results.html', {
        'assessment': assessment,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'completed_attempts_count': completed_attempts_count,
        'avg_score': avg_score,
        'pass_rate': pass_rate
    })

@login_required
def view_assessment_view(request, assessment_id):
    """View assessment details"""
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Check if user has permission to view
    if not (request.user == assessment.creator or request.user.is_staff):
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard_redirect')
    
    questions = assessment.questions.all().order_by('order')
    
    # Get attempt statistics
    all_attempts = assessment.attempts.all()
    completed_attempts = all_attempts.filter(is_completed=True)
    in_progress_attempts = all_attempts.filter(is_completed=False)
    graded_attempts = completed_attempts.filter(is_graded=True)
    
    # Calculate average score if there are graded attempts
    avg_score = graded_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    
    return render(request, 'assessments/view_assessment.html', {
        'assessment': assessment,
        'avg_score': avg_score,
        'questions': questions,
        'total_attempts': all_attempts.count(),
        'completed_attempts_count': completed_attempts.count(),
        'in_progress_attempts_count': in_progress_attempts.count(),
        'graded_attempts_count': graded_attempts.count(),
    })

@login_required
def grading_queue_view(request):
    """View all assessments requiring grading"""
    if request.user.user_type not in ['teacher', 'admin'] and not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard_redirect')
    
    # Get assessments needing grading
    attempts = StudentAttempt.objects.filter(
        assessment__creator=request.user,
        is_completed=True,
        percentage__isnull=True
    ).select_related('student', 'assessment').order_by('-completed_at')
    
    return render(request, 'assessments/grading_queue.html', {
        'attempts': attempts
    })

@login_required
def admin_assessments_view(request):
    """Admin view of all assessments"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('accounts:dashboard_redirect')
    
    assessments = Assessment.objects.all().select_related(
        'creator'
    ).annotate(
        total_attempts=Count('attempts'),
        completed_attempts=Count('attempts', filter=Q(attempts__is_completed=True))
    ).order_by('-created_at')
    
    return render(request, 'assessments/admin_assessments.html', {
        'assessments': assessments
    })
