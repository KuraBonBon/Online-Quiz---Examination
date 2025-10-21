from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from assessments.models import *
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample student attempts for testing grading functionality'

    def handle(self, *args, **options):
        self.stdout.write('📝 Creating sample student attempts...')
        
        # Get students and assessments
        students = User.objects.filter(user_type='student')
        assessments = Assessment.objects.filter(status='published')
        
        if not students.exists():
            self.stdout.write(self.style.ERROR('No students found. Run reset_and_populate first.'))
            return
            
        if not assessments.exists():
            self.stdout.write(self.style.ERROR('No assessments found. Run reset_and_populate first.'))
            return
        
        created_attempts = 0
        
        # Create attempts for each student on different assessments
        for student in students:
            for i, assessment in enumerate(assessments[:2]):  # First 2 assessments
                # Check if attempt already exists
                existing_attempt = StudentAttempt.objects.filter(
                    student=student,
                    assessment=assessment,
                    attempt_number=1
                ).first()
                
                if existing_attempt:
                    self.stdout.write(f'⚠️  Attempt already exists for {student.username} on "{assessment.title}"')
                    continue
                
                # Create a completed attempt
                attempt = StudentAttempt.objects.create(
                    student=student,
                    assessment=assessment,
                    started_at=timezone.now() - timedelta(hours=2),
                    completed_at=timezone.now() - timedelta(hours=1),
                    is_completed=True,
                    is_submitted=True,
                    time_taken=timedelta(hours=1),
                    ip_address='127.0.0.1',
                    attempt_number=1
                )
                
                # Create answers for each question
                questions = assessment.questions.all()
                correct_answers = 0
                total_questions = questions.count()
                
                for question in questions:
                    if question.question_type == 'multiple_choice':
                        # Get choices and randomly select one (bias towards correct)
                        choices = question.choices.all()
                        if choices.exists():
                            # 70% chance of correct answer
                            if random.random() < 0.7:
                                correct_choice = choices.filter(is_correct=True).first()
                                selected_choice = correct_choice if correct_choice else choices.first()
                                if correct_choice:
                                    correct_answers += 1
                            else:
                                selected_choice = random.choice(choices)
                                if selected_choice.is_correct:
                                    correct_answers += 1
                            
                            StudentAnswer.objects.create(
                                attempt=attempt,
                                question=question,
                                selected_choice=selected_choice,
                                is_correct=selected_choice.is_correct,
                                points_earned=question.points if selected_choice.is_correct else 0
                            )
                    
                    elif question.question_type == 'true_false':
                        choices = question.choices.all()
                        if choices.exists():
                            # 80% chance of correct answer for true/false
                            if random.random() < 0.8:
                                correct_choice = choices.filter(is_correct=True).first()
                                selected_choice = correct_choice if correct_choice else choices.first()
                                if correct_choice:
                                    correct_answers += 1
                            else:
                                selected_choice = random.choice(choices)
                                if selected_choice.is_correct:
                                    correct_answers += 1
                            
                            StudentAnswer.objects.create(
                                attempt=attempt,
                                question=question,
                                selected_choice=selected_choice,
                                is_correct=selected_choice.is_correct,
                                points_earned=question.points if selected_choice.is_correct else 0
                            )
                    
                    elif question.question_type in ['essay', 'identification']:
                        # Create text answers that need manual grading
                        sample_answers = {
                            'essay': [
                                'Lists are mutable and ordered collections that can store different data types. Tuples are immutable and ordered collections.',
                                'The main difference is that lists can be modified after creation while tuples cannot be changed.',
                                'Lists use square brackets [] and tuples use parentheses (). Lists are for data that changes, tuples for fixed data.'
                            ],
                            'identification': [
                                'Stack',
                                'LIFO data structure',
                                'Last In First Out structure'
                            ]
                        }
                        
                        answer_type = 'essay' if question.question_type == 'essay' else 'identification'
                        answer_text = random.choice(sample_answers[answer_type])
                        
                        StudentAnswer.objects.create(
                            attempt=attempt,
                            question=question,
                            text_answer=answer_text,
                            is_manually_graded=True,  # Needs grading
                            points_earned=0  # Not graded yet
                        )
                
                # Calculate percentage
                if total_questions > 0:
                    percentage = (correct_answers / total_questions) * 100
                    attempt.percentage = percentage
                    attempt.is_passed = percentage >= assessment.passing_score
                    attempt.save()
                
                created_attempts += 1
                self.stdout.write(f'✅ Created attempt for {student.username} on "{assessment.title}" ({percentage:.1f}%)')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Created {created_attempts} sample student attempts!\n'
                f'You can now test the grading functionality.\n'
                f'Some answers are marked as needing manual grading (essays/identification).'
            )
        )